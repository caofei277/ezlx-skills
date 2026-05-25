# OpenCode + OmO 完整使用手册

> 适用于已集成 oh-my-openagent 插件的 OpenCode 环境
> 基于三平台配置：OpenCode Zen + OpenCode Go + 智谱 Pro
> 成本规则：GLM-5.1/GLM-5-Turbo 高峰期（14:00-18:00）3倍、非高峰期2倍（6月底前1倍）；GLM-4.7 固定1倍；DeepSeek Free 免费

---

## 目录

- [一、界面与导航](#一界面与导航)
- [二、Agent 切换与角色说明](#二agent-切换与角色说明)
- [三、三种工作模式](#三三种工作模式)
- [四、智能体编排详解](#四智能体编排详解)
- [五、Category 任务委派](#五category-任务委派)
- [六、跨平台额度自动切换](#六跨平台额度自动切换)
- [七、内置命令全览](#七内置命令全览)
- [八、Skills 技能系统](#八skills-技能系统)
- [九、工具系统](#九工具系统)
- [十、会话管理与跨会话继续](#十会话管理与跨会话继续)
- [十一、自定义配置调整](#十一自定义配置调整)
- [十二、常见场景操作指南](#十二常见场景操作指南)
- [十三、模型分级体系与手动升级](#十三模型分级体系与手动升级)
- [十四、常见问题与故障排查](#十四常见问题与故障排查)
- [十五、变更与维护](#十五变更与维护)
- [十六、卸载与回退](#十六卸载与回退)

## 一、界面与导航

### 启动

```bash
cd /path/to/your/project
opencode
```

启动后进入 TUI（终端交互界面），你会看到：
- **左侧**：文件树
- **右侧**：对话区域
- **底部**：输入框

### 关键快捷键

| 按键 | 功能 |
|------|------|
| **Tab** | 切换 Agent（Sisyphus → Hephaestus → Prometheus → Atlas） |
| **Enter** | 发送消息 |
| **Ctrl+C** | 中断当前 Agent 操作 |
| **Esc** | 取消当前输入 |
| **Ctrl+D** | 退出 OpenCode |

### 底部输入框

所有操作都通过底部输入框完成。你可以：
- 直接输入自然语言对话
- 输入 `/` 开头的命令（如 `/models`、`/start-work`）
- 输入 `@plan` 触发规划模式
- 输入 `ulw` 或 `ultrawork` 触发全自动模式

---

## 二、Agent 切换与角色说明

### 如何切换 Agent

按 **Tab** 键，在以下 Agent 之间循环切换：

```
Sisyphus → Hephaestus → Prometheus → Atlas → （循环回 Sisyphus）
```

切换后输入框上方会显示当前 Agent 名称。

### 各 Agent 角色详解

#### Sisyphus（主编排者）— 默认 Agent

**什么时候用**：90% 的日常开发任务。这是你的默认工作 Agent。

**能力**：
- 接收你的需求，分析意图
- 将复杂任务拆解为子任务
- 委派给其他 Agent 并行执行
- 跟踪任务进度，确保完成

**你的模型分配**：
- 普通模式：`OpenCode DeepSeek V4 Flash Free`（免费、百万上下文）
- ultrawork 模式：`GLM-5.1`（智谱，最强推理）
- 额度用完自动切：Go DeepSeek V4 Flash → 智谱 GLM-4.7

**使用方式**：
```
直接输入你的需求即可，例如：
"给用户管理模块增加批量导入功能"
"修复登录页面的表单验证 Bug"
```

#### Hephaestus（深度自主工人）

**什么时候用**：需要 GPT 级别的深度推理、复杂架构设计、跨文件重构。

**能力**：
- 给定目标后完全自主探索和执行
- 深度研究代码库模式再动手
- 不会中途停下来等你，一直干到完

**使用方式**：
```
1. 按 Tab 切换到 Hephaestus
2. 输入你的目标（描述要什么，不要教它怎么做）
```

**示例**：
```
"设计一套插件系统，支持热加载和依赖注入"
"把这个 Express 项目迁移到 Hono 框架"
```

#### Prometheus（战略规划师）

**什么时候用**：多天的大型项目、需要精确规划的生产级变更。

**模型**：GLM-5-Turbo（长链路执行、工具调用、指令遵循优化，⚠️高峰3倍/非高峰2倍）

**能力**：
- 像真实主管一样采访你，深挖需求
- 自动咨询 Metis（审查遗漏）和 Momus（严格评审）
- 生成详细计划文件保存在 `.omo/plans/` 目录
- 只能修改 `.omo/` 目录下的 Markdown 文件，不会碰代码

**使用方式**：
```
方法一：按 Tab 切换到 Prometheus，然后描述你的需求
方法二：在 Sisyphus 中输入 @plan "你的需求"
```

**规划流程**：
```
你描述需求
  → Prometheus 采访你（问 3-8 个问题）
  → 你回答问题
  → Metis 审查计划遗漏
  → （可选）Momus 严格评审
  → 生成计划文件到 .omo/plans/xxx.md
  → 你确认计划
  → 输入 /start-work 开始执行
```

#### Atlas（编排执行者）

**什么时候用**：Prometheus 规划完成后，用它来执行计划。通常不需要手动切换到 Atlas。

**能力**：
- 读取 Prometheus 生成的计划
- 按任务分配给 Sisyphus-Junior 等子 Agent
- 累积学习（前面任务的经验传给后面的任务）
- 自动验证每个任务的完成质量

**使用方式**：
```
不需要手动切换。输入 /start-work 后自动激活 Atlas。
```

### 咨询型 Agent（不能直接切换，由 Sisyphus 自动调用）

这些 Agent 你不直接操作，Sisyphus 会按需调用：

| Agent | 角色 | 模型 | 触发方式 |
|-------|------|------|---------|
| **Oracle** | 架构顾问 | 智谱 GLM-4.7 | `Ask @oracle 你的问题` |
| **Librarian** | 文档搜索 | DeepSeek V4 Flash Free | `Ask @librarian 你的问题` |
| **Explore** | 代码搜索 | DeepSeek V4 Flash Free | `Ask @explore 你的问题` |
| **Multimodal-Looker** | 图片/PDF 分析 | Go Qwen 3.6 Plus | `look_at(图片路径)` |
| **Metis** | 计划审查 | 智谱 GLM-4.7 | Prometheus 规划时自动调用 |
| **Momus** | 严格评审 | 智谱 GLM-5-Turbo | Prometheus 高精度模式自动调用 |
| **Sisyphus-Junior** | 任务执行者 | 按 Category 路由 | Atlas 或 Sisyphus 自动调用 |

### 显式调用咨询 Agent

你可以在对话中直接要求 Sisyphus 咨询某个专家：

```
Ask @oracle to review this design and propose an architecture
Ask @librarian how this is implemented in the latest version
Ask @explore for the policy on this feature
```

---

## 三、三种工作模式

### 模式一：直接对话（日常使用，零成本）

**适用**：简单任务、快速修复、单文件改动。

**操作**：直接在 Sisyphus 中输入你的需求。底层使用免费的 DeepSeek V4 Flash Free。

```
"把登录接口的超时时间从 30 秒改为 60 秒"
"给这个组件加一个 loading 状态"
```

**成本**：DeekSeek Free 零成本。

**区别**：虽然操作和以前一样，但底层 Sisyphus 会自动判断是否需要调用其他 Agent 帮忙。

### 模式二：Ultrawork 全自动模式（⚠️ 高成本，谨慎使用）

> ⚠️ **高峰期（14:00-18:00）GLM-5.1 消耗 3倍额度！非高峰期2倍（6月底前1倍）。建议非高峰期使用。**

**适用**：复杂任务，让 Agent 自己探索搞定。

**操作**：在提示词中包含 `ultrawork` 或 `ulw`。

```
ultrawork 实现一套完整的多租户商家管理 CRUD，包括前后端
```

或简写：
```
ulw 修复所有失败的测试用例
```

**Ultrawork 幕后流程**：

```
你输入 ulw + 任务描述
  │
  ├─ IntentGate 分析你的真实意图（实现？修复？重构？调研？）
  │
  ├─ Sisyphus 切换到 ultrawork 模式（使用 GLM-5.1，⚠️ 高成本）
  │
  ├─ 自动探索代码库（调用 Explore Agent，免费 DeepSeek）
  │
  ├─ 自动查阅文档（调用 Librarian Agent，免费 DeepSeek）
  │
  ├─ 制定执行计划
  │
  ├─ 按任务类型分配给子 Agent 并行执行
  │   ├─ 前端任务 → Qwen 3.6 Plus（Go，Category: visual-engineering）
  │   ├─ 逻辑/写代码任务 → GLM-4.7（智谱，Category: unspecified-low/deep）
  │   ├─ 快速修改 → DeepSeek Free（免费，Category: quick）
  │   └─ 复杂推理 → GLM-5.1（智谱，Category: ultrabrain）
  │
  ├─ 每个任务完成后自动验证
  │
  └─ 所有任务完成后向你汇报  
```

### 模式三：Prometheus 精确规划模式（⚠️GLM-5-Turbo 长链路优化）

**适用**：多天的大型项目、需要精确规划的生产级变更、你想先看计划再执行。

**操作**：

```
步骤 1：进入规划模式
  - 方法 A：按 Tab 切到 Prometheus
  - 方法 B：在 Sisyphus 中输入 @plan "你的需求"

步骤 2：回答 Prometheus 的采访问题（GLM-5-Turbo，长链路规划优化）

步骤 3：审查生成的计划（.omo/plans/ 目录）

步骤 4：执行计划
  输入 /start-work
  Atlas 会自动接管，按计划逐任务执行
```

### 模式选择决策树

```
你的任务是什么？
  │
  ├─ 单文件小改动 → 直接对话（免费）
  │
  ├─ 中等复杂度 → ulw（⚠️ 高峰期3倍，非高峰期2倍/6月底前1倍）
  │
  ├─ 复杂但懒得写详细需求 → ulw（⚠️ 高峰期慎用）
  │
  ├─ 复杂且需要精确控制 → @plan 规划（1倍） → /start-work 执行
  │
  └─ 超大型多天项目 → @plan 规划（1倍） → /start-work 执行
```

---

## 四、智能体编排详解

### Sisyphus 如何编排其他 Agent

当你在 Sisyphus 中输入一个复杂需求时，它的工作流程：

```
Sisyphus 接收你的需求
  │
  ├─ 1. IntentGate 分析意图
  │     判断是：实现 / 修复 / 重构 / 调研 / 分析
  │
  ├─ 2. 制定执行计划
  │     将大任务拆解为多个子任务
  │
  ├─ 3. 委派子任务
  │     ├─ task(category="visual-engineering") → Qwen 3.6 Plus 做前端
  │     ├─ task(category="ultrabrain") → GLM-5.1 做逻辑
  │     ├─ task(category="quick") → OpenCode DeepSeek V4 Flash Free 做小活
  │     ├─ call_omo_agent(subagent_type="oracle") → 咨询架构
  │     ├─ call_omo_agent(subagent_type="explore") → 搜索代码
  │     └─ call_omo_agent(subagent_type="librarian") → 查文档
  │
  ├─ 4. 收集结果，验证完成度
  │
  └─ 5. 汇报给你
```

### 后台并行 Agent

Sisyphus 可以同时开多个后台 Agent 并行工作：

```
你："ulw 实现用户管理模块，同时调研竞品的权限系统设计"

Sisyphus 会同时：
  ├─ 前台：实现用户管理模块代码
  ├─ 后台 Agent 1：用 Explore 搜索现有代码模式
  ├─ 后台 Agent 2：用 Librarian 调研权限系统最佳实践
  └─ 后台 Agent 3：用 Oracle 分析架构影响
```

后台 Agent 完成后系统会通知你，Sisyphus 会自动获取结果。

### Hephaestus 的自主工作模式

Hephaestus 和 Sisyphus 的区别：

| 对比项 | Sisyphus | Hephaestus |
|--------|----------|------------|
| 工作方式 | 拆解任务，委派给子 Agent | 自己一个人从头干到尾 |
| 模型 | DeepSeek Free / GLM-5.1(ultrawork) | GLM-5.1（智谱，⚠️高成本） |
| 适合 | 需要多 Agent 协作的任务 | 需要深度推理的单一任务 |
| 你需要做的 | 描述需求 | 描述目标（不要教它怎么做） |

**什么时候用 Hephaestus**：
```
Tab 切到 Hephaestus，然后输入：

"设计并实现一套事件驱动的消息队列系统"
"追踪这个内存泄漏，它在高并发时每隔 2 小时出现一次"
"把这个 monolith 重构为微服务架构"
```

---

## 五、Category 任务委派

当 Sisyphus 将任务委派给 Sisyphus-Junior 时，它不指定模型名，而是指定 **Category（类别）**。系统自动按类别选模型。

### 你的 Category 模型分配表

| Category | 用途 | 主模型 | 成本 | 额度用完切 |
|----------|------|--------|------|-----------|
| `visual-engineering` | 前端、UI、设计、样式 | Go Qwen 3.6 Plus | Go额度 | 智谱 GLM-4.7 → DeepSeek Free |
| `ultrabrain` | 深度逻辑、架构决策 | 智谱 GLM-5.1 | ⚠️3倍/2倍 | 智谱 GLM-5-Turbo → 智谱 GLM-4.7 |
| `deep` | 自主深度问题解决 | 智谱 GLM-4.7 | 1倍 | DeepSeek Free |
| `artistry` | 创意、艺术任务 | Go Qwen 3.6 Plus | Go额度 | 智谱 GLM-4.7 → DeepSeek Free |
| `quick` | 小改动、改错字、单文件 | DeepSeek V4 Flash Free | 免费 | Go DeepSeek Flash |
| `unspecified-low` | 一般中等难度任务 | 智谱 GLM-4.7 | 1倍 | DeepSeek Free |
| `unspecified-high` | 一般高难度任务 | 智谱 GLM-5-Turbo | ⚠️3倍/2倍 | 智谱 GLM-4.7 → DeepSeek Free |
| `writing` | 文档、写作 | 智谱 GLM-4.7 | 1倍 | DeepSeek Free |

### 你不需要手动选 Category

Sisyphus 会根据你的需求自动判断。例如：

```
你："给登录页加一个动画效果"
→ Sisyphus 委派 task(category="visual-engineering")

你："修复这个空指针异常"
→ Sisyphus 委派 task(category="quick")

你："设计一套权限系统的架构"
→ Sisyphus 委派 task(category="ultrabrain")
```

---

## 六、跨平台额度自动切换

### 工作原理

当你某个平台的额度用完（API 返回 429 限流错误）时，OmO 的 `runtime_fallback` 会自动切换到另一个平台的同款或类似模型。

### 你的回退链示例

```
Sisyphus 要用 DeepSeek Free
  → OpenCode DeepSeek V4 Flash Free（正常使用，零成本）
  → Free 额度用完（429）
  → 自动切 Go DeepSeek V4 Flash（换付费平台）
  → Go 也用完（429）
  → 自动切 智谱 GLM-4.7（智谱兜底，1倍消耗）
```

```
Hephaestus 要用 GLM-5.1（⚠️高成本）
  → 智谱 GLM-5.1（正常使用）
  → 智谱额度用完（429）
  → 自动切 智谱 GLM-5-Turbo（智谱内部降级）
  → 也用完 → 智谱 GLM-4.7（继续降级）
```

### 切换时你会看到什么

切换时 TUI 会弹出一个 toast 通知，类似：
```
⚠ Runtime fallback: opencode-go/glm-5.1 → zhipu-coding-plan/glm-5.1
```

### 配置位置

回退链配置在 `~/.config/opencode/oh-my-openagent.json` 的 `fallback_models` 字段。`runtime_fallback` 控制切换行为：

```json
"runtime_fallback": {
  "enabled": true,            // 开启自动切换
  "retry_on_errors": [400, 429, 500, 502, 503, 504],  // 这些错误码触发切换
  "max_fallback_attempts": 3, // 最多尝试 3 个备选
  "cooldown_seconds": 60,     // 60 秒后重试原来的模型
  "notify_on_fallback": true  // 切换时通知你
}
```

---

## 七、内置命令全览

所有命令在输入框中输入，以 `/` 开头。

### 核心命令

| 命令 | 用途 | 使用方式 |
|------|------|---------|
| `ultrawork` / `ulw` | 全自动模式 | 在提示词中包含即可，如 `ulw 实现用户注册` |
| `@plan "需求"` | 进入规划模式 | 在 Sisyphus 中输入 |
| `/start-work` | 执行 Prometheus 生成的计划 | 规划完成后输入 |
| `/models` | 查看可用模型列表 | 随时输入 |

### 工作流命令

| 命令 | 用途 | 使用方式 |
|------|------|---------|
| `/init-deep` | 生成树状 AGENTS.md 知识库 | `/init-deep` |
| `/ralph-loop "任务"` | 自引用闭环，不完成不停止 | `/ralph-loop "修复所有测试"` |
| `/ulw-loop "任务"` | ultrawork 闭环模式 | `/ulw-loop "重构支付模块"` |
| `/cancel-ralph` | 取消当前 Ralph Loop | `/cancel-ralph` |
| `/refactor <目标>` | 智能重构 | `/refactor src/utils/format.ts` |
| `/stop-continuation` | 停止所有延续机制 | Agent 不停时使用 |
| `/handoff` | 生成交接文档 | 准备关机前使用 |

### 命令详解

#### /init-deep

为整个项目生成层级式知识库，Agent 会自动加载对应目录的上下文：

```bash
/init-deep
```

生成效果：
```
project/
├── AGENTS.md              # 全局架构与约定
├── src/
│   ├── AGENTS.md          # src 级规范
│   └── components/
│       └── AGENTS.md      # 组件级详细说明
```

#### /ralph-loop

让 Agent 持续工作直到任务 100% 完成。Agent 停下来会被自动拉回去继续：

```bash
/ralph-loop "实现完整的订单管理 CRUD，包含单元测试"
/ralph-loop "重构认证模块" --max-iterations=50
```

默认最多 100 轮，可以用 `--max-iterations` 调整。

#### /ulw-loop

和 ralph-loop 一样，但全程开启 ultrawork 最高强度模式。

#### /refactor

智能重构，使用 LSP + AST-Grep + TDD 验证：

```bash
/refactor src/utils/format.ts
/refactor src/services/ --scope=module --strategy=safe
```

#### /start-work

读取最新的 Prometheus 计划，启动 Atlas 执行：

```bash
/start-work              # 使用最新的计划
/start-work plan-name    # 使用指定计划
```

**支持断点续传**：如果你中途中断（关机、退出），下次输入 `/start-work` 会从上次进度继续。

#### /handoff

生成交接文档，包含当前工作状态、已完成的、待完成的。适合需要关机后在新会话中继续工作。

#### /stop-continuation

Agent 不停地工作时，输入这个命令让它停下来。

---

## 八、Skills 技能系统

### 内置 Skills

| Skill | 触发关键词 | 说明 |
|-------|-----------|------|
| `playwright` | 浏览器、截图、测试 | 浏览器自动化 |
| `git-master` | commit、rebase、提交 | 原子提交、风格检测 |
| `frontend-ui-ux` | UI/UX、样式、界面 | 设计师级前端实现 |
| `review-work` | "review my work" | 5 个并行审查子 Agent |
| `ai-slop-remover` | "remove AI slop" | 去除 AI 代码味道 |

### 如何触发 Skill

你不需要手动调用 Skill。Sisyphus 会根据你的需求自动加载对应的 Skill：

```
你："提交这些改动" → 自动加载 git-master
你："在浏览器中测试一下登录页" → 自动加载 playwright
你："把这个页面做得好看一点" → 自动加载 frontend-ui-ux
你："review my work" → 自动加载 review-work
```

### Skill + Category 组合

Sisyphus 可以将 Skill 和 Category 组合使用：

```
你："做一个漂亮的登录页"
→ task(category="visual-engineering", load_skills=["frontend-ui-ux"])
→ Qwen 3.6 Plus + UI/UX 专业知识
```

---

## 九、工具系统

OmO 注册了以下工具供 Agent 使用，你不需要直接操作，但了解它们有助于理解 Agent 的能力边界。

### 代码导航工具（LSP）

| 工具 | 功能 |
|------|------|
| `lsp_goto_definition` | 跳转到定义（Agent 知道函数在哪里定义的） |
| `lsp_find_references` | 查找所有引用（Agent 知道谁在用这个函数） |
| `lsp_rename` | 跨工作区重命名（安全地重命名变量/函数） |
| `lsp_diagnostics` | 获取错误/警告（Agent 写完代码会自动检查有没有报错） |
| `lsp_symbols` | 文件大纲（Agent 理解文件结构） |

### 代码搜索工具

| 工具 | 功能 |
|------|------|
| `grep` | 正则内容搜索 |
| `glob` | 文件名模式匹配 |
| `ast_grep_search` | AST 感知搜索（理解语法结构，不只是文本匹配） |
| `ast_grep_replace` | AST 感知替换（安全地批量重构） |

### 委派工具

| 工具 | 功能 |
|------|------|
| `task` | 按 Category 委派任务给 Sisyphus-Junior |
| `call_omo_agent` | 调用特定 Agent（Explore、Librarian 等） |
| `background_output` | 获取后台任务结果 |
| `background_cancel` | 取消后台任务 |

### 会话工具

| 工具 | 功能 |
|------|------|
| `session_list` | 列出所有历史会话 |
| `session_read` | 读取某个会话的历史 |
| `session_search` | 搜索历史会话内容 |

### 视觉工具

| 工具 | 功能 |
|------|------|
| `look_at` | 分析图片/PDF，通过 Multimodal-Looker Agent |

### Hashline Edit（安全编辑）

启用后，Agent 读到的每行代码都带哈希标记：
```
11#VK| function hello() {
22#XJ|   return "world";
33#MB| }
```

Agent 编辑时必须验证哈希，如果文件已经被改过，编辑会被拒绝。这防止了 Agent 改错行。

---

## 十、会话管理与跨会话继续

### 会话持久化

OmO 的工作状态保存在 `.omo/` 目录：

```
.omo/
├── plans/          # Prometheus 生成的计划
├── tasks/          # 任务状态
├── notepads/       # 累积的学习笔记
└── boulder.json    # 当前工作进度
```

### 断点续传

如果你中途退出（关机、Ctrl+C、会话超时），下次可以继续：

```bash
# 1. 重新启动 opencode
opencode

# 2. 输入 /start-work
/start-work

# OmO 会检测到未完成的工作，自动从断点继续
# 例如显示："Resuming '用户管理模块' - 3 of 8 tasks complete"
```

### /handoff 交接

如果需要完全新建会话继续工作：

```bash
/handoff
```

这会生成一份交接文档，包含：
- 当前任务进度
- 已完成的和待完成的
- 关键文件路径
- 上下文摘要

### Todo 强制执行

Agent 不能摸鱼。如果 Agent 中途停下来没有完成所有 todo：

```
[SYSTEM REMINDER - TODO CONTINUATION]

You have incomplete todos! Complete ALL before responding:
- [ ] Implement user service ← IN PROGRESS
- [ ] Add validation
- [ ] Write tests

DO NOT respond until all todos are marked completed.
```

---

## 十一、自定义配置调整

### 配置文件位置

| 文件 | 位置 | 作用 |
|------|------|------|
| OmO 配置 | `~/.config/opencode/oh-my-openagent.json` | Agent 模型分配、Category、fallback |
| TUI 插件 | `~/.config/opencode/tui.json` | TUI 界面插件注册 |
| OpenCode 配置 | `~/.config/opencode/opencode.json` | Provider、MCP、默认模型 |

### 常见调整

#### 更换某个 Agent 的模型

编辑 `oh-my-openagent.json`：

```json
{
  "agents": {
    "sisyphus": { "model": "opencode-go/glm-5.1" }
  }
}
```

#### 添加自定义 Category

```json
{
  "categories": {
    "rust-expert": {
      "model": "opencode-go/glm-5.1",
      "description": "Rust 专家",
      "prompt_append": "Focus on safe Rust patterns and idiomatic code."
    }
  }
}
```

#### 调整后台任务并发数

```json
{
  "background_task": {
    "providerConcurrency": {
      "opencode-go": 10,
      "bailian-coding-plan": 5,
      "zhipu-coding-plan": 5
    }
  }
}
```

#### 禁用某个 Hook

```json
{
  "disabled_hooks": ["comment-checker"]
}
```

#### 禁用某个 Skill

```json
{
  "disabled_skills": ["playwright"]
}
```

#### 关闭匿名遥测

设置环境变量：
```powershell
# Windows 持久化
[Environment]::SetEnvironmentVariable("OMO_SEND_ANONYMOUS_TELEMETRY", "0", "User")
```

---

## 十二、常见场景操作指南

### 场景 1：快速修个 Bug

```
直接在 Sisyphus 中输入：

"修复 src/utils/format.ts 里的日期格式化 Bug，输入 undefined 时会崩溃"
```

Sisyphus 会自动用 `quick` Category，调用 OpenCode DeepSeek V4 Flash Free 快速修复。

### 场景 2：开发一个新功能

```
ulw 实现用户注册功能，包含：
- 后端 API（Gin 路由 + 数据库操作）
- 前端注册页面（React 19 + 表单验证）
- 单元测试
```

Sisyphus 会拆解为多个子任务并行执行。

### 场景 3：大型项目先规划再执行

```
步骤 1：@plan "重构认证系统，从 Session 迁移到 JWT"

步骤 2：回答 Prometheus 的采访问题

步骤 3：审查生成的计划（.omo/plans/ 目录）

步骤 4：/start-work

步骤 5：（如果中途关机）重新 opencode → /start-work 继续
```

### 场景 4：死磕一个顽固 Bug

```
/ralph-loop "修复订单模块的并发超卖 Bug，必须通过单元测试"
```

Agent 会一直工作直到 Bug 修复并且测试通过。

### 场景 5：代码审查

```
review my work
```

自动触发 `review-work` Skill，5 个并行 Agent 同时审查：
- 目标验证
- 代码质量
- 安全审查
- 实际 QA 测试
- 上下文一致性

### 场景 6：项目初始化

```
/init-deep
```

为整个项目生成知识库，后续 Agent 工作时效率更高。

### 场景 7：需要架构咨询

```
Ask @oracle to review our database schema and suggest optimizations
```

Oracle Agent 会以只读模式分析你的架构并给出建议。

### 场景 8：提交代码

```
提交这些改动
```

自动触发 `git-master` Skill：
- 分析最近 30 条 commit 风格
- 按逻辑拆分多个原子提交
- 生成符合项目风格的 commit message

---

## 十三、模型分级体系与手动升级

### 你的模型分级（三平台版）

> 三平台：OpenCode Zen（免费）+ OpenCode Go（付费）+ 智谱 Pro（年费）
> 成本规则：GLM-5.1/GLM-5-Turbo 高峰期（14:00-18:00）3倍、非高峰期2倍（6月底前1倍）；GLM-4.7 固定1倍

| 档位 | 模型 | 平台 | 成本 | 定位 |
|------|------|------|------|------|
| **T1 最强** | GLM-5.1 | 智谱 | ⚠️高峰3倍/非高峰2倍（6月底前1倍） | 最复杂任务，ultrawork |
| **T1.5** | GLM-5-Turbo | 智谱 | ⚠️高峰3倍/非高峰2倍（6月底前1倍） | 审查、规划、高难度 |
| **T2 主力** | GLM-4.7 | 智谱 | 1倍 | **写代码主力**，日常开发 |
| **T2.5** | Qwen 3.6 Plus | Go | Go额度 | 前端/UI/多模态 |
| **T3 降级** | DeepSeek V4 Flash | Go | Go额度 | Free 的付费备选 |
| **T0 免费** | DeepSeek V4 Flash Free | Zen | 免费 | 日常对话、搜索、快速任务 |

### ⚠️ 高峰期成本提醒

| 时间段 | GLM-5.1/GLM-5-Turbo 成本 | 建议 |
|--------|-------------------------|------|
| **14:00-18:00（高峰）** | 3倍消耗 | 避免用 `ulw`，优先 GLM-4.7 和 Free |
| **其他时间（非高峰）** | 2倍消耗（6月底前1倍） | 可适当使用 `ulw` |
| **6月底后 非高峰** | 2倍消耗 | 谨慎使用高阶模型 |

### 重要：Fallback 是平台降级，不是难度升级

**Fallback 只在平台报错（429/500等）时触发**，模型返回了内容（即使内容是错的）不会触发 fallback。

难度升级靠 Sisyphus 编排器路由到不同的 Agent/Category：

```
用户提需求 → Sisyphus (DeepSeek Free，零成本)
  ├─ 简单 CRUD → quick → DeepSeek Free（免费）
  ├─ 前端/UI → visual-engineering → Go Qwen 3.6 Plus
  ├─ 写代码 → unspecified-low → 智谱 GLM-4.7（1倍，主力）
  ├─ 复杂架构 → deep → 智谱 GLM-4.7（1倍）
  └─ 超难问题 → ultrabrain → 智谱 GLM-5.1（⚠️高成本，终极武器）
```

### 手动升级模型的方法

当某个问题反复解决不了时，你有以下方式升级：

#### 方法 1：`ulw` 关键词（⚠️ 高成本，非高峰期使用）

直接在对话框输入包含 `ulw` 或 `ultrawork` 的消息：

```
ulw 这个问题太复杂了，用最强模式帮我解决
```

效果：
- 切换到 **GLM-5.1**（智谱，⚠️高峰期3倍/非高峰期2倍）
- 激活 **ultrawork 编排协议**（并行 Agent、深度探索、自动验证循环）

#### 方法 2：`@plan` 重新规划

```
@plan "这个问题需要重新规划方案"
```

效果：切换到 Prometheus（GLM-5-Turbo，长链路规划优化，⚠️高峰3倍/非高峰2倍），重新规划思路。

#### 方法 3：Tab 切换 Agent

按 Tab 键循环切换到更强大的 Agent：

| Tab 顺序 | Agent | 模型 | 成本 |
|-----------|-------|------|------|
| 1 | Sisyphus | DeepSeek Free | 免费 |
| 2 | **Hephaestus** | **GLM-5.1** | ⚠️高峰3倍 |
| 3 | Prometheus | GLM-5-Turbo | ⚠️3倍/2倍 |
| 4 | Atlas | GLM-4.7 | 1倍 |

#### 方法 4：口头指示 Sisyphus

直接告诉 Sisyphus 用更强的 Category：

```
请用 ultrabrain 级别重新处理这个任务
```
```
这个问题需要 deep 级别来分析
```

#### 所有关键词速查

| 关键词 | 触发方式 | 效果 |
|--------|---------|------|
| `ulw` / `ultrawork` | 消息中包含即可 | GLM-5.1 + 全力编排 |
| `@plan` | `@plan "需求"` | Qwen 3.6 Plus 重新规划 |
| `search` | 消息中包含 | 激活搜索模式 |
| `analyze` | 消息中包含 | 激活深度分析模式 |
| `hyperplan` / `hpp` | 消息中包含 | 对抗性规划 |
| `hyperplan ulw` | 消息中包含 | 对抗性规划 + 全力执行 |

> 注意：关键词在代码块（\`\`\`）或行内代码（\`...\`）中不会触发。不要加 `/` 前缀（如 `/ulw` 不会触发）。

### 实际操作决策树

| 场景 | 操作 | 成本 |
|------|------|------|
| 简单增删改查 | 直接说需求 → quick 类 | 免费 |
| 前端开发 | 直接说需求 → visual-engineering | Go额度 |
| 写代码（日常） | 直接说需求 → unspecified-low | 1倍（GLM-4.7） |
| 写代码搞了 2 轮不行 | 说"用 deep 重新分析" | 1倍（GLM-4.7） |
| 复杂架构问题 | 直接说"ulw 帮我设计" | ⚠️高峰3倍/非高峰2倍 |
| 任何任务反复搞不定 | 输入 `ulw` + 描述 | ⚠️高峰3倍/非高峰2倍 |
| 需要从头规划 | `@plan "重新规划"` | ⚠️GLM-5.1（高成本） |

### 低成本高质量编码策略：GLM-4.7 写代码 + GLM-5-Turbo 审查

**核心思路**：让 GLM-4.7（1倍消耗）写代码，让 GLM-5-Turbo（⚠️高成本）审查代码。审查一次的 token 量远小于写代码的完整迭代，用强模型审查的成本占比很小。

**成本对比**：

| 方案 | 写代码 | 审查 | 总成本 |
|------|--------|------|--------|
| 全程 GLM-5.1 | ⚠️高峰3倍 | - | 很高 |
| **GLM-4.7 写 + GLM-5-Turbo 审** | 1倍 | ⚠️非高峰2倍 | **省 40-60%** |
| 全程 DeepSeek Free | 免费 | 无 | 最低（免费） |

**三种触发审查的方式**：

```
方式 1：写完代码后说
"让 Momus 审查一遍刚才的代码"

方式 2：直接调用
Ask @momus 审查最近的代码变更，关注安全性和逻辑错误

方式 3：/start-work 流程（自动包含审查）
@plan "实现用户管理模块"
→ Prometheus 规划 → Metis 审查计划 → Atlas 执行 → Momus 审查代码
```

**适用场景**：日常开发、小改动、CRUD、前端页面、Bug 修复

**不适用**：复杂架构设计（应该直接用 `deep`/`ultrabrain` 或 `ulw`）

**你当前的配置已就绪**：

| 角色 | Agent | 模型 | 成本 |
|------|-------|------|------|
| 写代码 | Sisyphus-Junior（按 Category） | GLM-4.7（1倍）/ DeepSeek Free（免费） | 主力 |
| 审查代码 | Momus | GLM-5-Turbo | ⚠️3倍/2倍 |
| 审查计划 | Metis | GLM-4.7 | 1倍 |

---

## 十四、常见问题与故障排查

### Q: 启动 opencode 后黑屏？

**原因**：`opencode.json` 中 plugin 写法不对。`"oh-my-openagent@latest"` 会导致黑屏。

**修复**：改为 `"oh-my-openagent"`（不带 `@latest`）。

```json
{
  "plugin": ["oh-my-openagent"]
}
```

### Q: 启动 opencode 后看不到 Agent 切换？

**检查**：
```bash
$env:Path = "$env:USERPROFILE\.bun\bin;$env:Path"
bunx oh-my-openagent doctor
```

确认 `opencode.json` 的 `plugin` 数组中有 `"oh-my-openagent"`（不带 `@latest`）。

### Q: Agent 使用的不是我配置的模型？

检查 `oh-my-openagent.json` 中的 `agents` 配置。运行：
```bash
$env:Path = "$env:USERPROFILE\.bun\bin;$env:Path"
bunx oh-my-openagent doctor --verbose
```

查看模型解析结果。

### Q: 模型报 429 错误（额度用完）？

OmO 会自动切换到 fallback 模型。如果所有平台都限额了，需要等待额度恢复。`cooldown_seconds: 60` 后会自动重试。

### Q: Agent 不停下来？

输入 `/stop-continuation` 强制停止。

### Q: 会话上下文溢出？

OmO 会自动压缩上下文。如果还是不够：
- 输入 `/handoff` 生成交接文档
- 开新会话继续

### Q: 编辑总是失败？

确认 `hashline_edit` 已启用。如果特定文件编辑反复失败，可以在配置中临时关闭：
```json
{ "hashline_edit": false }
```

### Q: 想临时回到原生模式？

编辑 `opencode.json`，把 `plugin` 数组中的 `"oh-my-openagent@latest"` 注释掉或删除，重启 opencode。

---

## 十五、变更与维护

### 更新 OmO 插件

OmO 每次会话启动时会自动检查更新并提示，也可以手动更新：

```powershell
# 1. 备份当前配置
copy "$env:USERPROFILE\.config\opencode\oh-my-openagent.json" "$env:USERPROFILE\.config\opencode\oh-my-openagent.json.bak"

# 2. 更新插件
$env:Path = "$env:USERPROFILE\.bun\bin;$env:Path"
bunx oh-my-openagent@latest install --no-tui

# 3. 检查 opencode.json 中的 plugin 写法
# 确认是 "oh-my-openagent"（不带 @latest），否则会黑屏
```

**更新后必查项**：

| 检查项 | 说明 |
|--------|------|
| `opencode.json` 的 plugin | 必须是 `"oh-my-openagent"`，不能是 `"oh-my-openagent@latest"` |
| `oh-my-openagent.json` | 自定义的 agents/categories 不会被覆盖，放心 |
| 重启后是否黑屏 | 如果黑屏，还原备份：`copy oh-my-openagent.json.bak oh-my-openagent.json`，重启 opencode |

**如果更新后黑屏**：

```powershell
# 还原 opencode.json 的 plugin 条目
# 把 "oh-my-openagent@latest" 改回 "oh-my-openagent"
# 如果还不行，临时删除 plugin 条目恢复原生模式
```

### 取消某个 Coding Plan 订阅

当你不再使用某个 Coding Plan（如阿里云百炼）时，需要两步操作：

#### 第一步：从 opencode.json 删除 Provider

删除对应 provider 的整个配置块（models、options、apiKey）。

#### 第二步：从 oh-my-openagent.json 清理引用

删除所有 `平台名/模型名` 的主模型和 fallback 引用。例如取消百炼后：

```jsonc
// 改前
"sisyphus": {
  "model": "bailian-coding-plan/glm-5",
  "fallback_models": [
    "bailian-coding-plan/qwen3.6-plus",    // ← 删掉
    "opencode-go/qwen3.6-plus",
    "zhipu-coding-plan/glm-5-turbo"
  ]
}

// 改后
"sisyphus": {
  "model": "bailian-coding-plan/glm-5",
  "fallback_models": [
    "opencode-go/qwen3.6-plus",
    "zhipu-coding-plan/glm-5-turbo"
  ]
}
```

如果某个 Agent 的主模型正好在被取消平台上，需要换成其他平台：

```jsonc
// 改前（主模型在百炼）
"atlas": { "model": "bailian-coding-plan/glm-5", ... }

// 改后（换到 opencode-go）
"atlas": { "model": "opencode-go/glm-5", ... }
```

#### 需要改的文件汇总

| 文件 | 改什么 |
|------|--------|
| `opencode.json` | 删除整个 provider 块 |
| `oh-my-openagent.json` | 删除所有该平台的模型引用（主模型 + fallback） |
| 使用手册 | 同步更新模型分配表 |

#### 注意事项

- **不要只删 provider 不改 omo 配置**，否则运行时找不到模型会报错
- **opencode-go 的模型不受影响**，它是独立订阅
- **如果只剩一个平台**，fallback 链会很短或为空，成本控制主要靠手动 `ulw` 升级

### 调整模型编排配置

当你想微调某个 Agent 或 Category 使用的模型时，只需编辑 `oh-my-openagent.json`：

```jsonc
// 示例：把 Sisyphus ultrawork 模型改为 GLM-4.7（降低成本）
"sisyphus": {
  "model": "opencode/deepseek-v4-flash-free",
  "ultrawork": { "model": "zhipu-coding-plan/glm-4.7" },    // 改这里
  "fallback_models": ["opencode-go/deepseek-v4-flash", "zhipu-coding-plan/glm-4.7"]
}
```

**改完即生效**，重启 opencode 即可。不需要重新运行安装命令。

---

## 十六、卸载与回退

### 完整卸载

```powershell
# 1. 从 opencode.json 删除 plugin 条目
# 打开 %USERPROFILE%\.config\opencode\opencode.json
# 删除 "plugin": ["oh-my-openagent"] 这行

# 2. 删除 tui.json
del "%USERPROFILE%\.config\opencode\tui.json"

# 3. 删除 OmO 配置文件
del "%USERPROFILE%\.config\opencode\oh-my-openagent.json" 2>nul

# 4. 验证
opencode --version
# Tab 恢复 Plan/Build 切换，Provider 配置完好无损
```

### 卸载后保留的内容

- ✅ 所有 Provider 配置（智谱、OpenCode Go）
- ✅ MCP 配置（Puppeteer 等）
- ✅ API Key（auth.json）
- ✅ 默认模型设置
- ❌ OmO 生成的计划文件（`.omo/` 目录，可手动删除）

### 重新安装

如果卸载后想重新使用，执行安装 skill 的步骤即可，配置文件会重新生成。

---

## 附录：你的完整模型分配表

> 基于三平台配置：OpenCode Zen（免费）+ OpenCode Go（付费）+ 智谱 Pro（年费）
> 成本规则：GLM-5.1/GLM-5-Turbo 高峰期（14:00-18:00）3倍、非高峰期2倍（6月底前1倍）；GLM-4.7 固定1倍；DeepSeek Free 免费

### 按 Agent

| Agent | 主模型 | 成本 | 平台 | 回退链 |
|-------|--------|------|------|--------|
| Sisyphus（普通） | DeepSeek V4 Flash Free | 免费 | Zen | Go DeepSeek Flash → 智谱 GLM-4.7 |
| Sisyphus（ultrawork） | GLM-5.1 | 3倍/2倍 | 智谱 | 智谱 GLM-5-Turbo → 智谱 GLM-4.7 |
| Hephaestus | GLM-5.1 | 3倍/2倍 | 智谱 | 智谱 GLM-5-Turbo → 智谱 GLM-4.7 |
| Prometheus | GLM-5-Turbo | ⚠️3/2倍 | 智谱 | GLM-4.7 → Free | 长链路规划优化 |
| Atlas | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |
| Momus | GLM-5-Turbo | 3倍/2倍 | 智谱 | 智谱 GLM-4.7 → DeepSeek Free |
| Oracle | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |
| Metis | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |
| Multimodal-Looker | Qwen 3.6 Plus | Go额度 | Go | — |
| Librarian | DeepSeek V4 Flash Free | 免费 | Zen | Go DeepSeek Flash |
| Explore | DeepSeek V4 Flash Free | 免费 | Zen | Go DeepSeek Flash |
| Sisyphus-Junior | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |

### 按 Category

| Category | 主模型 | 成本 | 平台 | 回退 |
|----------|--------|------|------|------|
| visual-engineering | Qwen 3.6 Plus | Go额度 | Go | 智谱 GLM-4.7 → DeepSeek Free |
| ultrabrain | GLM-5.1 | 3倍/2倍 | 智谱 | 智谱 GLM-5-Turbo → 智谱 GLM-4.7 |
| deep | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |
| artistry | Qwen 3.6 Plus | Go额度 | Go | 智谱 GLM-4.7 → DeepSeek Free |
| quick | DeepSeek V4 Flash Free | 免费 | Zen | Go DeepSeek Flash |
| unspecified-low | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |
| unspecified-high | GLM-5-Turbo | 3倍/2倍 | 智谱 | 智谱 GLM-4.7 → DeepSeek Free |
| writing | GLM-4.7 | 1倍 | 智谱 | DeepSeek Free |

### 成本控制提醒

| 时间段 | 策略 |
|--------|------|
| **高峰期 14:00-18:00** | GLM-5.1/GLM-5-Turbo 消耗 3倍额度，避免使用 `ulw`，优先用 GLM-4.7 和 DeepSeek Free |
| **非高峰期 其他时间** | GLM-5.1/GLM-5-Turbo 消耗 2倍额度（6月底前1倍），可适当使用 `ulw` |
| **6月底后 非高峰** | GLM-5.1/GLM-5-Turbo 消耗 2倍，谨慎使用 |
