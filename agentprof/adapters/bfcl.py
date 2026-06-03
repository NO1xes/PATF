"""BFCL workload adapter.

Converts BFCL question files into AgentProf workload YAML.
This module is offline-only: it does not run BFCL, call a model, or start vLLM.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ID_KEYS = ("id", "run_id", "test_case_id", "question_id")
TEXT_KEYS = ("prompt", "question", "query", "instruction")
MESSAGE_KEYS = ("messages", "conversation", "turns")
TOOL_KEYS = ("tools", "functions", "function")


def load_bfcl_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load BFCL cases from JSON or JSONL.

    Supports common wrappers such as {"questions": [...]}, {"data": [...]}, and
    {"items": [...]}. Raises ValueError for unsupported payload shapes.

    BFCL v3 question files such as ``BFCL_v3_simple.json`` use a .json extension
    but are newline-delimited JSON objects (one JSON object per line).  This
    function first tries parsing the whole file as a single JSON document; on
    failure it falls back to line-by-line JSONL parsing so that those upstream
    benchmark files work without renaming or reformatting.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8")

    # Try standard JSON first (single array or object).
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Fall back to line-by-line JSONL parsing.
        cases = []
        for line in raw.splitlines():
            line = line.strip()
            if line:
                cases.append(json.loads(line))
        return cases

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("questions", "data", "items", "cases"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    raise ValueError(f"Unsupported BFCL case file shape: {path}")


def filter_cases(
    cases: list[dict[str, Any]],
    run_ids: list[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Filter cases by BFCL run ids, then apply an optional limit."""
    selected = cases
    if run_ids:
        wanted = set(run_ids)
        selected = [case for case in cases if extract_case_id(case) in wanted]
    if limit is not None:
        selected = selected[:limit]
    return selected


def extract_case_id(case: dict[str, Any]) -> str:
    for key in ID_KEYS:
        value = case.get(key)
        if value is not None:
            return str(value)
    raise ValueError(f"BFCL case is missing an id field: expected one of {ID_KEYS}")


def case_to_program(case: dict[str, Any]) -> dict[str, Any]:
    """Convert one BFCL case into one AgentProf workload program."""
    case_id = extract_case_id(case)
    prompt = extract_prompt(case)
    tool_names = extract_tool_names(case)
    notes = "BFCL V3 demo case"
    if tool_names:
        notes += f"; tools: {', '.join(tool_names[:5])}"
        if len(tool_names) > 5:
            notes += f"; +{len(tool_names) - 5} more"

    return {
        "task_id": case_id,
        "prompt": prompt,
        "expected_bottleneck": "unknown_real_benchmark",
        "source": "bfcl",
        "bfcl_id": case_id,
        "notes": notes,
    }


def extract_prompt(case: dict[str, Any]) -> str:
    """Extract a prompt-like string from common BFCL case shapes."""
    for key in TEXT_KEYS:
        if key in case:
            return render_value(case[key])
    for key in MESSAGE_KEYS:
        if key in case:
            return render_value(case[key])
    raise ValueError(
        "BFCL case is missing prompt text: expected one of "
        f"{TEXT_KEYS + MESSAGE_KEYS}"
    )


def extract_tool_names(case: dict[str, Any]) -> list[str]:
    for key in TOOL_KEYS:
        if key not in case:
            continue
        value = case[key]
        if isinstance(value, dict):
            value = [value]
        if isinstance(value, list):
            names = []
            for item in value:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("function", {}).get("name")
                    if name:
                        names.append(str(name))
                elif isinstance(item, str):
                    names.append(item)
            return names
    return []


def render_value(value: Any) -> str:
    """Render common BFCL message/question values into plain text."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        rendered = [render_value(item) for item in value]
        return "\n".join(part for part in rendered if part)
    if isinstance(value, dict):
        if "role" in value and "content" in value:
            return f"{value['role']}: {render_value(value['content'])}"
        if "content" in value:
            return render_value(value["content"])
        if "text" in value:
            return render_value(value["text"])
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return str(value)


def cases_to_workload(
    cases: list[dict[str, Any]],
    workload_name: str = "bfcl_v3_demo_subset",
    stage: str = "Milestone-5",
    source_path: str | None = None,
) -> dict[str, Any]:
    return {
        "workload_name": workload_name,
        "stage": stage,
        "description": (
            "BFCL V3 demo subset converted to AgentProf workload format. "
            "Generated offline; running this workload still requires a configured target agent."
        ),
        "source": {
            "benchmark": "Berkeley Function Calling Leaderboard",
            "version": "v3",
            "path": source_path,
        },
        "programs": [case_to_program(case) for case in cases],
    }


def write_workload_yaml(workload: dict[str, Any], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(workload, sort_keys=False), encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert BFCL cases to AgentProf workload YAML.")
    parser.add_argument("input", help="BFCL JSON or JSONL case file")
    parser.add_argument("--output", required=True, help="Output workload YAML path")
    parser.add_argument("--run-id", action="append", dest="run_ids", help="BFCL run id to include")
    parser.add_argument("--limit", type=int, help="Maximum number of cases to include")
    parser.add_argument("--workload-name", default="bfcl_v3_demo_subset")
    args = parser.parse_args(argv)

    cases = load_bfcl_cases(args.input)
    selected = filter_cases(cases, run_ids=args.run_ids, limit=args.limit)
    workload = cases_to_workload(
        selected,
        workload_name=args.workload_name,
        source_path=str(Path(args.input)),
    )
    write_workload_yaml(workload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

