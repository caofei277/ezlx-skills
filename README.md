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

### omo-setup

安装配置 [oh-my-openagent (OmO)](https://github.com/code-yeongyu/oh-my-openagent) 多模型编排插件，实现 AI Agent 自动按任务类型分配不同模型，支持 OpenCode Zen 免费层，跨平台额度互为备份。**支持无损卸载**，不习惯随时回退。

**功能**：
- 自动检测用户已有的 Coding Plan Provider
- 安装 OmO 插件到 OpenCode
- 根据用户 Provider 组合生成最优 Agent/Category 模型分配配置
- 配置跨平台 fallback 回退链（额度用完自动切换同款模型）
- 提供无损卸载流程，卸载后 OpenCode 恢复原始 Plan/Build 模式

**模型分配策略**：

| 任务类型 | 推荐模型 | 平台 | 成本 |
|----------|---------|------|------|
| 编排调度 / 快速任务 | DeepSeek V4 Flash Free | OpenCode Zen | **免费** |
| 中等任务 | DeepSeek V4 Pro | OpenCode Go | 低 |
| 规划 / 前端 / UI / 写作 | Qwen 3.6 Plus | 百炼 / OpenCode Go | 中等 |
| 架构咨询 / 复杂自主 | GLM-5 | 百炼 / OpenCode Go | 中等 |
| 审查评估 | GLM-5 Turbo | 智谱 | 中等 |
| 复杂推理 (ultrawork) | GLM-5.1 | 智谱 / OpenCode Go | 高 |

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
| OpenCode Zen | 内置（免费） | DeepSeek V4 Flash Free（免费） |
| OpenCode Go | 内置（自动路由） | GLM-5.1, DeepSeek V4 Flash/Pro, Qwen3.6 Plus, Kimi K2.6 等 12 个 |
| 智谱 Coding Plan | @ai-sdk/openai-compatible | GLM-5, GLM-5 Turbo, GLM-4.7, GLM-5.1 |
| 阿里云百炼 Coding Plan | @ai-sdk/anthropic | Qwen3.5 Plus, Qwen3.6 Plus, GLM-5, Kimi K2.5 等 9 个 |

### difit

使用 [difit](https://github.com/yoshiko-pg/difit) CLI 以 GitHub 风格 WebUI 查看和审查本地 git 差异，支持提交审查、分支对比、PR 审查和评论注入，评论可作为 AI 提示复制使用。

**功能**：
- 审查最新提交、指定提交、分支对比、工作目录变更
- 审查 GitHub PR（配合 GitHub CLI）
- WebUI 行内评论系统，支持按行或范围选择
- 评论可一键复制为结构化 AI 提示
- 代理可通过 `--comment` 参数预注入审查评论
- 支持标准输入管道 diff（兼容任意 diff 工具）
- 自动识别并折叠已删除文件、自动生成文件

**使用示例**：

```bash
# 审查最新提交
difit

# 审查未提交的更改
difit .

# 对比分支
difit feature main

# 审查 PR
difit --pr https://github.com/owner/repo/pull/123
```

### opencode-update

安全更新 OpenCode 到最新版本，处理 macOS 代码签名、npm prefix 冲突、网络不通（GFW）等常见更新失败问题。

**功能**：
- 自动检测当前 opencode 安装方式、版本和网络环境
- GFW 环境下优先使用 GitHub 镜像加速（ghfast.top 等）
- 多种更新方式：镜像 > 代理 > npm > 直连
- 下载完整性校验（防止 GFW 静默损坏文件）
- macOS 代码签名修复（解决 `zsh: killed` 问题）
- npm global prefix 冲突检测与绕过
- 旧版本备份与回滚

**解决的常见问题**：

| 问题 | 原因 |
|------|------|
| `zsh: killed opencode` | macOS 代码签名失效 |
| npm 更新成功但版本未变 | npm prefix 被其他应用覆盖 |
| `curl: (35) Connection reset` | GFW 干扰 GitHub 连接 |
| 下载完成但文件损坏 | GFW 静默截断下载，curl 未报错 |

### 安装指定 Skill

```bash
# 安装单个 skill
bash install.sh difit

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
