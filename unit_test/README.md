# Unit Test 说明

## 环境准备

需要先激活 conda 环境：

```bash
conda activate agentprof
```

## 运行全部测试

```bash
# 设置 PYTHONPATH
export PYTHONPATH=/home/zyc/workspace/PATF/unit_test:$PYTHONPATH

# 运行测试
python3 -m pytest tests/ -v
```

## 运行单个测试

```bash
export PYTHONPATH=/home/zyc/workspace/PATF/unit_test:$PYTHONPATH

# 运行特定测试文件
python3 -m pytest tests/test_agent_integration.py -v

# 运行特定测试函数
python3 -m pytest tests/test_agent_integration.py::TestAgentWithExecTool::test_agent_exec_pwd -v

# 详细输出（显示 print）
python3 -m pytest tests/test_agent_integration.py::TestAgentWithExecTool::test_agent_exec_pwd -v -s
```

## 测试文件说明

- `test_agent_integration.py` - Agent 集成测试，验证 tools 在 LangChain agent 下正常工作
- `test_generic_tools.py` - 工具单元测试，验证各 tool 的基本功能

## 测试日志

测试运行后会自动生成日志文件到 `test_logs/` 目录，日志名称与测试函数名对应：

```
test_logs/test_agent_exec_pwd_call_20260604_130036.log
```

## 常用 pytest 选项

- `-v` verbose，显示每个测试的详细信息
- `-s` 显示 print 输出
- `--tb=short` 简化 traceback
- `-x` 遇错即停
- `-k EXPR` 只运行匹配 EXPR 的测试

## 示例

```bash
# 激活环境
conda activate agentprof

# 设置路径
export PYTHONPATH=/home/zyc/workspace/PATF/unit_test:$PYTHONPATH

# 运行所有测试
python3 -m pytest tests/ -v

# 只运行 agent 集成测试
python3 -m pytest tests/test_agent_integration.py -v

# 只运行包含 exec 的测试
python3 -m pytest tests/ -k "exec" -v

# 详细输出
python3 -m pytest tests/ -v -s
```