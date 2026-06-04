# Generic Tools 设计文档

## 概述

Generic Tools 是一套为 LLM Agent 提供系统级操作能力的工具集，兼容 LangGraph 的 tool list 格式。所有工具使用 `@tool` 装饰器定义，基于 LangChain 的 `langchain_core.tools` 构建。

## 设计原则

1. **安全优先** - 所有文件操作限制在允许目录内，shell 命令有危险模式拦截
2. **类型标注** - 所有参数使用 `Annotated[type, description]` 格式，便于 LLM 理解
3. **错误处理** - 所有工具返回字符串，失败时返回 `[ERROR]` 前缀的错误消息
4. **路径安全** - 文件操作限制在 `os.getcwd()`、`/tmp`、`/var/tmp` 目录内

## 工具列表

| 工具名 | 功能 |
|--------|------|
| `exec_tool` | 执行 shell 命令 |
| `read_tool` | 读取文件内容 |
| `write_tool` | 写入文件内容 |
| `grep_tool` | 正则搜索文件 |
| `blob_tool` | 大文件/二进制操作 |
| `ls_tool` | 目录列表 |
| `process_run_tool` | 后台进程管理 |
| `process_status_tool` | 查询进程状态 |
| `process_list_tool` | 列出进程 |
| `system_info_tool` | 即时系统指标 |
| `system_info_processes_tool` | Top 进程列表 |
| `system_monitor_tool` | 持续后台监控 |

---

## exec_tool

执行 shell 命令并返回输出。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `command` | `Annotated[str, ...]` | 必填 | 要执行的 shell 命令 |
| `cwd` | `Annotated[str \| None, ...]` | `None` | 工作目录 |
| `timeout` | `Annotated[int, ...]` | `30` | 超时秒数，0 表示不限 |
| `check` | `Annotated[bool, ...]` | `False` | 非零退出码是否抛异常 |

### 返回值

```
[OK] Command executed successfully
stdout: ...
stderr: ...
exit_code: 0
```

### 安全机制

- 危险命令拦截：`rm -rf /`、`rm -rf *`、`mkfs`、fork bomb 等
- 受限环境变量：`PATH=/usr/bin:/bin`，移除 `LD_*` 等危险变量
- 超时限制：防止命令永久挂起

### 示例

```
exec_tool(command="ls -la", cwd="/tmp", timeout=10)
```

---

## read_tool

读取文件内容，支持 offset 和 limit。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `Annotated[str, ...]` | 必填 | 文件路径 |
| `offset` | `Annotated[int, ...]` | `0` | 起始行号（0-indexed） |
| `limit` | `Annotated[int \| None, ...]` | `None` | 最大行数，None 表示不限 |
| `encoding` | `Annotated[str, ...]` | `"utf-8"` | 文件编码 |

### 返回值

文件内容字符串，或 `[ERROR]` 开头的错误消息。

### 路径限制

只允许访问：`os.getcwd()`、`/tmp`、`/var/tmp`

### 示例

```
read_tool(path="/tmp/test.txt", offset=0, limit=100)
```

---

## write_tool

写入内容到文件，支持多种模式。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `Annotated[str, ...]` | 必填 | 文件路径 |
| `content` | `Annotated[str, ...]` | 必填 | 要写入的内容 |
| `mode` | `Annotated[str, ...]` | `"overwrite"` | 写入模式 |
| `encoding` | `Annotated[str, ...]` | `"utf-8"` | 文件编码 |

### 模式说明

- `overwrite`：覆盖现有文件（默认）
- `append`：追加到文件末尾
- `create`：仅创建新文件，若存在则失败

### 返回值

```
[OK] Written {bytes} bytes to {path}
```

或错误消息。

### 示例

```
write_tool(path="/tmp/output.txt", content="Hello World", mode="overwrite")
```

---

## grep_tool

在文件或目录中搜索正则表达式模式。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `pattern` | `Annotated[str, ...]` | 必填 | 正则表达式模式 |
| `path` | `Annotated[str, ...]` | 必填 | 文件或目录路径 |
| `recursive` | `Annotated[bool, ...]` | `False` | 是否递归搜索子目录 |
| `case_sensitive` | `Annotated[bool, ...]` | `True` | 是否大小写敏感 |
| `context_lines` | `Annotated[int, ...]` | `0` | 上下文行数 |
| `max_results` | `Annotated[int, ...]` | `100` | 最大结果数，0 表示不限 |
| `file_pattern` | `Annotated[str \| None, ...]` | `None` | 文件名过滤模式（如 `*.py`） |

### 返回值

格式：`{file}:{line}:{content}`

```
[OK] Found 3 match(es):

/path/to/file.py:10:def hello():
/path/to/file.py:15:    print("hello world")
/path/to/file.py:20:hello()
```

### 示例

```
grep_tool(pattern="def main", path="src/", recursive=True, file_pattern="*.py")
```

---

## blob_tool

处理大文件或二进制数据，比 read_tool 更安全。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `Annotated[str, ...]` | 必填 | 文件路径 |
| `operation` | `Annotated[str, ...]` | 必填 | 操作类型 |
| `limit` | `Annotated[int, ...]` | `100` | 行数（head/tail）或字节数（b64） |
| `offset` | `Annotated[int, ...]` | `0` | b64 操作的字节偏移 |

### 操作类型

| 操作 | 说明 |
|------|------|
| `head` | 读取前 N 行 |
| `tail` | 读取后 N 行 |
| `size` | 获取文件大小 |
| `exists` | 检查文件是否存在 |
| `encoding` | 检测文本编码 |
| `b64` | Base64 编码文件部分内容 |

### 返回值

```
[OK] /path/to/file: 12345 bytes (0.01 MB)
```

### 示例

```
blob_tool(path="/tmp/large.log", operation="tail", limit=50)
```

---

## ls_tool

列出目录内容，支持多种格式和排序。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | `Annotated[str, ...]` | `"."` | 目录路径 |
| `show_hidden` | `Annotated[bool, ...]` | `False` | 是否显示隐藏文件 |
| `long_format` | `Annotated[bool, ...]` | `True` | 是否使用详细格式 |
| `max_items` | `Annotated[int, ...]` | `100` | 最大显示数量 |
| `sort_by` | `Annotated[str, ...]` | `"name"` | 排序方式：`name`/`size`/`modified` |

### 返回值

```
drwxr-xr-x  4096 Jun  4 10:00 .
drwxr-xr-x   512 Jun  4 10:00 ..
-rw-r--r--  1024 Jun  4 10:00 README.md
-rw-r--r--  2048 Jun  4 10:01 test.py
```

### 示例

```
ls_tool(path="/tmp", show_hidden=True, sort_by="modified")
```

---

## process_run_tool

在后台启动命令，不阻塞 agent。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `command` | `Annotated[str, ...]` | 必填 | 要执行的命令 |
| `cwd` | `Annotated[str \| None, ...]` | `None` | 工作目录 |
| `label` | `Annotated[str \| None, ...]` | `None` | 可选标签标识进程 |
| `detached` | `Annotated[bool, ...]` | `True` | 是否完全分离运行 |

### 返回值

```
[OK] Process started
PID: 12345
Output: /tmp/process_12345.log
Label: my_task
```

### 全局注册表

进程信息存储在内存字典 `_PROCESS_REGISTRY` 中，可通过 `process_status_tool` 查询。

### 示例

```
process_run_tool(command="python3 long_task.py", label="training")
```

---

## process_status_tool

查询特定进程的状态。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `process_id` | `Annotated[str, ...]` | 必填 | 进程 ID 或标签 |

### 返回值

```
[OK] Process status:
PID: 12345
Label: training
Status: running
Exit Code: None
Started: 2024-06-04 10:00:00
```

### 示例

```
process_status_tool(process_id="training")
```

---

## process_list_tool

列出所有注册的进程。

### 返回值

```
[OK] Registered processes:
- Label: training, PID: 12345, Status: running
- Label: backup, PID: 12346, Status: completed (exit 0)
```

### 示例

```
process_list_tool()
```

---

## system_info_tool

收集即时系统指标（CPU、内存、磁盘、网络）。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `metrics` | `Annotated[list[str], ...]` | `None` | 要收集的指标列表 |
| `interval` | `Annotated[float, ...]` | `0.1` | CPU 测量间隔（秒） |

### 指标选项

- `cpu` - CPU 使用率
- `memory` - 内存使用情况
- `disk` - 磁盘空间
- `network` - 网络接口信息
- `all` - 所有指标（默认）

### 返回值

```
=== System Info ===

--- CPU ---
Model: Intel(R) Core(TM) i7-9700K @ 3.60GHz
Cores: 8 cores, 8 threads
Usage: 15.3% (interval: 0.1s)

--- Memory ---
Total: 32 GB
Available: 16 GB
Used: 16 GB (50.0%)
```

### 示例

```
system_info_tool(metrics=["cpu", "memory"], interval=0.5)
```

---

## system_info_processes_tool

获取当前最活跃的进程列表。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sort_by` | `Annotated[str, ...]` | `"cpu"` | 排序方式：`cpu`/`memory`/`pid` |
| `max_processes` | `Annotated[int, ...]` | `10` | 最大显示进程数 |

### 返回值

```
[OK] Top processes by CPU:
  PID  %CPU %MEM     COMMAND
12345  15.2  2.1  python3
12346   8.5  1.5  node
```

### 示例

```
system_info_processes_tool(sort_by="memory", max_processes=5)
```

---

## system_monitor_tool

在后台持续监控系统指标，可记录一段时间的数据后获取。

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | `Annotated[str, ...]` | 必填 | 操作类型 |
| `monitor_id` | `Annotated[str, ...]` | 必填 | 监控实例 ID |
| `duration` | `Annotated[int, ...]` | `60` | 监控持续时间（秒） |
| `interval` | `Annotated[float, ...]` | `1.0` | 采样间隔（秒） |

### 操作类型

| action | 说明 |
|--------|------|
| `start` | 启动后台监控 |
| `stop` | 停止监控 |
| `status` | 查看监控状态 |
| `get` | 获取所有记录 |

### 返回值格式

**start:**
```
[OK] System monitor started
Monitor ID: my_monitor
Duration: 60s, Interval: 1.0s
```

**status:**
```
[OK] Monitor status:
Monitor ID: my_monitor
Status: running
Records: 45
```

**get:**
```
=== System Monitor Records: my_monitor ===

[0] 2024-06-04T10:00:00
  cpu_percent: 15.3
  memory_percent: 50.2
  disk_percent: 45.0
  network_sent: 1234 bytes
  network_recv: 5678 bytes
...
```

### 示例

```python
# 启动监控
system_monitor_tool(action="start", monitor_id="test1", duration=60, interval=1.0)

# 等待一段时间...

# 获取记录
system_monitor_tool(action="get", monitor_id="test1")
```

---

## 架构设计

### 工具注册流程

1. 每个工具定义使用 `@tool` 装饰器
2. 工具汇总到 `agentprof/tools/generic/__init__.py`
3. 创建 agent 时直接传入工具列表

```python
from agentprof.tools.generic import (
    exec_tool, read_tool, write_tool, grep_tool,
    blob_tool, ls_tool, system_info_tool, system_monitor_tool,
    process_run_tool, process_status_tool, process_list_tool,
)

tools = [
    exec_tool, read_tool, write_tool, grep_tool,
    blob_tool, ls_tool, system_info_tool, system_monitor_tool,
    process_run_tool, process_status_tool, process_list_tool,
]

agent = create_agent(llm, tools=tools)
```

### 错误处理模式

所有工具遵循统一的错误处理模式：

```python
try:
    # 执行操作
    result = doSomething()
    return f"[OK] {result}"
except PermissionError:
    return f"[ERROR] Permission denied"
except FileNotFoundError:
    return f"[ERROR] File not found"
except Exception as e:
    return f"[ERROR] {type(e).__name__}: {str(e)}"
```

### 路径安全检查

```python
def _is_safe_path(path: Path) -> bool:
    """检查路径是否在允许的目录内"""
    safe_dirs = [os.getcwd(), "/tmp", "/var/tmp"]
    abs_path = path.expanduser().resolve()
    return any(str(abs_path).startswith(d) for d in safe_dirs)
```

### 进程注册表（内存）

`process_run_tool` 使用全局字典维护进程信息：

```python
_PROCESS_REGISTRY: dict[str, dict] = {}

# 结构
{
    "label_or_pid": {
        "pid": 12345,
        "label": "training",
        "output_file": "/tmp/process_12345.log",
        "start_time": datetime.now(),
        "status": "running"
    }
}
```

---

## 测试覆盖

每个工具都有对应的单元测试和 agent 集成测试：

- `test_generic_tools.py` - 各工具的功能测试
- `test_agent_integration.py` - 工具在 agent 上下文中的测试

测试日志保存在 `unit_test/test_logs/` 目录，文件名与测试函数对应。