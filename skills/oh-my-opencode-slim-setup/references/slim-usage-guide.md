# OpenCode + OmO-slim 完整使用手册

> 适用于已集成 oh-my-opencode-slim 插件的 OpenCode 环境
> 基于长期稳定配置：OpenCode Zen（免费）+ 智谱 Coding Plan（付费）
> 成本规则：GLM-5.2 高峰期（14:00-18:00）3倍、非高峰期2倍；GLM-4.7 固定1倍；DeepSeek V4 Flash Free 免费

---

## 目录

- [一、界面与导航](#一界面与导航)
- [二、Agent 体系总览](#二agent-体系总览)
- [三、Primary Agent 详解（Tab 可切换）](#三primary-agent-详解tab-可切换)
- [四、Subagent 详解（Orchestrator 委派）](#四subagent-详解orchestrator-委派)
- [五、四种工作模式](#五种工作模式)
- [六、Orchestrator 编排机制](#六orchestrator-编排机制)
- [七、Preset 预设系统（4 套方案）](#七preset-预设系统4-套方案)
- [八、Council 多模型共识](#八council-多模型共识)
- [九、Skills 技能系统](#九skills-技能系统)
- [十、MCP 服务系统](#十mcp-服务系统)
- [十一、工具系统](#十一工具系统)
- [十二、会话管理](#十二会话管理)
- [十三、常见场景操作指南](#十三常见场景操作指南)
- [十四、模型分级体系与成本控制](#十四模型分级体系与成本控制)
- [十五、常见问题与故障排查](#十五常见问题与故障排查)
- [十六、变更与维护](#十六变更与维护)
- [十七、卸载与回退](#十七卸载与回退)
- [附录：完整模型分配表](#附录完整模型分配表)

---

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
| **Tab** | 切换 Agent（Orchestrator → Build → Council → Plan → 循环，共 4 个） |
| **Enter** | 发送消息 |
| **Ctrl+C** | 中断当前 Agent 操作 |
| **Esc** | 取消当前输入 |
| **Ctrl+D** | 退出 OpenCode |

### 底部输入框

所有操作都通过底部输入框完成。你可以：
- 直接输入自然语言对话
- 输入 `/` 开头的命令（如 `/preset`、`/models`）
- 输入 `@agent` 触发特定 Subagent（如 `@oracle`、`@explorer`）

---

## 二、Agent 体系总览

### 两类 Agent

OmO-slim 的 Agent 分为两类，理解这一点非常重要：

| 类型 | Tab 可切换 | 如何使用 | 数量 |
|------|-----------|---------|------|
| **Primary Agent** | 可以，按 Tab 循环 | 切换到后直接输入 | 4 个 |
| **Subagent（子智能体）** | **不可以** | 由 Orchestrator 自动委派，或用 `@agent` 语法调用 | 6 个 |

### Tab 切换顺序

```
Orchestrator → Build → Council → Plan → （循环）
```

### 完整 Agent 列表

| Agent | 类型 | 模型 | 成本 | 一句话定位 |
|-------|------|------|------|-----------|
| **Orchestrator** | Primary | deepseek-v4-flash-free（默认）| 免费 | 总调度，理解需求并委派 |
| **Build** | Primary | opencode/deepseek-v4-flash-free | 免费 | 直接写代码，不经编排 |
| **Council** | Primary | glm-5-turbo (high) | 中 | 多模型共识，方案对比 |
| **Plan** | Primary | opencode/deepseek-v4-flash-free | 免费 | 先出方案，不写代码 |
| **Explorer** | Subagent | deepseek-v4-flash-free (low) | 免费 | 代码搜索，文件定位 |
| **Librarian** | Subagent | deepseek-v4-flash-free (low) | 免费 | 文档查找，Web 搜索 |
| **Oracle** | Subagent | glm-5.2 (high) | 高 | 深度推理，架构咨询 |
| **Designer** | Subagent | deepseek-v4-flash-free (medium) | 免费 | UI/UX 实现 |
| **Fixer** | Subagent | glm-4.7 (low) | 低 | 范围明确的代码实现 |
| **Observer** | Subagent | **已禁用** | — | 无免费多模态模型可用 |

> **关键理解**：你日常操作的入口是 **Orchestrator**。它是一个调度员，接收你的需求后判断应该自己做还是委派给哪个 Subagent。Subagent 不会出现在 Tab 列表中。

---

## 三、Primary Agent 详解（Tab 可切换）

### Orchestrator（主协调者）— 默认 Agent

**来源**：OmO-slim 插件
**Tab 位置**：第一个（启动后默认）

#### 什么时候用

**90% 的场景**。这是你的默认工作入口。任何开发任务都先跟 Orchestrator 说，它会自动判断：
- 自己能做 → 直接做
- 需要专家 → 委派给对应 Subagent

#### 工作方式

Orchestrator 是调度员，不是苦力。它的工作流程：

```
你输入需求
   │
   ├─ 1. 理解你的意图（实现？修复？重构？调研？）
   │
   ├─ 2. 判断是否需要委派
   │     ├─ 简单任务 → 自己执行
   │     ├─ 需要搜索代码 → 委派 @explorer
   │     ├─ 需要查文档 → 委派 @librarian
   │     ├─ 需要深度思考 → 委派 @oracle
   │     ├─ 需要写 UI → 委派 @designer
   │     └─ 范围明确的实现 → 委派 @fixer
   │
   ├─ 3. 收集 Subagent 返回的结果
   │
   └─ 4. 汇报给你
```

#### 模型与 Preset

Orchestrator 的模型随 Preset 变化，这是成本控制的核心：

| Preset | Orchestrator 模型 | 成本 | 何时用 |
|--------|------------------|------|--------|
| `zen-free`（默认） | deepseek-v4-flash-free | **免费** | 日常开发 |
| `zhipu-std` | glm-4.7 | 低（1倍） | 免费模型委派不准时 |
| `zhipu-fast` | glm-5-turbo | 中 | 需要更快更好的编排 |
| `zhipu-full` | glm-5.2 | 高 | 最强编排质量 |

#### 使用示例

```
"给用户管理模块增加批量导入功能"
"修复登录页面的表单验证 Bug"
"重构这个文件，把重复逻辑提取成公共函数"
"项目里有哪些地方用了过时的 API？"
```

#### 建议的升级路径

```
先用 zen-free 跑几天
   │
   ├─ 委派精准，任务完成好 → 保持 zen-free
   │
   ├─ 偶尔委派失误 → /preset zhipu-std
   │
   ├─ 还不够好 → /preset zhipu-fast
   │
   └─ 需要最强 → /preset zhipu-full
```

---

### Build（构建者）

**来源**：OpenCode 内置
**Tab 位置**：第二个

#### 什么时候用

| 场景 | 适合用 Build |
|------|-------------|
| 任务简单明确，不需要编排 | "改一下这个函数的返回值" |
| 不想让 Orchestrator 做复杂分析 | "直接加个 console.log" |
| Plan 生成方案后，手动执行 | Plan → Build 分阶段工作流 |
| 想要最快的响应 | Build 不做分析，直接动手 |

#### 什么时候不用 Build

| 场景 | 用 Orchestrator 更好 |
|------|---------------------|
| 任务复杂，需要搜索多个文件 | Orchestrator 会委派 Explorer |
| 不确定怎么实现 | Orchestrator 会咨询 Oracle |
| 涉及 UI 和后端同时改 | Orchestrator 会拆分给 Designer + Fixer |

#### 与 Orchestrator 对比

| | Build | Orchestrator |
|--|-------|-------------|
| 工作方式 | 直接执行，不做分析 | 先分析，再委派 Subagent |
| 响应速度 | 快（省去了分析环节） | 稍慢（需要分析+委派） |
| 任务质量 | 依赖你描述的精确度 | 自动判断最佳方案 |
| 编排能力 | 无 | 可委派 6 个 Subagent |
| 适合 | "动手做" | "帮我想清楚再动手做" |

#### 使用示例

```
Tab → Build → "把 src/utils/format.ts 第 23 行的日期格式从 YYYY-MM-DD 改为 DD/MM/YYYY"
Tab → Build → "在 User 类型里加一个 phone 字段，string 类型"
Tab → Build → "按刚才的计划实现第一步"
```

---

### Council（思维的合唱团）

**来源**：OmO-slim 插件
**Tab 位置**：第三个
**模型**：zhipu-coding-plan/glm-5-turbo (high)

#### 什么时候用

**需要多个 AI 模型从不同角度独立分析同一个问题，然后合成最终答案。**

| 适合 | 不适合 |
|------|--------|
| 技术选型纠结 | 简单的是非判断 |
| 架构方案 A vs B | 日常 Bug 修复 |
| 需要高置信度决策 | 时间紧迫的任务 |
| 单个模型回答不确定 | 已经有明确答案的问题 |

#### 工作方式

```
你提出问题
   │
    ├─ alpha (glm-5.2, 智谱) → 从"正确性与边界条件"角度回答
   ├─ beta  (glm-4.7, 智谱) → 从"性能与权衡"角度回答
   └─ gamma (deepseek-free, Zen) → 从"用户体验与实现"角度回答
   │
   └─ Council 合成三个回答 → 最终答案（含一致性分析）
```

#### 使用示例

```
Tab → Council → "这个项目用 Next.js 还是 Nuxt 更合适？"
Tab → Council → "数据库用 PostgreSQL 还是 MongoDB？考虑我们的读写场景"
Tab → Council → "这个认证方案用 JWT 还是 Session？各有什么风险？"
```

> **也可以在 Orchestrator 中调用**：`@council 这两种方案哪个更好？`

#### 成本提醒

Council 每次调用会同时运行 3 个模型，是普通对话的 **3 倍消耗**。请谨慎使用。

---

### Plan（计划者）

**来源**：OpenCode 内置
**Tab 位置**：第四个

#### 什么时候用

**需要先出方案再看，不急着写代码。**

| 适合 | 不适合 |
|------|--------|
| 大型功能开发前 | 紧急 Bug 修复 |
| 需要评审方案再动手 | 简单改动 |
| 团队协作，方案需要审核 | 已经很清楚该怎么做 |

#### 工作方式

```
Tab → Plan → 输入需求
   │
   └─ 生成计划文件保存在 .opencode/plans/ 目录
      （只分析，不改代码）
```

Plan → Build 典型工作流：
```
1. Tab → Plan: "为登录模块增加记住我功能"
   → 生成实施方案（分析现有代码结构、列出改动点）

2. 你审核方案，确认无误

3. Tab → Build: "按计划实现"
   → 按方案写代码
```

#### 使用示例

```
Tab → Plan → "实现用户注册功能，需要后端 API + 前端页面 + 表单验证"
Tab → Plan → "把现有的 REST API 迁移到 GraphQL，制定迁移计划"
Tab → Plan → "分析项目的技术债务，列出优先级排序"
```

> **提示**：Orchestrator 内部已包含计划能力。大多数场景不需要显式用 Plan，只有在需要"先审核方案再动手"时才用。

---

## 四、Subagent 详解（Orchestrator 委派）

以下 6 个 Agent **不会出现在 Tab 切换列表中**。它们有两种使用方式：

1. **自动委派**：Orchestrator 根据任务需要自动判断并委派（推荐）
2. **显式调用**：在 Orchestrator 中使用 `@agent名` 语法手动调用

---

### Explorer（代码搜索者）

**模型**：`opencode/deepseek-v4-flash-free` (low) — **免费**
**角色定位**：快速搜索代码库，定位文件、符号、模式

#### 什么时候用 Explorer

| 适合委派 | 不适合委派 |
|---------|-----------|
| "项目里有哪些文件处理支付？" | 已知具体路径，直接读取 |
| "找到所有使用了 deprecated API 的地方" | 需要理解代码逻辑 |
| "搜索实现了某某接口的类" | 单文件内搜索 |
| "这个函数在哪些地方被调用？" | 需要修改代码 |

#### Orchestrator 自动委派场景

Orchestrator 在以下情况会自动委派给 Explorer：
- 你说"找一下..."、"搜索..."、"看看项目里有没有..."
- 任务涉及未知代码区域，需要先探索
- 需要并行搜索多个模式

#### 手动调用

```
@explorer 找到所有处理用户认证的文件
@explorer 搜索项目中使用了哪些日志框架
@explorer 哪些文件 import 了 moment.js？我想迁移到 dayjs
@explorer 找到所有 TypeScript 的 interface 定义中包含 'User' 的
@explorer 这个项目的路由结构是什么？
```

#### Explorer 的能力边界

- **可以**：Glob（文件名搜索）、Grep（内容搜索）、AST 搜索（代码结构搜索）
- **不可以**：修改文件、深度理解业务逻辑、Web 搜索

---

### Librarian（文档搜索者）

**模型**：`opencode/deepseek-v4-flash-free` (low) — **免费**
**角色定位**：查找外部文档、Web 搜索、API 参考

#### 什么时候用 Librarian

| 适合委派 | 不适合委派 |
|---------|-----------|
| "React 19 有什么新特性？" | 代码库内部搜索 |
| "这个 API 的参数是什么？" | 常识性问题 |
| "查找最新的 Prisma 文档" | 已有稳定的本地文档 |
| "这个错误码是什么意思？" | 需要修改代码 |

#### Orchestrator 自动委派场景

Orchestrator 在以下情况会自动委派给 Librarian：
- 涉及第三方库的 API 用法
- 需要查找最新版本的文档
- 你的问题中提到了具体的库名或框架名

#### 手动调用

```
@librarian Next.js 15 的 App Router 有什么新特性？
@librarian Prisma 的 $transaction 用法是什么？
@librarian TypeScript 5.7 的 satisfies 操作符怎么用？
@librarian 查一下 Tailwind CSS v4 的安装方法
@librarian 这个 npm 包的最新版本是多少？
```

#### Librarian vs Explorer 的区别

| | Explorer | Librarian |
|--|---------|-----------|
| 搜索范围 | 你的代码库内部 | 外部文档和互联网 |
| 典型问题 | "我的项目里..." | "这个库的文档说..." |
| 工具 | Glob, Grep, AST | Web Search, Web Fetch |
| MCP | 无 | websearch, grep_app |

---

### Oracle（深度推理者）

**模型**：`zhipu-coding-plan/glm-5.2` (high) — **高成本（高峰3倍/非高峰2倍）**
**角色定位**：深度架构推理、复杂调试、代码审查、高风险决策

#### 什么时候用 Oracle

| 适合委派 | 不适合委派 |
|---------|-----------|
| "这个架构设计有什么风险？" | 简单的 Bug 修复 |
| "这个 Bug 反复出现，帮我分析根因" | 首次尝试的简单问题 |
| "审查这个重构方案" | 低风险改动 |
| "这两个数据库设计哪个更好？" | 明确的实现任务 |
| "这个性能瓶颈怎么优化？" | 快速原型 |

#### Orchestrator 自动委派场景

Orchestrator 在以下情况会自动委派给 Oracle：
- 同一个问题已经失败 2 次以上（需要深度分析）
- 涉及架构级别的改动
- 安全相关的决策
- 代码审查和简化（Oracle 有 `simplify` skill）

#### 手动调用

```
@oracle 这个数据库 schema 应该如何优化？考虑高并发场景
@oracle 帮我审查这个重构方案的潜在风险
@oracle 这个 Bug 反复出现，帮我深入分析根本原因
@oracle 这段代码有什么安全隐患？
@oracle 简化这个函数，保持行为不变  ← 触发 simplify skill
@oracle 我们应该用微服务还是单体？分析利弊
```

#### 成本提醒

Oracle 使用 glm-5.2 (high) 是成本最高的 Subagent。高峰期（14:00-18:00）消耗 3 倍额度。
- 不要用 Oracle 做简单的事情（"加个字段"、"改个变量名"）
- 复杂的架构决策、反复出现的 Bug、代码审查才值得用 Oracle

---

### Designer（UI 实现者）

**模型**：`opencode/deepseek-v4-flash-free` (medium) — **免费**
**角色定位**：UI/UX 实现、前端开发、界面打磨

#### 什么时候用 Designer

| 适合委派 | 不适合委派 |
|---------|-----------|
| "做一个登录页面" | 后端逻辑开发 |
| "优化这个组件的交互" | 数据库操作 |
| "这个页面需要响应式布局" | API 开发 |
| "加个动画效果" | 算法实现 |

#### Orchestrator 自动委派场景

Orchestrator 在以下情况会自动委派给 Designer：
- 你的需求涉及 UI/UX
- 提到了"页面"、"组件"、"样式"、"布局"、"动画"等关键词
- 前端相关的实现工作

#### 手动调用

```
@designer 做一个漂亮的登录页面，包含表单验证和 loading 状态
@designer 优化这个按钮的交互动画
@designer 把这个页面改成响应式布局
@designer 实现一个可复用的 Modal 组件
@designer 这个表格在移动端显示不好，优化一下
```

#### 成本说明

Designer 使用免费的 deepseek-v4-flash-free (medium variant)。UI 实现对模型要求不是极高，免费模型配合 medium variant 的引导足够完成大多数 UI 任务。

---

### Fixer（代码实现者）

**模型**：`zhipu-coding-plan/glm-4.7` (low) — **低成本（1倍）**
**角色定位**：范围明确的代码实现、快速编码、测试编写

#### 什么时候用 Fixer

| 适合委派 | 不适合委派 |
|---------|-----------|
| "写一个单元测试" | 需要先调研的未知任务 |
| "实现这个函数"（需求明确） | 需要架构决策 |
| "改一下这个文件的类型定义" | 跨多个模块的重构 |
| "按照这个方案实现第1步" | 需求不明确 |

#### Orchestrator 自动委派场景

Orchestrator 在以下情况会自动委派给 Fixer：
- 任务范围明确，不需要研究
- 写测试
- 多文件并行修改（Fixer 可以同时改多个文件）
- 简单的实现工作

#### 手动调用

```
@fixer 给 src/utils/format.ts 的 formatDate 函数写单元测试
@fixer 把这个函数的返回类型从 string 改成 { date: string; time: string }
@fixer 在 User 类型里加一个 phone 字段，并更新所有引用
@fixer 按照上面的方案实现代码
```

#### 为什么 Fixer 用 glm-4.7

Fixer 做的是"明确的编码工作"，不需要深度推理。glm-4.7 代码能力强且成本固定 1 倍，是日常编码的最佳选择。

---

### Observer（视觉分析者）— 当前已禁用

**状态**：**已禁用**
**原因**：当前没有免费的多模态模型可用

#### 原本的能力

- 图片/PDF 分析
- 截图解读
- 结构化视觉信息提取

#### 如果未来需要启用

当有多模态模型可用时，修改配置：
```jsonc
{
  "disabled_agents": [],  // 清空禁用列表
  "presets": {
    "zen-free": {
      "observer": { "model": "opencode/kimi-k2.5" }  // 需要支持视觉的模型
    }
  }
}
```

---

## 五、四种工作模式

### 模式一：Orchestrator 自动编排（推荐，90% 场景）

**操作**：直接在 Orchestrator 中输入需求，不做任何特殊操作。

```
"把登录接口的超时时间从 30 秒改为 60 秒"
"给这个组件加一个 loading 状态"
"实现用户注册功能，包含后端 API 和前端页面"
```

**幕后发生了什么**：
```
Orchestrator 收到需求
   │
   ├─ "改超时时间" → 简单任务，自己直接改
   │
   ├─ "实现注册功能" → 复杂任务
   │   ├─ @explorer → 搜索现有的注册相关代码
   │   ├─ @librarian → 查注册 API 最佳实践
   │   ├─ @fixer → 实现后端 API
   │   └─ @designer → 实现前端页面
   │
   └─ 汇总结果，汇报给你
```

### 模式二：显式委派（精确控制）

**操作**：在 Orchestrator 中使用 `@agent` 语法指定用哪个 Subagent。

```
@oracle 这个架构设计有什么风险？
@explorer 找到所有 API 路由定义
@librarian React 19 的最新文档
@designer 优化这个页面的交互
@fixer 写一个测试
```

**什么时候用**：
- 你明确知道该用哪个专家
- Orchestrator 自动委派的结果不满意，想手动指定
- 想节省 Orchestrator 的分析开销，直接让专家处理

### 模式三：Plan → Build 分阶段

**操作**：先用 Plan 出方案，再用 Build 执行。

```
Step 1: Tab → Plan → "为登录模块增加记住我功能，生成实施方案"
Step 2: 审核方案
Step 3: Tab → Build → "按计划实现"
```

**什么时候用**：
- 大型功能，需要先审核方案再动手
- 团队协作，方案需要其他人确认
- 不确定实现思路，想先看 AI 怎么规划

### 模式四：Council 多模型决策

**操作**：切换到 Council 或在 Orchestrator 中调用。

```
Tab → Council → "这个项目用 Next.js 还是 Nuxt？"
```

或：

```
@council REST 和 GraphQL 哪个更适合我们？
```

**什么时候用**：
- 技术选型纠结
- 需要从多个角度验证方案
- 单个模型的回答不够自信

---

## 六、Orchestrator 编排机制

### 委派规则

Orchestrator 内置了以下委派规则，它会根据任务特征自动判断：

| Subagent | 委派时机 | 不委派时机 |
|----------|---------|-----------|
| @explorer | 需要发现未知内容、并行搜索 | 已知路径，直接读取 |
| @librarian | 库 API 变化频繁、需要最新文档 | 简单稳定的 API |
| @oracle | 高风险决策、反复失败（2次+）、安全审查 | 简单修复、首次尝试 |
| @designer | 用户界面、响应式布局、动画 | 后端/逻辑工作 |
| @fixer | 范围明确的实现、测试编写、多文件修改 | 需要研究/决策 |
| @council | 需要多模型判断（高成本，需手动调用） | 简单任务 |

### 并行委派

Orchestrator 可以同时开多个 Subagent 并行工作：

```
你："实现用户管理模块，同时调研竞品的权限系统"

Orchestrator 会同时：
   ├─ 自己：分析现有代码结构
   ├─ @explorer：搜索项目中已有的用户相关代码
   ├─ @librarian：调研权限系统最佳实践
   └─ @fixer：实现用户 CRUD API
```

### 验证路由

Orchestrator 在任务完成前的验证阶段也会使用 Subagent：

| 验证类型 | 路由到 |
|---------|--------|
| UI/UX 验证 | @designer |
| 代码审查、简化 | @oracle |
| 测试编写 | @fixer |
| 多媒体分析 | @observer（如启用） |

---

## 七、Preset 预设系统（4 套方案）

### 设计思路

4 套 Preset **只有 Orchestrator 的模型不同**，其余 Subagent 所有 Preset 都一样。这是因为：
- Orchestrator 是消耗 token 的入口点，模型越强成本越高
- Subagent 的模型已经按"免费做杂活、1倍做主力、高阶做重活"原则固定

### 4 套 Preset 对比

| | zen-free（默认） | zhipu-std | zhipu-fast | zhipu-full |
|--|-----------------|-----------|------------|------------|
| **Orchestrator** | deepseek-free | glm-4.7 | glm-5-turbo | glm-5.2 |
| **Orchestrator 成本** | **免费** | 低（1倍） | 中 | 高（3倍/2倍） |
| **其他 Agent** | 全部相同 | 全部相同 | 全部相同 | 全部相同 |

各 Preset 下所有 Agent 的完整模型分配：

| Agent | zen-free | zhipu-std | zhipu-fast | zhipu-full |
|-------|----------|-----------|------------|------------|
| Orchestrator | `opencode/deepseek-v4-flash-free` | `zhipu/glm-4.7` | `zhipu/glm-5-turbo` | `zhipu/glm-5.2` |
| Explorer | `opencode/deepseek-v4-flash-free` (low) | 同左 | 同左 | 同左 |
| Librarian | `opencode/deepseek-v4-flash-free` (low) | 同左 | 同左 | 同左 |
| Oracle | `zhipu/glm-5.2` (high) | 同左 | 同左 | 同左 |
| Designer | `opencode/deepseek-v4-flash-free` (medium) | 同左 | 同左 | 同左 |
| Fixer | `zhipu/glm-4.7` (low) | 同左 | 同左 | 同左 |
| Council | `zhipu/glm-5-turbo` (high) | 同左 | 同左 | 同左 |

### 如何切换

```
/preset                # 列出所有可用预设
/preset zen-free       # 切换到免费编排
/preset zhipu-std      # 切换到标准编排
/preset zhipu-fast     # 切换到快速编排
/preset zhipu-full     # 切换到最强编排
```

### 切换持久化

| 方法 | 持久化 | 说明 |
|------|--------|------|
| 编辑配置文件 `"preset": "zen-free"` | 跨重启 | 永久生效 |
| `/preset zen-free` 命令 | 仅当前会话 | 重启后恢复配置文件设置 |

### 推荐的升级节奏

```
第 1-2 周：用 zen-free，观察 Orchestrator 的委派质量
    │
    ├─ 委派精准 → 长期使用 zen-free，免费！
    │
    ├─ 偶尔失误 → 升级到 zhipu-std（1倍成本）
    │
    ├─ 经常失误 → 升级到 zhipu-fast（中等成本）
    │
    └─ 要求最高 → 升级到 zhipu-full（最强但最贵）
```

---

## 八、Council 多模型共识

### 概念

Council 是一个多模型共识系统：
1. 并行运行 3 个模型（Councillors）
2. 每个 Councillor 从不同角度独立回答
3. Council Agent 合成最终答案

### 当前配置

| 议员 | 模型 | 平台 | 视角 |
|------|------|------|------|
| alpha | `zhipu-coding-plan/glm-5.2` | 智谱 | "Focus on correctness and edge cases." |
| beta | `zhipu-coding-plan/glm-4.7` | 智谱 | "Focus on performance and trade-offs." |
| gamma | `opencode/deepseek-v4-flash-free` | Zen | "Focus on user experience and implementation." |

### 使用方式

**方式一**：Tab 切换到 Council，直接输入
```
Tab → Council → "这两个方案哪个更好？"
```

**方式二**：在 Orchestrator 中调用
```
@council 对比 REST 和 GraphQL 的优劣
```

### 典型使用场景

```
@council 这个项目应该用 monorepo 还是多仓库？
@council 数据库选 PostgreSQL 还是 MongoDB？
@council 用 JWT 还是 Session 做认证？
@council 前端用 Next.js 还是 Vite + React？
@council 这个性能优化方案 A 和方案 B 哪个更好？
```

### 输出格式

Council 响应包含：
1. **Council Response** — 合成的最终答案
2. **Councillor Details** — 每个模型的独立回答
3. **Council Summary** — 一致性分析、置信度

### 成本提醒

- 每次调用 Council = 3 个模型同时运行
- alpha 用 glm-5.2（高成本），beta 用 glm-4.7（低成本），gamma 用 deepseek-free（免费）
- **综合成本约等于 1 次高阶调用**，但获得 3 个视角
- Orchestrator 不会自动调用 Council，必须手动触发

---

## 九、Skills 技能系统

### 内置 Skills

| Skill | 描述 | 默认分配给 |
|-------|------|-----------|
| `simplify` | 代码简化，保持行为不变 | `oracle` |
| `codemap` | 代码库映射生成 | `orchestrator` |
| `clonedeps` | 依赖源码克隆 | `orchestrator` |

### Skills 分配规则

```
orchestrator → ["*"]（所有 Skills）
oracle       → ["simplify"]（仅简化代码）
其他 Agent   → []（无 Skills）
```

### 如何触发

你不需要手动调用 Skill，Agent 会根据任务自动加载：

```
你："简化这段代码"        → oracle 自动加载 simplify
你："生成代码地图"        → orchestrator 自动加载 codemap
你："克隆 lodash 的源码"  → orchestrator 自动加载 clonedeps
```

---

## 十、MCP 服务系统

### 内置 MCP

| MCP | 描述 | 分配 |
|-----|------|------|
| `websearch` | Web 搜索 | librarian |
| `grep_app` | 在线代码搜索 | librarian |
| `context7` | 文档搜索 | 未分配（已排除） |

### MCP 分配规则

```
orchestrator → ["*", "!context7"]（所有 MCP，排除 context7）
librarian    → ["websearch", "grep_app"]（搜索相关）
其他 Agent   → []（无 MCP）
```

---

## 十一、工具系统

### 代码导航工具（LSP）

| 工具 | 功能 |
|------|------|
| `lsp_goto_definition` | 跳转到定义 |
| `lsp_find_references` | 查找所有引用 |
| `lsp_rename` | 跨工作区重命名 |
| `lsp_diagnostics` | 获取错误/警告 |
| `lsp_symbols` | 文件大纲 |

### 代码搜索工具

| 工具 | 功能 |
|------|------|
| `grep` | 正则内容搜索 |
| `glob` | 文件名模式匹配 |
| `ast_grep_search` | AST 感知搜索 |
| `ast_grep_replace` | AST 感知替换 |

### 委派工具

| 工具 | 功能 |
|------|------|
| `task` | 委派任务给 Subagent |
| `subtask` | 运行子任务 |
| `handoff` | 任务交接 |

### 其他工具

| 工具 | 功能 |
|------|------|
| `webfetch` | 获取网页内容 |
| `bash` | 执行 Shell 命令 |
| `read` / `edit` / `write` | 文件读写 |

---

## 十二、会话管理

### 会话持久化

OmO-slim 会记住最近的子 Agent 会话，方便复用：

- 每个 Agent 最多记住 2 个最近会话
- 可使用短别名恢复会话

### 配置

```jsonc
{
  "sessionManager": {
    "maxSessionsPerAgent": 2,
    "readContextMinLines": 10,
    "readContextMaxFiles": 8
  }
}
```

---

## 十三、常见场景操作指南

### 场景 1：快速修个 Bug

```
Orchestrator → "修复 src/utils/format.ts 里的日期格式化 Bug，输入 undefined 时会崩溃"
```

Orchestrator 自动判断：简单修复 → 自己处理 或 委派 @fixer

### 场景 2：开发一个新功能

```
Orchestrator → "实现用户注册功能，包含后端 API、前端注册页面、表单验证"
```

Orchestrator 自动拆解并委派：
- @explorer → 搜索现有注册相关代码
- @fixer → 实现后端 API
- @designer → 实现前端注册页面

### 场景 3：复杂 Bug 反复出现

```
@oracle 这个空指针异常反复出现，帮我深入分析根本原因
```

Oracle 会用 glm-5.2 (high) 深度分析。

### 场景 4：技术选型纠结

```
Tab → Council → "项目用 Next.js 还是 Nuxt？"
```

3 个模型从不同角度分析，合成最终建议。

### 场景 5：大型功能先出方案

```
Tab → Plan → "实现支付系统，支持支付宝和微信"
→ 审核方案
Tab → Build → "按计划实现"
```

### 场景 6：查找最新文档

```
@librarian Prisma 5 的 $transaction 有什么变化？
```

### 场景 7：代码库探索

```
@explorer 找到所有处理支付逻辑的文件
```

### 场景 8：简化复杂代码

```
@oracle 简化 src/services/payment.ts，保持行为不变
```

Oracle 自动加载 `simplify` skill。

### 场景 9：切换 Preset（Orchestrator 不给力时）

```
/preset              # 查看当前预设
/preset zhipu-std    # 升级 Orchestrator 到 glm-4.7
```

### 场景 10：不想等编排，直接干活

```
Tab → Build → "在 User 类型里加个 phone 字段"
```

跳过分析，直接执行。

---

## 十四、模型分级体系与成本控制

### 你的模型分级

| 档位 | 模型 | 平台 | 成本 | 分配给 |
|------|------|------|------|--------|
| **T0 免费** | DeepSeek V4 Flash Free | Zen | **免费** | Explorer, Librarian, Designer, Orchestrator（默认） |
| **T1 低成本** | GLM-4.7 | 智谱 | 1倍 | Fixer, Orchestrator（zhipu-std） |
| **T2 中等** | GLM-5-Turbo | 智谱 | 中 | Council, Orchestrator（zhipu-fast） |
| **T3 高阶** | GLM-5.2 | 智谱 | ⚠️高峰3倍/非高峰2倍 | Oracle, Orchestrator（zhipu-full） |

### 成本分配原则

```
免费做杂活：Explorer（搜索）、Librarian（查档）、Designer（UI）
1倍做主力：Fixer（日常写代码）
高阶做重活：Oracle（深度推理）— 只有高难度任务才用
按需升编排：Orchestrator 从免费开始，不行再升级
```

### 高峰期成本提醒

| 时间段 | GLM-5.2 成本 | 建议 |
|--------|-------------|------|
| **14:00-18:00（高峰）** | 3倍消耗 | 避免大量 Oracle 任务，Orchestrator 用 zen-free |
| **其他时间（非高峰）** | 2倍消耗 | 可适当使用 Oracle |

### 手动升级 Orchestrator

```
/preset zen-free    # 免费（默认）
/preset zhipu-std   # 1倍
/preset zhipu-fast  # 中等
/preset zhipu-full  # 最强
```

---

## 十五、常见问题与故障排查

### Q: 启动 opencode 后看不到 Agent 切换？

按 Tab 应能看到 Orchestrator / Build / Council / Plan 共 4 个 Agent（Subagent 不会出现在 Tab 中）。

```bash
bunx oh-my-opencode-slim@latest doctor
```

确认 `opencode.json` 的 `plugin` 数组中有 `"oh-my-opencode-slim"`。

### Q: Agent 使用的不是我配置的模型？

检查 `oh-my-opencode-slim.json` 中的 `preset` 和 `presets` 字段。

### Q: Council 报错？

检查：
1. `council.presets` 是否配置
2. 至少有一个 preset
3. Councillor 模型是否存在（用 `opencode models` 确认）

### Q: Orchestrator 委派不准？

尝试升级 Preset：
```
/preset zhipu-std    # 免费模型 → glm-4.7
/preset zhipu-fast   # glm-4.7 → glm-5-turbo
/preset zhipu-full   # glm-5-turbo → glm-5.2
```

### Q: 模型报错？

检查 Provider 认证状态：
```bash
opencode auth status
```

### Q: 想用 Observer 分析图片？

当前 Observer 已禁用（无免费多模态模型）。等有多模态模型可用时修改 `disabled_agents: []` 并配置模型。

---

## 十六、变更与维护

### 更新 OmO-slim 插件

```bash
bunx oh-my-opencode-slim@latest install --no-tui --skills=yes
```

更新后检查：
- `opencode.json` 的 plugin 写法是否正确
- 配置文件是否需要更新

### 调整模型编排

编辑 `oh-my-opencode-slim.json`：
- 修改当前 Preset：`"preset": "zen-free"`
- 修改 Agent 模型：在对应 preset 中改 `"model"` 字段
- 添加新 Preset：在 `"presets"` 中加新 key

### 切换配置文件位置

| 系统 | 路径 |
|------|------|
| Windows | `%USERPROFILE%\.config\opencode\oh-my-opencode-slim.json` |
| Mac/Linux | `~/.config/opencode/oh-my-opencode-slim.json` |

---

## 十七、卸载与回退

详见 [uninstall-guide.md](uninstall-guide.md)

简要步骤：
1. 从 `opencode.json` 移除 `"oh-my-opencode-slim"`
2. 删除 `oh-my-opencode-slim.json`
3. 验证 Tab 切换恢复为只有 Build / Plan 等 OpenCode 内置 Agent

---

## 附录：完整模型分配表

### Tab 可切换的 Primary Agent

| Agent | 默认模型 | 可切换 Preset | 成本 |
|-------|---------|-------------|------|
| Orchestrator | opencode/deepseek-v4-flash-free | zen-free / zhipu-std / zhipu-fast / zhipu-full | 免费 ~ 高 |
| Build | opencode/deepseek-v4-flash-free | 不受 Preset 影响 | 免费 |
| Council | zhipu-coding-plan/glm-5-turbo (high) | 所有 Preset 相同 | 中 |
| Plan | opencode/deepseek-v4-flash-free | 不受 Preset 影响 | 免费 |

### Orchestrator 委派的 Subagent（所有 Preset 通用）

| Agent | 模型 | 成本 | 平台 |
|-------|------|------|------|
| Explorer | opencode/deepseek-v4-flash-free (low) | **免费** | Zen |
| Librarian | opencode/deepseek-v4-flash-free (low) | **免费** | Zen |
| Designer | opencode/deepseek-v4-flash-free (medium) | **免费** | Zen |
| Oracle | zhipu-coding-plan/glm-5.2 (high) | 高（3倍/2倍） | 智谱 |
| Fixer | zhipu-coding-plan/glm-4.7 (low) | 低（1倍） | 智谱 |
| Observer | 已禁用 | — | — |

### Council 议员

| 议员 | 模型 | 平台 | 视角 |
|------|------|------|------|
| alpha | zhipu-coding-plan/glm-5.2 | 智谱 | 正确性与边界条件 |
| beta | zhipu-coding-plan/glm-4.7 | 智谱 | 性能与权衡 |
| gamma | opencode/deepseek-v4-flash-free | Zen | 用户体验与实现 |

### 成本控制速查

| 时间段 | 策略 |
|--------|------|
| **高峰期 14:00-18:00** | Orchestrator 用 zen-free，避免大量 @oracle 调用 |
| **非高峰期 其他时间** | 可用 /preset zhipu-fast 临时升级，Oracle 2倍消耗 |
