# TODO

## Milestone 0: Repository Skeleton

- [x] Create directory structure
- [x] Write README.md, AGENTS.md
- [ ] Write all skeleton docs and configs (in progress)
- [ ] Create conda environment `agentprof`
- [ ] Initial commit and push to GitHub

## Milestone 1: Minimal Event Chain

- [ ] Implement `agentprof/observers/semantic_langchain.py` (LangChain callback)
- [ ] Implement `agentprof/observers/llm_client_timing.py` (OpenAI-compatible client timing)
- [ ] Implement `agentprof/observers/tool_wrapper.py` (tool start/end/error/duration)
- [ ] Implement `agentprof/storage/writer.py` (events.jsonl writer)
- [ ] Implement `targets/langchain_react_agent/agent.py`
- [ ] Run slow_tool / cpu_tool / flaky_tool tasks
- [ ] Verify `profiles/<run_id>/events.jsonl` is produced

## Milestone 2: Timeline + Report

- [ ] Implement `agentprof/timeline.py` (timeline.csv + summary.json)
- [ ] Implement `agentprof/report.py` (report.md)
- [ ] Run all three controlled tasks end-to-end
- [ ] Review first `report.md`

## Milestone 3: AgentProf Controller

- [ ] Implement `agentprof/questions.py` (diagnostic question generation)
- [ ] Implement `agentprof/policy.py` (rule-based observer selection)
- [ ] Implement `agentprof/controller.py` (LangChain tool-calling controller)
- [ ] Add rule validator (ALLOWED_ACTIONS_MVP enforcement)

## Milestone 4: Multi-Program Workload

- [ ] Extend `configs/workload_controlled.yaml` for multiple programs
- [ ] Implement system-level aggregation in `agentprof/timeline.py`

## Milestone 5: Real Benchmark Subset

- [ ] Select BFCL V3 multi-turn subset
- [ ] Implement trace adapter for BFCL tasks
- [ ] Compare report vs controlled workload

## Deferred / Future

- [ ] `agentprof/observers/vllm_metrics.py` (vLLM /metrics endpoint)
- [ ] `agentprof/observers/tool_process.py` (psutil process tree)
- [ ] `agentprof/observers/resource_counters.py` (nvidia-smi/NVML)
- [ ] `agentprof/adapters/openinference_adapter.py`
- [ ] Docker setup
