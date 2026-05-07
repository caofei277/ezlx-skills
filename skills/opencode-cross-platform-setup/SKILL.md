---
name: opencode-cross-platform-setup
description: 在 Windows/macOS/Linux 上安装配置 OpenCode，包括多 Coding Plan Provider（智谱/阿里云百炼）接入与 MCP 集成。用于新成员入职或新机器初始化时一键落地可用的 OpenCode 环境。
metadata:
  display_name: OpenCode 跨平台安装配置
  version: "3"
compatibility:
  - filesystem
  - nodejs
  - npm
---

# OpenCode 跨平台安装配置

## 何时使用

- 用户要求"安装 OpenCode""配置 OpenCode""初始化开发环境"中的 OpenCode 部分
- 需要为当前机器新增或变更 Coding Plan Provider（智谱 / 阿里云百炼）
- 需要修复 OpenCode 配置文件缺失或损坏的问题

## 不适用

- OpenCode 使用技巧或对话技巧（非安装配置范畴）
- 其他 IDE/编辑器的配置
- OpenCode 源码开发与调试

## 输入

- 当前操作系统（由 agent 自动检测，无需用户提供）
- 用户选择要配置的 Provider：智谱 / 阿里云百炼 / 两者都要
- 用户提供的 API Key（敏感值，不得写入仓库）

## 输出

- 已安装的 OpenCode 二进制（全局可用）
- `~/.config/opencode/opencode.json` 配置文件（含 Provider、模型、MCP）
- 安装验证通过：`opencode --version` 正常返回，TUI 内 `/models` 显示配置的模型

## 约束

- **安全**：API Key 不得明文写入配置文件提交到仓库；使用 `{env:VAR_NAME}` 变量引用或 `/connect` 交互输入
- **安全**：配置文件路径（`~/.config/opencode/`）应加入项目 `.gitignore`
- **幂等**：重复执行不应破坏已有配置；已安装时跳过安装步骤
- **平台适配**：所有路径和命令必须根据当前 OS 自动适配，不得硬编码
- **配置合并**：OpenCode 配置文件是合并而非替换；多个配置源可叠加

## 主流程

### 步骤 0：前置条件检查

确认 Node.js 已安装：

```bash
node --version
```

若未安装，引导用户安装 Node.js（建议 v20+）。Node.js 是 OpenCode 的运行前提。

**判据**：`node --version` 返回 v20+ 版本号。

### 步骤 1：平台检测

检测当前 OS 并确定关键路径：

| 项目 | Windows | macOS / Linux |
|------|---------|---------------|
| 配置目录 | `%USERPROFILE%\.config\opencode\` | `$HOME/.config/opencode/` |
| 配置文件 | 同上 `opencode.json` | 同上 `opencode.json` |
| npx 命令 | `C:\Program Files\nodejs\npx.cmd` | `npx` |

**判据**：成功获取路径变量。

### 步骤 2：安装 / 升级 OpenCode

```bash
npm install -g opencode-ai@latest
```

> 注意：npm 包名是 `opencode-ai`，不是 `opencode`。

安装后验证：

```bash
opencode --version
```

**判据**：命令返回版本号，无报错。

### 步骤 3：创建配置目录

若 `~/.config/opencode/` 不存在则创建。

**判据**：目录存在且可写。

### 步骤 4：生成配置文件

根据用户选择的 Provider，组装 `opencode.json`。配置模板见：

- 单 Provider 模板 → [references/provider-templates.md](references/provider-templates.md)
- 完整多 Provider + MCP 模板 → [references/full-config-template.md](references/full-config-template.md)

关键规则：
- `model` 字段设为用户选择的主模型（默认 `zhipu-coding-plan/glm-5.1`）
- MCP Puppeteer 命令路径按步骤 1 的平台结果填入
- `apiKey` 字段使用 OpenCode 变量语法 `{env:环境变量名}`，不得硬编码明文。例如：`{env:ZHIPU_API_KEY}`
- 也支持从文件读取：`{file:~/.secrets/zhipu-key}`
- 若环境变量未设置，将替换为空字符串

**判据**：文件写入成功，JSON 格式合法。

### 步骤 5：引导配置 API Key

向用户说明：

1. API Key 获取地址（见下方决策表）
2. 推荐设置环境变量并持久化到 shell profile：
   - macOS/Linux：将 `export ZHIPU_API_KEY="xxx"` 写入 `~/.bashrc` 或 `~/.zshrc`
   - Windows：`[Environment]::SetEnvironmentVariable("ZHIPU_API_KEY", "xxx", "User")` 持久化为用户级变量
3. 或者使用 OpenCode 内置的 `/connect` 命令交互输入（密钥存储在 `~/.local/share/opencode/auth.json`）
4. 提醒将 `.config/opencode/opencode.json` 加入 `.gitignore`

**判据**：用户已知晓 API Key 配置方式。

### 步骤 6：最终验证

启动 OpenCode：

```bash
cd /path/to/project
opencode
```

在 TUI 内执行 `/models`，确认输出中包含用户配置的 Provider 和模型。

**判据**：模型列表中可见配置的 Provider 模型。

## 决策表

| 用户需求 | Provider ID | npm SDK 包 | baseURL | API Key 环境变量 | 获取地址 |
|----------|-------------|-----------|---------|-----------------|---------|
| 智谱 Coding Plan | `zhipu-coding-plan` | `@ai-sdk/openai-compatible` | `https://open.bigmodel.cn/api/coding/paas/v4` | `ZHIPU_API_KEY` | https://open.bigmodel.cn → Coding Plan 套餐 |
| 阿里云百炼 Coding Plan | `bailian-coding-plan` | `@ai-sdk/anthropic` | `https://coding.dashscope.aliyuncs.com/apps/anthropic/v1` | `DASHSCOPE_API_KEY` | https://bailian.console.aliyun.com |

## 边界情况

- **已安装旧版本**：直接 `npm install -g opencode-ai@latest` 覆盖安装
- **配置文件已存在**：OpenCode 配置采用合并策略，新增 Provider 不会覆盖已有配置；但同名 key 会覆盖，提示用户确认
- **npx 路径不存在**（Windows）：检查 `%USERPROFILE%\AppData\Roaming\npm\npx.cmd` 作为备选；若仍未找到，提示用户确认 Node.js 安装
- **npm 全局权限不足**（Linux/macOS）：提示使用 `sudo` 或建议通过 nvm 管理 Node
- **MCP Puppeteer 启动失败**：不影响核心功能，建议用户设置 `"enabled": false` 跳过
- **Windows 推荐使用 WSL**：OpenCode 官方推荐 Windows 用户通过 WSL 获得最佳体验；但也支持原生 Windows（Chocolatey/Scoop/npm 均可）
- **`{env:VAR}` 未设置**：变量会被替换为空字符串，导致 API Key 为空，请求会鉴权失败——需提醒用户确认环境变量已设置并已重启终端

## 参考

- [references/provider-templates.md](references/provider-templates.md) — 各 Provider 的模型配置模板
- [references/full-config-template.md](references/full-config-template.md) — 多 Provider + MCP 完整配置模板
- [references/model-params.md](references/model-params.md) — 模型参数字段说明
- OpenCode 官方：https://opencode.ai
- OpenCode 配置文档：https://opencode.ai/docs/config/
- OpenCode Provider 文档：https://opencode.ai/docs/providers/
- 智谱 GLM 文档：https://open.bigmodel.cn
- 阿里云百炼文档：https://help.aliyun.com/zh/model-studio/
