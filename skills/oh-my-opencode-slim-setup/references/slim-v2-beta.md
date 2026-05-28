# OmO-slim V2 后台编排 Beta 说明

> **状态**：Beta 版本，需要启用实验性特性
> **适用**：大型项目、需要并行执行多个专家 Agent 的场景

---

## V2 与 V1 的区别

| 对比项 | V1 稳定版 | V2 Beta 版 |
|--------|----------|------------|
| Orchestrator 角色 | 执行工作器 | 调度器 |
| 专家 Agent 运行 | 前台阻塞 | 后台并行 |
| 任务执行 | 串行为主 | 可并行调度 |
| 适用场景 | 日常开发 | 大型项目、多任务并行 |
| 状态轮询 | 无 | 定期轮询专家状态 |
| 结果核对 | 等待返回后继续 | 调度后继续，定期核对结果 |

---

## V2 核心特性

### 1. Orchestrator 作为调度器

V2 中，Orchestrator 不直接执行大部分工作，而是：
- **规划工作**：分析需求，制定执行计划
- **调度专家**：将工作分发给专家 Agent
- **状态轮询**：定期检查专家 Agent 的进度
- **结果核对**：收集专家结果，验证完成度

### 2. 专家 Agent 后台运行

专家 Agent（Explorer, Librarian, Oracle, Designer, Fixer 等）在后台运行：
- Orchestrator 调度后继续工作
- 不阻塞 Orchestrator
- 完成后自动上报结果

### 3. `/deepwork` 命令

V2 新增 `/deepwork` 命令：
- 将宏大目标转化为基于文件的具体计划
- 生成计划文件在 `.slim/deepwork/` 目录
- 支持断点续传

---

## 安装 V2 Beta

### 前置条件

- OpenCode 支持 `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=1` 环境变量
- OmO-slim Beta 版本已安装

### 安装命令

```bash
# 安装 Beta 版
bunx oh-my-opencode-slim@beta install --no-tui --skills=yes

# 启动 OpenCode 并启用后台子智能体
OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=1 opencode
```

### Windows 设置环境变量

```powershell
# 临时设置（当前终端）
$env:OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS = "1"
opencode

# 持久化设置（用户级）
[Environment]::SetEnvironmentVariable("OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS", "1", "User")
opencode
```

### Mac/Linux 设置环境变量

```bash
# 临时设置
export OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=1
opencode

# 持久化设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=1' >> ~/.bashrc
source ~/.bashrc
opencode
```

---

## V2 使用方式

### 使用 `/deepwork` 命令

```
/deepwork 实现用户管理模块，包含前后端和测试
```

Orchestrator 会：
1. 分析需求
2. 将目标转化为文件级计划
3. 保存计划到 `.slim/deepwork/` 目录
4. 调度专家 Agent 在后台执行
5. 定期轮询进度
6. 核对结果

### 查看计划文件

```
.slim/deepwork/
├── user-management-plan.md
├── progress.json
└── tasks/
    ├── backend-api.task.md
    ├── frontend-page.task.md
    └── tests.task.md
```

### 断点续传

如果中途退出，下次启动会自动恢复：

```
Resuming 'user-management' - 2 of 3 tasks complete
```

---

## V2 工作流程图

```
用户输入需求
   │
   ├─ Orchestrator 分析
   │
   ├─ 制定执行计划
   │
   ├─ 调度专家 Agent（后台）
   │   ├─ @explorer → 后台搜索代码
   │   ├─ @librarian → 后台查文档
   │   ├─ @oracle → 后台架构分析
   │   ├─ @designer → 后台 UI 实现
   │   └─ @fixer → 后台快速实现
   │
   ├─ Orchestrator 继续工作（不阻塞）
   │
   ├─ 定期轮询专家状态
   │
   ├─ 专家完成后上报结果
   │
   ├─ Orchestrator 核对结果
   │
   └─ 汇报给用户
```

---

## V2 与 V1 切换

### 回退到 V1 稳定版

```bash
# 不设置环境变量
opencode

# 或卸载 Beta 版，安装稳定版
bunx oh-my-opencode-slim@latest install --no-tui --skills=yes
opencode
```

---

## V2 Beta 注意事项

### 1. 实验性特性

V2 是 Beta 版本，可能存在：
- 未发现的 Bug
- 行为变化
- 性能问题

### 2. 资源消耗

后台并行运行多个 Agent 会增加：
- API 调用次数
- 内存占用
- 并发请求

### 3. 不适合所有场景

V2 更适合：
- 大型项目
- 多任务并行
- 需要长时间运行的复杂任务

V1 更适合：
- 日常开发
- 简单任务
- 交互式对话

---

## V2 配置示例

目前 V2 不需要额外配置，只需启用环境变量。

未来可能支持的配置：

```jsonc
{
  "experimental": {
    "background_subagents": {
      "enabled": true,
      "max_parallel": 5,  // 最大并行数
      "poll_interval_ms": 5000  // 轮询间隔
    }
  }
}
```

---

## 常见问题

### Q: 启动后报错 `background subagents not supported`？

**原因**：OpenCode 版本不支持此特性。

**解决**：升级 OpenCode 到最新版本。

### Q: 专家 Agent 没有在后台运行？

**检查**：
```bash
echo $OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS
```

确认环境变量已设置。

### Q: V2 比 V1 慢？

**原因**：V2 的调度和轮询开销可能增加延迟。

**建议**：对于简单任务，使用 V1；对于复杂任务，使用 V2。

---

## 参考链接

- OmO-slim V2 发布说明：https://github.com/alvinunreal/oh-my-opencode-slim/releases
- OpenCode 后台子智能体文档：https://opencode.ai/docs/experimental/background-subagents