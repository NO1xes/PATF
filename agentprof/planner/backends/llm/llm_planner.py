"""LLM Planner: generates an ObservationPlan via LLM call.

Builds a structured prompt from ProfilingState, calls the configured LLM,
parses the JSON response into an ObservationPlan.
"""

from __future__ import annotations

import json
import os
import uuid

from agentprof.planner.base import BasePlanner
from agentprof.planner.backends.llm.context_builder import build_planner_context
from agentprof.planner.backends.llm.prompts import SYSTEM_PROMPT, PLAN_REQUEST_TEMPLATE
from agentprof.schema.observations import ObservationPlan
from agentprof.state import ProfilingState


class LLMPlanner(BasePlanner):
    """LLM-based planner — calls the configured LLM to produce an ObservationPlan."""

    def plan_observation(self, state: ProfilingState) -> ObservationPlan:
        from openai import OpenAI

        base_url = os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
        api_key = os.environ.get("VLLM_API_KEY", "dummy")
        model = os.environ.get("VLLM_MODEL", "Qwen/Qwen3-30B-A3B")

        client = OpenAI(base_url=base_url, api_key=api_key)
        ctx = build_planner_context(state)
        user_content = PLAN_REQUEST_TEMPLATE.format(**ctx)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content or ""
        return _parse_plan(raw, state)


def _parse_plan(raw: str, state: ProfilingState) -> ObservationPlan:
    """Extract JSON from LLM output and build ObservationPlan."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: find the first {...} block
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

    # Validate observers against registry; drop unknown ones
    available = set(state.observer_registry.all_names())
    observers = [o for o in data.get("observers", []) if o in available]
    if not observers:
        observers = ["resource_snapshot"] if "resource_snapshot" in available else []

    return ObservationPlan(
        plan_id=data.get("plan_id") or f"plan_llm_{uuid.uuid4().hex[:8]}",
        question_id=data.get("question_id", "q_unknown"),
        observers=observers,
        scope=data.get("scope", {}),
        mode=data.get("mode", "query_existing"),
        rationale=data.get("rationale", raw[:200]),
        expected_evidence=data.get("expected_evidence", []),
    )
