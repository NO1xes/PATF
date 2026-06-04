"""AgentProf ReAct controller — Phase 1 (Hardware/System tier).

Replaces the old linear "baseline → analysis → planner → executor"
pipeline with an LLM-driven ReAct tool-calling loop.

The controller acts as an EXTERNAL observer: the target agent system
is already running, and AgentProf calls profiling tools to diagnose it
from coarse to fine.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from openai import OpenAI

from agentprof.planner.backends.llm.prompts_v2 import (
    PROFILING_AGENT_SYSTEM_PROMPT,
    build_profiling_context,
    describe_available_tools,
    get_active_tools,
    get_tool_dispatch,
)
from agentprof.storage import ensure_run_dir


def _load_yaml(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_machine_info() -> dict[str, Any]:
    """Read machine capabilities from the environment / config."""
    import os

    cpu_count = os.cpu_count() or 1
    try:
        import psutil
        mem = psutil.virtual_memory()
        memory_gb = round(mem.total / (1024**3), 1)
    except Exception:
        memory_gb = 0

    gpu_count = 0
    gpu_model = "none"
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            gpus = [l.strip() for l in result.stdout.strip().split("\n") if l]
            gpu_count = len(gpus)
            gpu_model = gpus[0] if gpus else "none"
    except Exception:
        pass

    return {
        "cpu_cores": cpu_count,
        "memory_gb": memory_gb,
        "gpu_count": gpu_count,
        "gpu_model": gpu_model,
    }


def run_profiling_session(
    target_config_path: str,
    profiling_config_path: str | None = None,
    profiles_base: str = "./profiles",
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    max_tool_calls: int = 8,
) -> dict[str, Any]:
    """Run one AgentProf ReAct profiling session.

    Args:
        target_config_path: Path to target_system.yaml describing the system
            being profiled (LLM endpoint, agent runtime, sandbox info).
        profiling_config_path: Optional profiling session config.
        profiles_base: Output directory root.
        model: LLM model for the profiling agent (env: AGENTPROF_MODEL).
        base_url: LLM API base URL (env: AGENTPROF_LLM_URL or VLLM_BASE_URL).
        api_key: API key (env: AGENTPROF_API_KEY or VLLM_API_KEY).
        max_tool_calls: Maximum tool calls before forced report.

    Returns a dict with keys: run_id, report, tool_call_log, error (if any).
    """
    # -- resolve LLM config -------------------------------------------------
    import os

    if base_url is None:
        base_url = os.getenv("AGENTPROF_LLM_URL") or os.getenv("VLLM_BASE_URL") or "http://127.0.0.1:8000/v1"
    if api_key is None:
        api_key = os.getenv("AGENTPROF_API_KEY") or os.getenv("VLLM_API_KEY") or "not-needed"
    if model is None:
        model = os.getenv("AGENTPROF_MODEL") or os.getenv("VLLM_MODEL") or "Qwen/Qwen3-30B-A3B-Instruct-2507"

    # -- load configs --------------------------------------------------------
    target_cfg = _load_yaml(target_config_path)
    profiling_cfg = _load_yaml(profiling_config_path) if profiling_config_path else {}

    workload_description = profiling_cfg.get(
        "workload_description",
        "A multi-agent system running coding / web tasks on a shared LLM backend.",
    )
    target_system_info = {
        "llm_endpoint": target_cfg.get("llm_endpoint", base_url),
        "agent_runtime": target_cfg.get("agent_runtime", "langchain_react"),
        "agent_count": profiling_cfg.get("agent_count", "unknown"),
        "sandbox": profiling_cfg.get("sandbox", "none"),
    }
    machine_info = _build_machine_info()

    # -- setup output directory ----------------------------------------------
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    output_dir = ensure_run_dir(profiles_base, run_id)

    # -- build context -------------------------------------------------------
    tool_descriptions = describe_available_tools()
    context = build_profiling_context(
        workload_description=workload_description,
        target_system_info=target_system_info,
        machine_info=machine_info,
        available_tool_descriptions=tool_descriptions,
    )

    # -- build messages ------------------------------------------------------
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": PROFILING_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]

    tools = get_active_tools()
    dispatch = get_tool_dispatch()

    # -- ReAct loop ----------------------------------------------------------
    client = OpenAI(base_url=base_url, api_key=api_key)
    tool_call_log: list[dict[str, Any]] = []
    final_report = ""
    error = None

    for iteration in range(max_tool_calls):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                temperature=0.0,
                timeout=60,
            )
        except Exception as exc:
            error = f"LLM call failed at iteration {iteration}: {exc}"
            break

        choice = response.choices[0]
        message = choice.message

        # Check for tool calls
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute the tool
                if tool_name in dispatch:
                    try:
                        tool_result = dispatch[tool_name](**tool_args)
                        result_str = json.dumps(tool_result, ensure_ascii=False, default=str)
                    except Exception as exc:
                        result_str = json.dumps({"error": str(exc)})
                else:
                    result_str = json.dumps({"error": f"Unknown tool: {tool_name}"})

                tool_call_log.append({
                    "iteration": iteration,
                    "tool": tool_name,
                    "args": tool_args,
                    "result_summary": (
                        result_str[:200] + "..." if len(result_str) > 200 else result_str
                    ),
                })

                # Append assistant message + tool result to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    ],
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })
        else:
            # No tool calls → the model is writing the final report
            final_report = message.content or ""
            break
    else:
        # Budget exhausted — force a final report
        messages.append({
            "role": "user",
            "content": (
                "You have reached the maximum number of tool calls.  "
                "Write your final profiling report NOW based on the "
                "evidence you have gathered so far.  If the root cause "
                "is still unclear, explain what Layer 2–4 tools would "
                "help and why."
            ),
        })
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.0, timeout=60,
            )
            final_report = response.choices[0].message.content or ""
        except Exception as exc:
            error = f"Final report generation failed: {exc}"

    # -- save outputs --------------------------------------------------------
    timestamp = datetime.now(timezone.utc).isoformat()
    session_output: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp,
        "model": model,
        "base_url": base_url,
        "workload_description": workload_description,
        "target_system_info": target_system_info,
        "machine_info": machine_info,
        "tool_call_log": tool_call_log,
        "tool_calls_count": len(tool_call_log),
        "final_report": final_report,
        "error": error,
    }
    output_path = output_dir / "profiling_session.json"
    output_path.write_text(
        json.dumps(session_output, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    if final_report:
        (output_dir / "report.md").write_text(final_report, encoding="utf-8")

    return session_output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="AgentProf ReAct profiling session (Phase 1 — Hardware tier)",
    )
    parser.add_argument(
        "--target-config", required=True,
        help="Path to target_system.yaml describing the system being profiled.",
    )
    parser.add_argument(
        "--profiling-config",
        help="Optional profiling session config with workload description.",
    )
    parser.add_argument(
        "--profiles-base", default="./profiles",
        help="Output directory root (default: ./profiles).",
    )
    parser.add_argument(
        "--model", default=None,
        help="LLM model for the profiling agent (env: AGENTPROF_MODEL).",
    )
    parser.add_argument(
        "--base-url", default=None,
        help="LLM API base URL (env: AGENTPROF_LLM_URL or VLLM_BASE_URL).",
    )
    parser.add_argument(
        "--max-tool-calls", type=int, default=8,
        help="Maximum tool calls per session (default: 8).",
    )
    args = parser.parse_args(argv)

    result = run_profiling_session(
        target_config_path=args.target_config,
        profiling_config_path=args.profiling_config,
        profiles_base=args.profiles_base,
        model=args.model,
        base_url=args.base_url,
        max_tool_calls=args.max_tool_calls,
    )

    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return 1
    print(f"Session complete: {result['run_id']}")
    print(f"Tool calls: {result['tool_calls_count']}")
    print(f"Report saved to profiles/{result['run_id']}/report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
