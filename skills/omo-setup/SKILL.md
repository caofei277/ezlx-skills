---
name: omo-setup
description: 安装配置 oh-my-openagent (OmO) 插件，实现多模型智能体自动编排。支持无损安装与卸载，不破坏现有 OpenCode 多平台 Provider 配置。
metadata:
  display_name: OmO 多模型编排插件
  version: "1"
  compatibility:
    - filesystem
    - nodejs
    - npm
---

# OmO 多模型编排插件安装配置

## 何时使用

- 用户希望 AI Agent 自动按任务类型分配不同模型（前端用通义、逻辑用 GLM、快速任务用 DeepSeek）
- 用户已配置多个 Coding Plan Provider（OpenCode Go / 智谱 / 阿里云百炼），希望跨平台额度互为备份
- 用户想尝试 oh-my-openagent 但不确定是否适合，希望可以无损回退

## 不适用

- OpenCode 本身的安装或 Provider 配置（使用 `opencode-cross-platform-setup` skill）
- OpenCode 版本更新（使用 `opencode-update` skill）
- OmO 插件的二次开发或源码调试

## 前置条件

- OpenCode v1.0.150+ 已安装
- 至少一个 Coding Plan Provider 已配置并可用（建议先配置好 OpenCode Go + 智谱 + 百炼三个平台）
- bun 已安装（仅安装时需要，CLI 本身有独立二进制）

检查命令：

```bash
opencode --version
bun --version
```

## 输入

- 用户当前已有的 Provider 列表（agent 自动从 `opencode.json` 读取）
- 用户对各平台额度情况的描述（哪些模型用得多、哪些是备用）

## 输出

- OmO 插件已注册到 `opencode.json`
- `oh-my-openagent.jsonc` 配置文件已生成（按用户 Provider 分配 Agent 和 Category 模型）
- 包含跨平台 fallback 回退链（额度用完自动切换）
- 验证通过：`bunx oh-my-openagent doctor` 正常

## 约束

- **无损**：安装和卸载过程不得修改用户已有的 Provider 配置（`opencode.json` 的 `provider` 字段）
- **可逆**：卸载后 OpenCode 恢复到安装前的状态，Plan/Build 模式恢复正常
- **安全**：API Key 不得明文写入新文件
- **幂等**：重复执行不破坏已有配置

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

| opencode.json 中的 provider key | OmO 中使用的前缀 |
|------|------|
| （OpenCode Go 内置） | `opencode-go/` |
| `bailian-coding-plan` | `bailian-coding-plan/` |
| `zhipu-coding-plan` | `zhipu-coding-plan/` |

**判据**：已确认 OpenCode 版本、bun 版本、用户已有的 Provider 列表。

### 步骤 2：安装 OmO

```bash
bunx oh-my-openagent install --no-tui --claude=no --openai=no --gemini=no --copilot=no --opencode-go=yes
```

> 根据用户实际订阅调整参数。如果用户只有 OpenCode Go，使用上面这条命令。如果用户还有其他订阅，参考安装参数对照表：

| 订阅 | 参数 |
|------|------|
| OpenCode Go | `--opencode-go=yes` |
| 智谱 Coding Plan | `--zai-coding-plan=yes`（OmO 原生支持智谱模型） |
| Kimi for Coding | `--kimi-for-coding=yes` |

安装完成后，`opencode.json` 的 `plugin` 数组中会新增 `"oh-my-openagent"`。

**验证安装**：

```bash
bunx oh-my-openagent doctor
```

**判据**：`plugin` 数组包含 `"oh-my-openagent"`，doctor 检查无严重错误。

### 步骤 3：生成 OmO 配置文件

根据步骤 1 检测到的 Provider 列表，在用户配置目录生成 `oh-my-openagent.jsonc`：

| 平台 | 配置文件路径 |
|------|-------------|
| Windows | `%USERPROFILE%\.config\opencode\oh-my-openagent.jsonc` |
| Mac/Linux | `~/.config/opencode/oh-my-openagent.jsonc` |

配置文件内容根据用户的 Provider 组合生成，详见：
- 单/双/三 Provider 配置模板 → [references/omo-config-templates.md](references/omo-config-templates.md)

关键规则：
- 每个 Agent 指定主模型 + fallback 回退链（跨平台同款模型互为备份）
- 每个 Category 按任务类型分配最合适的模型
- 优先使用用户已有平台的模型，不引用用户没有的 Provider

**判据**：配置文件已写入，JSONC 格式合法。

### 步骤 4：验证

```bash
bunx oh-my-openagent doctor --verbose
```

确认模型解析正确，无报错。

启动 OpenCode 验证：

```bash
opencode
```

在 TUI 中：
1. 按 Tab 确认可看到 Sisyphus / Prometheus 等 Agent
2. 输入 `/models` 确认模型列表正常

**判据**：Tab 可切换 Agent，模型列表正常。

### 步骤 5：向用户说明

1. **使用方式**：
   - 直接对话：和原来一样，Sisyphus 会自动编排
   - 全自动：输入 `ulw` 或 `ultrawork`，Agent 自动探索、执行、验证
   - 精确规划：按 Tab 切到 Prometheus，或输入 `@plan "需求"`
   - 执行计划：`/start-work`

2. **回退方式**：
   - 如果不习惯，随时可以无损卸载（见步骤 6）
   - 卸载后 OpenCode 恢复原始 Plan/Build 模式

### 步骤 6：卸载（仅在用户要求时执行）

> **无损卸载**：只移除 OmO 相关内容，不动用户原有的 Provider 配置。

详见 [references/uninstall-guide.md](references/uninstall-guide.md)

简要步骤：

1. 从 `opencode.json` 的 `plugin` 数组中移除 `"oh-my-openagent"` 和 `"oh-my-opencode"`
2. 删除 OmO 配置文件：
   - `~/.config/opencode/oh-my-openagent.jsonc`
   - `~/.config/opencode/oh-my-openagent.json`
   - `~/.config/opencode/oh-my-opencode.jsonc`
   - `~/.config/opencode/oh-my-opencode.json`
3. （可选）删除项目级 OmO 配置：`.opencode/oh-my-openagent.jsonc`
4. （可选）删除 OmO 工作目录：`.omo/`
5. 验证：`opencode --version`，确认无插件输出，Tab 恢复 Plan/Build 切换

**判据**：`opencode.json` 中无 OmO 插件条目，Tab 恢复 Plan/Build 模式。

## 决策表

| 用户需求 | 操作 |
|---------|------|
| 安装 OmO | 步骤 1-4 |
| 安装后想自定义模型分配 | 修改 `oh-my-openagent.jsonc` 的 `agents` 和 `categories` |
| 用着不习惯想卸载 | 步骤 6 |
| 想临时回到原生模式 | 不卸载，直接在 opencode.json 中临时注释 plugin 条目 |
| Provider 额度用完了 | OmO 自动 fallback，无需操作 |
| 添加了新的 Provider | 在 `oh-my-openagent.jsonc` 的 fallback_models 中补充新平台模型 |

## 边界情况

- **bun 未安装**：引导用户安装 bun（Windows: `irm bun.sh/install.ps1 | iex`，Mac: `curl -fsSL https://bun.sh/install | bash`）
- **OpenCode 版本过低**：先使用 `opencode-update` skill 升级到 v1.0.150+
- **没有 OpenCode Go**：OmO 可以只用百炼/智谱的模型运行，但推荐配合 OpenCode Go 使用（模型更多、回退链更丰富）
- **配置文件已存在**：合并而非替换，保留用户已有配置
- **安装后 Tab 没有 Agent**：检查 plugin 注册是否正确，运行 `bunx oh-my-openagent doctor`
- **卸载后 Tab 没有 Plan/Build**：确认 `plugin` 数组中已无 OmO 条目，重启 OpenCode

## 参考

- [references/omo-config-templates.md](references/omo-config-templates.md) — 按用户 Provider 组合生成的配置模板
- [references/uninstall-guide.md](references/uninstall-guide.md) — 无损卸载详细步骤
- OmO 官方安装指南：https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/guide/installation.md
- OmO 配置参考：https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/reference/configuration.md
