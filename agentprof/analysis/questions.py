"""Diagnostic question generator.

Produces structured diagnostic questions from:
  - breakdown (dominant component, time split)
  - resource_health (CPU/memory saturation symptoms)
  - execution_model (unattributed spans)

Each question has: id, text, priority, source, candidate_observers.
Priority 1 = highest. The LLM planner selects which questions to address.
"""

from __future__ import annotations

from agentprof.model.execution_model import ExecutionModel

DOMINANCE_THRESHOLD = 0.5
UNKNOWN_TIME_THRESHOLD = 0.2
HIGH_ERROR_THRESHOLD = 2


def generate_questions(
    breakdown: dict,
    resource_health: dict,
    execution_model: ExecutionModel,
) -> list[dict]:
    """Return prioritized diagnostic questions.

    Each question:
    {
      "question_id": "q_001",
      "priority": 1,
      "text": "Tool time accounts for 58% of total time. Which tool dominates?",
      "source": "breakdown",
      "candidate_observers": ["tool_events", "tool_process"]
    }
    """
    questions: list[dict] = []
    counter = [0]

    def _q(text: str, priority: int, source: str, observers: list[str]) -> dict:
        counter[0] += 1
        return {
            "question_id": f"q_{counter[0]:03d}",
            "priority": priority,
            "text": text,
            "source": source,
            "candidate_observers": observers,
        }

    dominant = breakdown.get("dominant_component", "none")
    tool_pct = breakdown.get("tool_pct", 0.0)
    llm_pct = breakdown.get("llm_pct", 0.0)
    unknown_pct = breakdown.get("unknown_pct", 0.0)
    errors = breakdown.get("errors", 0)
    tool_calls = breakdown.get("tool_calls", 0)

    # --- Breakdown-driven questions ---
    if dominant == "tool" and tool_pct >= DOMINANCE_THRESHOLD:
        questions.append(_q(
            f"Tool time accounts for {tool_pct:.0%} of total time. Which tool dominates and why?",
            priority=1,
            source="breakdown",
            observers=["tool_events", "tool_process"],
        ))

    if dominant == "llm" and llm_pct >= DOMINANCE_THRESHOLD:
        questions.append(_q(
            f"LLM time accounts for {llm_pct:.0%} of total time. Is this inference latency or queue wait?",
            priority=1,
            source="breakdown",
            observers=["llm_client_timing", "semantic_langchain"],
        ))

    if unknown_pct >= UNKNOWN_TIME_THRESHOLD:
        questions.append(_q(
            f"{unknown_pct:.0%} of time is unattributed. Are there gaps between spans?",
            priority=2,
            source="breakdown",
            observers=["semantic_langchain", "llm_client_timing"],
        ))

    if errors >= HIGH_ERROR_THRESHOLD:
        questions.append(_q(
            f"{errors} errors observed across {tool_calls} tool calls. Is retry overhead significant?",
            priority=2,
            source="breakdown",
            observers=["tool_events"],
        ))
    elif errors == 1:
        questions.append(_q(
            "1 error observed. Was it retried successfully, and how much did the retry cost?",
            priority=3,
            source="breakdown",
            observers=["tool_events"],
        ))

    # --- Resource health-driven questions ---
    if resource_health.get("cpu_saturated"):
        cpu_max = resource_health.get("cpu_util_max_pct", 0.0)
        questions.append(_q(
            f"CPU peaked at {cpu_max:.1f}% during the run. Is this from tool computation or framework overhead?",
            priority=1,
            source="resource_health",
            observers=["resource_snapshot", "tool_process"],
        ))

    if resource_health.get("memory_saturated"):
        mem_max = resource_health.get("memory_util_max_pct", 0.0)
        questions.append(_q(
            f"Memory peaked at {mem_max:.1f}%. Is there a memory leak or large context accumulation?",
            priority=2,
            source="resource_health",
            observers=["resource_snapshot"],
        ))

    for symptom in resource_health.get("symptoms", []):
        if "Disk" in symptom or "disk" in symptom:
            questions.append(_q(
                "Elevated disk I/O detected. Are tools writing large files?",
                priority=3,
                source="resource_health",
                observers=["resource_snapshot"],
            ))
            break

    # --- ExecutionModel-driven questions ---
    unlinked_nodes = [
        nid for nid, attrs in execution_model.nodes.items()
        if not any(e["src"] == nid or e["dst"] == nid for e in execution_model.edges)
        and len(execution_model.nodes) > 1
    ]
    if unlinked_nodes:
        questions.append(_q(
            f"{len(unlinked_nodes)} node(s) in the execution model have no correlation edges. "
            "Can they be linked to spans?",
            priority=3,
            source="execution_model",
            observers=["semantic_langchain", "llm_client_timing"],
        ))

    questions.sort(key=lambda q: q["priority"])
    return questions
