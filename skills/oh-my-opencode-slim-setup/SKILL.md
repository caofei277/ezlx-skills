---
name: oh-my-opencode-slim-setup
description: 安装配置 oh-my-opencode-slim 插件，实现多智能体自动编排。支持 OpenCode Zen 免费 + 智谱 Coding Plan 双平台编排，内置 4 套 Preset 逐级升级、Council 多模型共识、Skills 技能系统。
metadata:
  display_name: OmO-slim 多智能体编排插件
  version: "1"
  compatibility:
    - filesystem
    - nodejs
    - npm
---

# OmO-slim 多智能体编排插件安装配置

## 何时使用

- 用户希望 AI Agent 自动按任务类型分配不同模型（Oracle 用 GLM-5.1 高阶推理、Explorer 用 DeepSeek Free 快速浏览）
- 用户已配置智谱 Coding Plan Provider，并使用 OpenCode Zen 免费模型
- 用户想使用 Council 功能（多模型并行讨论、合成共识答案）
- 用户想尝试 oh-my-opencode-slim 但不确定是否适合，希望可以无损回退
- 用户关心成本控制，需要高峰期避免高阶模型消耗过多的策略

## 不适用

- OpenCode 本身的安装或 Provider 配置（使用 `opencode-cross-platform-setup` skill）
- OpenCode 版本更新（使用 `opencode-update` skill）
- OmO-slim 插件的二次开发或源码调试
- V2 后台编排 Beta 的深度调试（参见 slim-v2-beta.md）

## 前置条件

- OpenCode v1.0.150+ 已安装
- 至少有智谱 Coding Plan 或 OpenCode Zen 免费模型可用
- bun 已安装（仅安装时需要，CLI 本身有独立二进制）。若未安装可用 `npm install -g bun`

检查命令：

```bash
opencode --version
bun --version
```

## 输入

- 用户当前已有的 Provider 列表（agent 自动从 `opencode.json` 读取）
- 用户对各平台额度情况的描述（哪些模型用得多、哪些是备用）

## 输出

- OmO-slim 插件已注册到 `opencode.json`
- `oh-my-opencode-slim.jsonc` 配置文件已生成（按用户 Provider 分配 Agent 模型）
- 包含 Preset 预设系统（运行时 `/preset` 命令切换）
- 包含 Council 多模型共识配置
- 验证通过：`ping all agents` 正常

## 约束

- **无损**：安装和卸载过程不得修改用户已有的 Provider 配置（`opencode.json` 的 `provider` 字段）
- **可逆**：卸载后 OpenCode 恢复到安装前的状态，Agent 切换恢复正常
- **安全**：API Key 不得明文写入新文件
- **幂等**：重复执行不破坏已有配置

> **Agent 架构说明**：OmO-slim 的 Agent 分为两类。**Primary Agent**（Orchestrator、Council）可通过 Tab 切换，与 OpenCode 内置的 Build、Plan 一起构成 Tab 循环：`Orchestrator → Build → Council → Plan`。**Subagent**（Explorer、Oracle、Librarian、Designer、Fixer、Observer）不会出现在 Tab 列表中，只能由 Orchestrator 自动委派或通过 `@agent` 语法调用。

## 智能体分级策略

OmO-slim 采用分级智能体策略，免费做杂活、1倍做主力、高阶做重活：

| 级别 | Agent | 类型 | 模型 | 平台 | 成本 | 适用场景 |
|------|-------|------|------|------|------|---------|
| T0 免费 | Explorer, Librarian, Designer | Subagent | deepseek-v4-flash-free | Zen | **免费** | 搜索、查档、UI |
| T1 主力 | Fixer | Subagent | glm-4.7 (low) | 智谱 | 1倍 | 日常写代码 |
| T2 高阶 | Oracle | Subagent | glm-5.1 (high) | 智谱 | ⚠️3倍/2倍 | 深度推理 |
| T3 共识 | Council | Primary | glm-5-turbo (high) | 智谱 | 中 | 多模型共识 |
| T0~T3 | Orchestrator | Primary | 按Preset切换 | Zen/智谱 | 免费~高 | 主编排 |

**Orchestrator 逐级升级 Preset**：

| Preset | Orchestrator 模型 | 成本 | 何时用 |
|--------|------------------|------|--------|
| zen-free（默认） | deepseek-v4-flash-free | **免费** | 先试试免费编排 |
| zhipu-std | glm-4.7 | 低（1倍） | 免费委派不准时 |
| zhipu-fast | glm-5-turbo | 中 | 需要更快更好 |
| zhipu-full | glm-5.1 | 高 | 要求最高 |

**核心原则**：
- **免费做杂活**：Explorer/Librarian/Designer 用 deepseek-free，零成本
- **1倍做主力**：Fixer 用 glm-4.7 写日常代码
- **高阶做重活**：Oracle 用 glm-5.1 只在深度推理时用
- **按需升编排**：Orchestrator 从免费开始，/preset 一键升级
- **Observer 已禁用**：无免费多模态模型，等有可用模型再启用
- **Council 慎用**：多模型并行消耗高，需通过 Tab 切换到 Council 或 `@council` 调用

## 主流程

### 步骤 1：检测现有环境

```bash
opencode --version
bun --version
```

读取用户配置文件，确认已有 Provider：

| 平台 | Windows 路径 | Mac/Linux 路径 |
|------|-------------|----------------|
| 配置文件 | `%USERPROFILE%\.config\opencode\opencode.json` | `~/.config/opencode/opencode.json` |

从配置文件中提取 `provider` 对象的 key 列表，确认用户有哪些平台可用。

常见 Provider 前缀映射：

| opencode.json 中的 provider key | OmO-slim 中使用的前缀 |
|------|------|
| （OpenCode Zen 内置，无需配置） | `opencode/` |
| `zhipu-coding-plan` | `zhipu-coding-plan/` |

> OpenCode Zen 提供 **免费** 的 DeepSeek V4 Flash Free，provider 前缀为 `opencode/`。无需额外配置，OpenCode 安装即可使用。
>
> **智谱成本提醒**：GLM-5.1 高峰期（14:00-18:00 UTC+8）消耗 3 倍额度，非高峰期消耗 2 倍。GLM-4.7 固定 1 倍消耗。Orchestrator 默认用免费模型，按需升级。

**判据**：已确认 OpenCode 版本、bun 版本、用户已有的 Provider 列表。

### 步骤 2：安装 OmO-slim

**V1 稳定版安装**：

```bash
bunx oh-my-opencode-slim@latest install --no-tui --skills=yes --preset=opencode-go
```

> 如果用户只有 OpenCode Go，使用上面这条命令。如果用户还有智谱 Pro，安装后编辑配置文件即可。

安装参数说明：

| 参数 | 说明 |
|------|------|
| `--skills=yes` | 安装捆绑 Skills（simplify, codemap, clonedeps） |
| `--preset=opencode-go` | 使用 opencode-go 预设（推荐） |
| `--preset=openai` | 使用 OpenAI 预设（需 OpenAI API） |
| `--no-tui` | 非交互模式 |
| `--reset` | 强制覆盖已有配置 |

**V2 Beta 版安装**（可选）：

```bash
bunx oh-my-opencode-slim@beta install --no-tui --skills=yes
OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS=1 opencode
```

> V2 后台编排特性：Orchestrator 作为调度器，专家 Agent 在后台运行。详见 [references/slim-v2-beta.md](references/slim-v2-beta.md)。

安装完成后，`opencode.json` 的 `plugin` 数组中会新增 `"oh-my-opencode-slim"`。

验证安装：

```bash
bunx oh-my-opencode-slim@latest doctor
```

**判据**：`plugin` 数组包含 `"oh-my-opencode-slim"`，doctor 检查无严重错误。

### 步骤 3：生成 OmO-slim 配置文件

根据步骤 1 检测到的 Provider 列表，在用户配置目录生成 `oh-my-opencode-slim.jsonc`：

| 平台 | 配置文件路径 |
|------|-------------|
| Windows | `%USERPROFILE%\.config\opencode\oh-my-opencode-slim.jsonc` |
| Mac/Linux | `~/.config/opencode/oh-my-opencode-slim.jsonc` |

配置文件内容根据用户的 Provider 组合生成，详见：
- 三平台配置模板 → [references/slim-config-templates.md](references/slim-config-templates.md)

关键规则：
- 生成 4 套 Preset（zen-free / zhipu-std / zhipu-fast / zhipu-full），只有 Orchestrator 模型不同
- Explorer/Librarian/Designer 用免费模型（deepseek-v4-flash-free）
- Oracle 用高阶模型（glm-5.1, variant: high）
- Fixer 用主力模型（glm-4.7, variant: low）
- Council 用快速模型（glm-5-turbo, variant: high）
- Observer 默认禁用（`disabled_agents: ["observer"]`）

**判据**：配置文件已写入，JSONC 格式合法。

### 步骤 4：验证

```bash
bunx oh-my-opencode-slim@latest doctor --verbose
```

确认模型解析正确，无报错。

启动 OpenCode 验证：

```bash
opencode
```

在 TUI 中：
1. 按 Tab 确认可看到 Orchestrator → Build → Council → Plan 共 4 个 Agent（Subagent 不会出现在 Tab 中）
2. 输入 `ping all agents` 确认所有 Agent 正常响应

**判据**：Tab 可切换 Agent，ping all agents 正常响应。

### 步骤 5：向用户说明

1. **使用方式**：
   - 直接对话：和原来一样，Orchestrator 会自动判断并委派
   - 调用专家：`@oracle "架构问题"`、`@librarian "查文档"`、`@council "对比方案"`
   - 切换预设：`/preset` 列出预设，`/preset <name>` 切换
   - **高峰期（14:00-18:00）避免让 Oracle/Council 处理大量任务**

2. **Agent 说明**（Tab 切换只有 4 个 Agent，其他为 Subagent）：

   **Tab 可切换（Primary）**：
   | Agent | 来源 | 何时使用 |
   |-------|------|---------|
   | Orchestrator | OmO-slim | 日常开发、自动编排（默认） |
   | Build | OpenCode 内置（opencode/deepseek-v4-flash-free） | 直接写代码，不经编排 |
   | Council | OmO-slim | 多模型讨论、方案对比（高成本） |
   | Plan | OpenCode 内置（opencode/deepseek-v4-flash-free） | 先制定实施方案 |

    **Orchestrator 委派（Subagent，不通过 Tab）**：
    | Agent | 何时使用 | 成本 |
    |-------|---------|------|
    | Explorer | 快速浏览代码库 | **免费** |
    | Librarian | 查最新文档/Web | **免费** |
    | Oracle | 架构咨询、复杂调试 | ⚠️高阶 |
    | Designer | UI/UX 实现 | **免费** |
    | Fixer | 快速实现（Orchestrator 自动委派） | 低（1倍） |
    | Observer | 已禁用（无免费多模态模型） | — |

3. **回退方式**：
   - 如果不习惯，随时可以无损卸载（见步骤 6）
   - 卸载后 OpenCode 恢复原始模式

### 步骤 6：卸载（仅在用户要求时执行）

> **无损卸载**：只移除 OmO-slim 相关内容，不动用户原有的 Provider 配置。

详见 [references/uninstall-guide.md](references/uninstall-guide.md)

简要步骤：

1. 从 `opencode.json` 的 `plugin` 数组中移除 `"oh-my-opencode-slim"`
2. 删除 OmO-slim 配置文件：
   - `~/.config/opencode/oh-my-opencode-slim.jsonc`
   - `~/.config/opencode/oh-my-opencode-slim.json`
3. （可选）删除 Skills 目录：`~/.config/opencode/skills/simplify` 等
4. 验证：`opencode --version`，确认无插件输出，Tab 恢复正常切换

**判据**：`opencode.json` 中无 OmO-slim 插件条目，Agent 切换恢复正常。

## 决策表

| 用户需求 | 操作 |
|---------|------|
| 安装 OmO-slim | 步骤 1-4 |
| 安装后想自定义模型分配 | 修改 `oh-my-opencode-slim.jsonc` 的 `presets` |
| 用着不习惯想卸载 | 步骤 6 |
| 想临时回到原生模式 | 不卸载，直接在 opencode.json 中临时注释 plugin 条目 |
| Provider 额度用完了 | OmO-slim 不自动 fallback，需手动切换 `/preset` 或修改配置 |
| 添加了新的 Provider | 在 `oh-my-opencode-slim.jsonc` 中添加新的 Preset 或修改现有 Preset |
| 更新 OmO-slim 插件 | `bunx oh-my-opencode-slim@latest install --no-tui --skills=yes` |
| 使用 V2 后台编排 | 参考 [references/slim-v2-beta.md](references/slim-v2-beta.md) |
| 调用架构咨询 | 输入 `@oracle "你的问题"` |
| 调用多模型讨论 | 输入 `@council "你的问题"` |
| 切换预设 | `/preset` 列出预设，`/preset <name>` 切换 |

## 边界情况

- **bun 未安装**：引导用户安装 bun（Windows: `npm install -g bun`，Mac: `curl -fsSL https://bun.sh/install | bash`）
- **OpenCode 版本过低**：先使用 `opencode-update` skill 升级到 v1.0.150+
- **没有智谱 Coding Plan**：Orchestrator 可以只用 Zen 免费模型（zen-free preset），但 Oracle/Fixer 需要智谱模型
- **配置文件已存在**：安装器会提示，使用 `--reset` 强制覆盖（会创建 .bak 备份）
- **安装后 Tab 没有 Agent**：检查 plugin 注册是否正确，运行 `bunx oh-my-opencode-slim doctor`
- **卸载后 Tab 恢复正常**：确认 `plugin` 数组中已无 OmO-slim 条目，重启 OpenCode
- **Observer 已禁用**：`disabled_agents: ["observer"]`，无免费多模态模型可用
- **Orchestrator 委派不准**：`/preset zhipu-std` 升级到 glm-4.7，再不行继续升级

## 参考

- [references/slim-config-templates.md](references/slim-config-templates.md) — 双平台配置模板（Zen + 智谱）
- [references/slim-usage-guide.md](references/slim-usage-guide.md) — OmO-slim 使用手册（Agent、Preset、命令、Skills 等）
- [references/slim-v2-beta.md](references/slim-v2-beta.md) — V2 后台编排 Beta 说明
- [references/uninstall-guide.md](references/uninstall-guide.md) — 无损卸载详细步骤
- OmO-slim 官方文档：https://github.com/alvinunreal/oh-my-opencode-slim
- OmO-slim 安装指南：https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/installation.md
- OmO-slim 配置参考：https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/configuration.md