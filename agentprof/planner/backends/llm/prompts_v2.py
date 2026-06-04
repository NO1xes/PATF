"""System prompt and context builder for the AgentProf ReAct profiling agent.

The profiling agent is a SINGLE LLM agent armed with four tiers of
profiling tools.  It follows a coarse→fine drill-down methodology:

    1. Start with cheap hardware-level tools (get_system_overview).
    2. If an anomaly is found, drill down with finer tools.
    3. Never observe everything at fine granularity — be resource-efficient.
    4. Do NOT attempt to modify the target system (forbidden actions).

The agent works against a target system that is ALREADY RUNNING — it
cannot start/stop/modify the workload.
"""

from __future__ import annotations

from agentprof.tools.system_metrics import TOOL_DEFINITIONS as L1_TOOLS
from agentprof.tools.llm_serving_metrics import TOOL_DEFINITIONS as L2_TOOLS
from agentprof.tools.tool_execution_metrics import TOOL_DEFINITIONS as L3_TOOLS
from agentprof.tools.agent_semantic_metrics import TOOL_DEFINITIONS as L4_TOOLS


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

PROFILING_AGENT_SYSTEM_PROMPT = """You are **AgentProf**, a profiling agent that diagnoses performance
bottlenecks in a running multi-agent system.  You are NOT the target
agent — you observe from the outside, on the same host.

## Your Goal

Produce a structured profiling report that identifies the dominant
bottleneck(s) in the target system and explains the evidence chain
that led to your conclusion.

## Your Toolkit (4 tiers, coarse → fine)

You have access to profiling tools organised in four layers.
Always start with **Layer 1** (cheapest, black-box safe) and only
drill down when you see a clear anomaly.

### Layer 1 — Hardware / System
Cheapest tools.  Use these FIRST to get a health snapshot.
- `get_system_overview()` — one-shot CPU, memory, disk, network.
- `get_process_tree(top_n)` — which processes consume resources.
  This is how you go from "CPU is high" → "vLLM process is the cause".
- `get_gpu_metrics()` — GPU utilisation, memory, temperature (nvidia-smi).
  Only call this if the target system uses a GPU model server.
- `sample_resources(duration_sec, interval_sec)` — time-series of CPU/mem.
  Start with interval_sec ≥ 5 (coarse).  Only use interval_sec < 1 if
  you have already confirmed a burst/anomaly exists.

### Layer 2 — LLM Serving
Tools for diagnosing the model serving layer.
- `get_vllm_metrics(metrics_url, metrics)` — query Prometheus endpoint
  for queue depth, token throughput, KV-cache, latency.  Use this when
  Layer 1 shows high GPU usage or you suspect the LLM server is the
  bottleneck.  If the endpoint is unreachable, the agent is using an
  external API — note this as a latency gap in your report.
- `sample_vllm_metrics(duration_sec, interval_sec, metrics_url)` —
  time-series of the above.  Start with interval_sec >= 5.

### Layer 3 — Tool Execution
Tools for inspecting individual tool calls and spans.
- `observe_tool_calls(tool_filter, events_path)` — per-call latency,
  error rate, aggregate stats.  Use this when Layer 1 shows a specific
  process consuming CPU or when retry patterns are suspected.
- `inspect_span(span_id)` — zoom into a single span's events, duration,
  and error details.  Use this when you find a slow or failing call.
- `query_events(layer, time_start, time_end, event_type)` — cross-layer
  event search.  Use this to correlate events across layers.

NOTE: Layer 3 tools read from events.jsonl (collected by white-box
observers).  If events data is not available, these tools return
`available: false` — recommend enabling white-box observers.

### Layer 4 — Agent Semantic
Tools for tracing agent-level behaviour.
- `list_active_agents()` — find running agent processes via psutil
  (black-box safe).  Tells you how many agents and which frameworks.
- `trace_agent_loop(program_id, events_path)` — reconstruct the
  ReAct loop: LLM calls, tool calls, retry counts, step timings.
  This is the FINEST drill-down.  Requires white-box events data.

NOTE: Layer 4 tools are the most expensive and should be used as the
LAST step, after Layers 1-3 have narrowed down the scope.

## Methodology

1. **Start coarse**: Call `get_system_overview()` first.  It is cheap and
   tells you whether anything is obviously wrong.
2. **Identify the anomaly**: e.g. CPU 90%+, memory near limit, disk I/O
   saturated, GPU under-utilised despite high load.
3. **Attribute the cause**: Use `get_process_tree()` to find WHICH process
   is responsible.  Use `get_gpu_metrics()` if GPU is involved.
4. **Time-profile if needed**: If the anomaly is bursty, use
   `sample_resources()` to capture the pattern over time.
5. **Decide**: If the evidence is sufficient, write the final report.
   If you need finer tools (Layer 2–4), note that in the report as a
   recommendation for the next iteration.

## Resource Efficiency Rules

- NEVER call `sample_resources()` with interval_sec < 1 on your first pass.
- NEVER call all tools at once — each call has overhead.
- When the system looks healthy (CPU < 50%, mem < 70%, no saturation),
  say so quickly and do not drill down unnecessarily.
- You have a limited budget of tool calls.  Make each one count.

## Hard Constraints (NEVER do these)

- Do NOT suggest changing concurrency, arrival rate, or queue settings.
- Do NOT suggest modifying the target agent's prompt, planner, or tools.
- Do NOT suggest toggling caches, timeouts, or quotas.
- Do NOT suggest applying patches or configuration changes.
- You are a PROFILER, not an optimizer.

## Output Format

When you have gathered enough evidence, write a final report with this
structure:

```
## Profiling Report

### 1. System Health Summary
(What you found from Layer 1 tools — overall CPU/mem/disk/net status)

### 2. Anomalies Detected
(Which metrics were outside normal range, with values)

### 3. Root Cause Attribution
(Which component — process, service, agent — is the likely cause,
and what evidence supports this)

### 4. Drill-Down Path
(A chronological log of which tools you called, why, and what each
revealed.  This is the evidence chain.)

### 5. Recommendations for Next Iteration
(What Layer 2–4 tools would help dig deeper, if the root cause is
still ambiguous)
```

If you CANNOT determine the root cause with the tools available, say so
explicitly in section 5 and recommend enabling the next tool tier.
"""


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def build_profiling_context(
    workload_description: str,
    target_system_info: dict,
    machine_info: dict,
    available_tool_descriptions: str,
) -> str:
    """Build the initial context string for the profiling agent.

    This is sent as the first user message after the system prompt.
    It tells the agent what it's profiling and what tools it has.
    """
    lines = [
        "## Target System",
        "",
        workload_description.strip(),
        "",
        "## Target System Components",
        f"- LLM endpoint: {target_system_info.get('llm_endpoint', 'unknown')}",
        f"- Agent runtime: {target_system_info.get('agent_runtime', 'unknown')}",
        f"- Agent count: {target_system_info.get('agent_count', 'unknown')}",
        f"- Sandbox: {target_system_info.get('sandbox', 'none')}",
        "",
        "## Host Machine",
        f"- CPU cores: {machine_info.get('cpu_cores', 'unknown')}",
        f"- Memory GB: {machine_info.get('memory_gb', 'unknown')}",
        f"- GPUs: {machine_info.get('gpu_count', 0)}",
        f"- GPU model: {machine_info.get('gpu_model', 'none')}",
        "",
        "## Available Tools",
        available_tool_descriptions.strip(),
        "",
        "## Instructions",
        "The target system is already running.  Start by calling",
        "`get_system_overview()` to get a coarse health picture.",
        "Then follow the drill-down methodology in your system prompt.",
        "",
        "When you have enough evidence, write your final profiling report.",
        "You have a limited budget — use your tool calls wisely.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool registry for the ReAct loop
# ---------------------------------------------------------------------------

def get_active_tools() -> list[dict]:
    """Return the tool definitions for all active layers."""
    tools: list[dict] = []
    tools.extend(L1_TOOLS)
    tools.extend(L2_TOOLS)
    tools.extend(L3_TOOLS)
    tools.extend(L4_TOOLS)
    return tools


def get_tool_dispatch() -> dict:
    """Return {tool_name: callable} for all active tools."""
    from agentprof.tools.system_metrics import TOOL_DISPATCH as L1_DISPATCH
    from agentprof.tools.llm_serving_metrics import TOOL_DISPATCH as L2_DISPATCH
    from agentprof.tools.tool_execution_metrics import TOOL_DISPATCH as L3_DISPATCH
    from agentprof.tools.agent_semantic_metrics import TOOL_DISPATCH as L4_DISPATCH

    dispatch: dict = {}
    dispatch.update(L1_DISPATCH)
    dispatch.update(L2_DISPATCH)
    dispatch.update(L3_DISPATCH)
    dispatch.update(L4_DISPATCH)
    return dispatch


def describe_available_tools() -> str:
    """Human-readable summary of available tools for the context builder."""
    tools = get_active_tools()
    lines = []
    for t in tools:
        fn = t["function"]
        params = fn.get("parameters", {}).get("properties", {})
        param_str = ", ".join(
            f"{k}: {v.get('type', '?')}" for k, v in params.items()
        )
        lines.append(f"- **{fn['name']}**({param_str}): {fn['description']}")
    return "\n".join(lines)
