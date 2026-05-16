# ezlx-skills

[English](README.en.md)

Agent Skills 与工具集合，由 ezlx 团队维护。

## 一键安装

### Windows (PowerShell)

```powershell
curl -fsSL https://raw.githubusercontent.com/caofei277/ezlx-skills/main/install.ps1 | pwsh
```

### macOS / Linux (Bash)

```bash
curl -fsSL https://raw.githubusercontent.com/caofei277/ezlx-skills/main/install.sh | bash
```

安装完成后，Skill 会放入 `~/.config/opencode/skills/`（全局可用）。

## 可用 Skills

### opencode-cross-platform-setup

在 Windows / macOS / Linux 上安装配置 [OpenCode](https://opencode.ai)，包括多 Coding Plan Provider 接入与 MCP 集成。

**功能**：
- 自动检测平台（Windows / macOS / Linux）
- 安装 opencode-ai（通过 npm）
- 配置 OpenCode Go（内置提供商，通过 `/connect` 命令）
- 配置智谱 Coding Plan / 阿里云百炼 Coding Plan Provider
- 配置 MCP Puppeteer
- 引导 API Key 设置（环境变量持久化）

**支持的 Provider**：

| Provider | SDK | 模型 |
|----------|-----|------|
| OpenCode Go | 内置（自动路由） | GLM-5.1, DeepSeek V4 Flash/Pro, Qwen3.6 Plus, Kimi K2.6 等 12 个 |
| 智谱 Coding Plan | @ai-sdk/openai-compatible | GLM-5, GLM-5 Turbo, GLM-4.7, GLM-5.1 |
| 阿里云百炼 Coding Plan | @ai-sdk/anthropic | Qwen3.5 Plus, Qwen3.6 Plus, GLM-5, Kimi K2.5 等 9 个 |

### opencode-update

安全更新 OpenCode 到最新版本，处理 macOS 代码签名、npm prefix 冲突、网络不通（GFW）等常见更新失败问题。

**功能**：
- 自动检测当前 opencode 安装方式和版本
- 多种更新方式：官方脚本 > npm > 代理 > GitHub 镜像
- macOS 代码签名修复（解决 `zsh: killed` 问题）
- npm global prefix 冲突检测与绕过
- GFW 网络环境检测，提供代理/镜像降级方案
- 旧版本备份与回滚

**解决的常见问题**：

| 问题 | 原因 |
|------|------|
| `zsh: killed opencode` | macOS 代码签名失效 |
| npm 更新成功但版本未变 | npm prefix 被其他应用覆盖 |
| `curl: (35) Connection reset` | 网络不通（GFW 干扰） |

### 安装指定 Skill

```bash
# 安装单个 skill
bash install.sh opencode-update

# 安装多个 skill
bash install.sh opencode-cross-platform-setup opencode-update
```

## 手动安装

如果不想用脚本，也可以手动操作：

```bash
git clone https://github.com/caofei277/ezlx-skills.git
mkdir -p ~/.config/opencode/skills
cp -r ezlx-skills/skills/* ~/.config/opencode/skills/
```

## License

[MIT](LICENSE)
