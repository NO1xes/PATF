# AgentProf 当前实现问题分析

## 1. 核心定位矛盾

### 1.1 当前定位

AgentProf 是一个**自动化 Profiling 控制器**，定位是：
- 通过外部拦截的方式观察目标 agent 的行为
- 对收集的数据进行分析，生成诊断报告

### 1.2 需求定位

AgentProf 应该是一个**真正的 LLM Agent**，能够：
- 以 LLM 为核心推理引擎，主动决策并执行行动
- 以 agent 负载所影响的整个系统为 profiling 对象

### 1.3 矛盾

| 维度 | 当前实现 | 需求 |
|------|---------|------|
| 角色 | 观察者（passive observer） | 控制者（active controller） |
| LLM 作用 | 信息汇总 + 策略建议 | 推理引擎 + 行动决策 |
| 执行方式 | 确定性流水线（baseline→analysis→report） | 动态多轮交互式 loop |
| 对系统的影响 | 零修改 | 部分干预 |

---

## 2. Controller Loop 的本质

### 2.1 当前实现

```python
# controller.py — 确定性流水线
for i in range(max_iter):
    plan = planner.plan_observation(state)   # LLM 决定用哪个 observer
    approved, reason = validator.validate()   # 确定性检查
    if not approved: break
    execute(plan, state, output_dir)          # 从已有数据收集证据
```

这**不是 agent loop**，只是循环执行固定步骤。

### 2.2 LLM 在当前系统中的角色

```python
# llm_planner.py — LLM 调用的全部内容
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": PLAN_REQUEST_TEMPLATE.format(**ctx)},
    ],
    temperature=0,
)
# LLM 输出 = ObservationPlan JSON（一个数据结构，不是行动）
```

LLM 只是充当"信息汇总 + 建议生成"的角色，不执行任何行动。

### 2.3 矛盾

| 维度 | 当前 | 需求 |
|------|------|------|
| planner 输出 | JSON 格式的观察计划 | 可执行的系统干预 |
| executor | 从已有数据提取证据（只读） | 触发新的 profiling 实验（写） |
| 循环控制 | 固定迭代次数 | 基于 LLM 推理动态决定 |

---

## 3. Observer 设计的隐含假设 vs 真实场景

### 3.1 当前四个 Observer 的假设

| Observer | 依赖假设 |
|---------|---------|
| `LangChainSemanticObserver` | 目标 agent 支持 LangChain `BaseCallbackHandler` |
| `ToolEventsObserver` | 工具代码可修改，可以被 `wrap_tool` 包装 |
| `ResourceSnapshotObserver` | 可在本地运行 psutil（唯一真正通用的） |

### 3.2 真实世界目标 Agent 的情况

| 场景 | 现实 |
|------|------|
| 第三方商业 agent | 代码不可见，无任何 hook |
| 开源 agent（非 LangChain） | 不支持 `BaseCallbackHandler` |
| 企业内部 agent | 不可修改，只能观察 API 调用 |

### 3.3 矛盾

当前 Observer 设计依赖"目标 agent 完全透明可控"的前提：
- `wrap_tool` 需要修改工具代码 → 真实系统不可修改
- `callback` 需要 agent 支持 → 真实系统可能不支持

**所有 Observer 都是概念验证（Proof of Concept）**。当前 observer 设计依赖"目标 agent 完全透明可控"的前提，在真实黑盒场景下会全部失效。

---

## 3.4 BFCL 不能解决什么

### BFCL 对 AgentProf 的价值

```
BFCL 提供测试用例
        ↓
BFCL 运行被测 LLM（这就是 agent）
        ↓
BFCL trace 输出（标准化格式）
        ↓ BFCL Adapter
AgentProf 的 AgentEvent 格式
        ↓
build_timeline() → breakdown → report
```
**BFCL 只能作为评估 agent能力 的工具**，或许可以作为 AgentProf 的一个工具提供给他，但是其本身并不能对 system profiling 带来任何作用，其提供的 trace 也只是对于特定场景下(特定测试用例下)的 trace，可以作为 AgentProf 定位问题时的辅助样例模板，但是不能直接将其当作通用的 profiling 对象

### BFCL 不能解决的问题

```
Toy tasks                BFCL                  真实黑盒 agent
──────────             ────────                ─────────────
Agent 自己写的        BFCL 跑已知 LLM             第三方 agent
工具完全可控          trace 格式标准化             你什么都拿不到
                    但 LLM 对 BFCL 是透明的

BFCL 不是"解决黑盒问题"
BFCL 是"用已知 agent 生成标准 trace，然后用 AgentProf 分析这个 trace"
```

BFCL adapter 的任务是格式转换，不是让黑盒变透明。真实黑盒 agent 的 profiling 问题，**没有通用解决方案**，取决于黑盒提供什么接口：

| 黑盒提供的接口 | AgentProf 能做的 |
|--------------|-----------------|
| OpenAI-compatible API | Monkey-patch client（已有） |
| Tracing/metrics endpoint | 读取 metrics（vllm_metrics 未实现） |
| Request/response only | 只能分析 I/O |
| 完全无接口 | 什么都做不了 |

---

## 4. Profiling 对象的矛盾

### 4.1 当前实际 profiling 的对象

```
目标 Agent（被 profiling 的核心）
    │
    ├── tool_call timing
    ├── llm_request timing
    ├── agent 内部决策（callback）
    └── 本机资源（CPU/memory）
```

### 4.2 真正想要 profiling 的对象

```
被 Agent 负载驱动的系统
    │
    ├── LLM API Server (vLLM / OpenAI / Anthropic)
    │       └── profiling 对象：GPU 利用率、KV cache 命中率、batch 队列深度
    │
    ├── External Tools / APIs
    │       └── profiling 对象：server-side 延迟、API 处理时间
    │
    ├── Database
    │       └── profiling 对象：查询计划、锁等待、连接池状态
    │
    └── Network Infrastructure
            └── profiling 对象：DNS 延迟、TCP 重传率、中间件耗时
```

### 4.3 矛盾

| 维度 | 当前 | 需求 |
|------|------|------|
| 视角 | 从 agent 内部向外看 | 从系统响应向内看 |
| Profiling 对象 | agent 的"行为" | agent 造成的"负载影响" |
| 能看到 | tool call timing、LLM timing | GPU 利用率、API server 延迟、数据库查询计划 |
| Observer 层 | agent_semantic、llm_serving、tool_execution | vllm_metrics、external_api、database、network_path |

---

## 6. Observer 设计层次对比

### 6.1 当前 Observer 层次

```
layer: agent_semantic    → LangChain 内部 callback
layer: llm_serving       → Monkey-patch OpenAI client
layer: tool_execution    → wrap_tool 包装工具函数
layer: hardware_resource → psutil 后台线程（唯一真正通用）
```

### 6.2 需要的 Observer 层次
这是 ai 分析生成的，不要全信，像 database 这种东西不太可能能看到，而运行 agent 的系统的信息如 cpu 资源、内存资源却应该是重点关注对象
```
layer: vllm_metrics      → GPU 利用率、batch size、队列深度（需要 vLLM metrics endpoint）
layer: external_api      → Server-side API 延迟（需要 API 支持 tracing）
layer: database          → 查询计划、锁等待（需要数据库监控工具）
layer: network_path      → DNS 延迟、TCP 重传率（需要 distributed tracing）
```

**当前 Observer 设计无法适应系统级 profiling 的需求。**

---

## 7. 总结：两个根本不同的系统目标

### 7.1 系统 A（当前实现）

```
定位：自动化 Profiling 工具（"观察者"）
目标：对已知的目标 agent 进行 profiling
LLM 角色：辅助决策（planning assistant）
对系统的影响：零修改
Profiling 范围：目标 agent 内部行为
```

### 7.2 系统 B（需求）
还是一样，对于 database 的观测不太可能，而对于 cpu、内存资源的观察很有必要
```
定位：真正的 LLM Agent（"控制者"）
目标：对被 agent 负载驱动的整个系统进行 profiling
LLM 角色：核心推理和决策引擎
对系统的影响：部分干预（需要解除部分禁忌）
Profiling 范围：agent → LLM server / API / Database / Network
```

### 7.3 核心问题

把 AgentProf 从系统 A 变成系统 B **不是简单地在某个部分加功能**，而是需要：

1. **重新定义核心目标**：是继续做"profiling 工具"还是"agent 系统控制器"？
2. **扩展 LLM 角色**：从"信息汇总"到"推理 + 行动决策"
3. **扩展 Executor**：从"只读已有数据"到"可触发新的 profiling 实验"
4. **设计新的 Observer 层**：系统级 profiling（vllm_metrics、external_api 等）
5. **重新评估 FORBIDDEN_ACTIONS**：部分禁忌需要解除以支持主动 probing

---

## 8. 建议的技术路线
这部分我就全删了，ai 写的实在不太靠谱，还是要人工审核


## 9. 写在后面
现在的整个系统设计有些歪，不是一个 agent 应该的设计样式。  
会议上老师提到可能可以考虑广度，比如单系统上跑多个 agent。  
整个 profiling 设计的核心是系统而非 agent，对于 agent 的观测仅仅只能作为参考因素，得到的无论哪个阶段的信息都要能够被翻译为系统的语言。  
负载为 agent 程序的系统和对应的 llm 服务系统需要分别 profiling，因为其资源占用有明显差异。  
甚至于说由于现实 agent 的黑盒性质，需要考虑到避开 agent 语义下的观察，纯粹从系统角度出发。  
实际的 profiling 不应该是对于完全受我们掌控的子 agent 进行的，应该是在一个运行有任意 agent 的系统上进行，profiling 应该展现出其通用性。  
所有在之前实现的 observer 中能够收集到的信息在现实场景中都是得不到的，我们无法直接得到 tool call 的详细信息。  
目前实现的内容本质是一个 log收集 + llm分析 的功能。

