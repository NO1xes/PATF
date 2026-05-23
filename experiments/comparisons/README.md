# Comparison Experiments Index

Each subdirectory contains one comparison experiment: configuration, results, and conclusions.

## Naming convention

`expXXX-<short-description>/`

## Planned experiments

| ID | Description | Status | Owner |
| --- | --- | --- | --- |
| exp001 | LLM planner vs rule-based planner (ablation) | planned | TBD |
| exp002 | LangChain backend vs DeepAgent backend | planned | TBD |
| exp003 | AgentProf vs observability/profiling baselines (Langfuse, Phoenix/OpenInference, AgentOps, AgentSight, and relevant AgentProf-named projects) | planned | collab survey + NO1xes demo |

## Comparison style

These comparisons are motivation-oriented. They do not need to isolate one variable
perfectly. Record what each baseline can observe, what it cannot attribute, what
kind of report or UI it produces, and which gaps motivate AgentProf's methodology.

## How to add a new comparison experiment

1. Create `experiments/comparisons/expXXX-<name>/`
2. Add `README.md` with: hypothesis, configs used, how to reproduce, conclusion
3. Add `config_A.yaml` and `config_B.yaml` (or more)
4. Run: `python -m agentprof.runner --config config_A.yaml` and `config_B.yaml`
5. Copy `profiles/<run_id>/breakdown.json` and `report.md` into `results/`
6. Write conclusion in `README.md`
7. Update this index and `EXPERIMENTS.md`
