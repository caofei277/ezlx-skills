---
name: opencode-update
description: 安全更新 OpenCode 到最新版本，处理 macOS 代码签名、npm prefix 冲突、网络不通等常见更新失败问题。
metadata:
  display_name: OpenCode 更新
  version: "1"
compatibility:
  - filesystem
  - nodejs
  - npm
---

# OpenCode 更新

## 何时使用

- 用户要求"更新 OpenCode""升级 OpenCode""opencode 版本太旧"
- 用户执行更新后遇到 `zsh: killed opencode`（macOS 签名问题）
- 用户执行更新后版本号未变化
- 用户反馈 `curl -fsSL https://opencode.ai/install | bash` 失败

## 不适用

- OpenCode 首次安装（使用 `opencode-cross-platform-setup` skill）
- OpenCode 配置问题（Provider / MCP / 模型配置）
- OpenCode 使用技巧

## 输入

- 当前操作系统（agent 自动检测）
- 当前 opencode 安装路径和版本（agent 自动检测）

## 输出

- opencode 已更新到最新版本
- 二进制文件可正常执行，无 `killed` / `segfault` 等错误

## 约束

- **安全**：替换二进制前必须备份旧版本，以便回滚
- **macOS**：从外部下载的二进制文件必须重新签名（`codesign`），否则系统会直接 kill 进程
- **幂等**：已是最新版本时跳过，不重复操作
- **不破坏配置**：更新过程不得修改 `~/.config/opencode/opencode.json` 或 `~/.local/share/opencode/auth.json`

## 主流程

### 步骤 0：前置检查

检测当前 opencode 安装情况：

```bash
which opencode
```

```bash
opencode --version
```

> 注意：部分版本的 `opencode --version` 会启动 TUI 而非输出版本号。若命令挂起，直接终止，改用其他方式获取版本。

若 `which opencode` 返回路径，确认安装方式：

| 安装路径模式 | 安装方式 | 更新策略 |
|-------------|---------|---------|
| `~/.opencode/bin/opencode` | curl 官方安装脚本 | 方式 A → C |
| `~/.nvm/versions/node/.../opencode` | npm global | 方式 B |
| `/usr/local/bin/opencode` | Homebrew | 方式 B（brew） |
| 其他 | 需确认 | 方式 C |

**判据**：已确定 opencode 安装路径和当前版本。

### 步骤 1：查询最新版本

```bash
npm view opencode-ai version
```

若当前版本已是最新，告知用户并结束。

**判据**：已确认最新版本号，判断是否需要更新。

### 步骤 2：执行更新（按优先级尝试）

#### 方式 A：官方安装脚本（推荐）

```bash
curl -fsSL https://opencode.ai/install | bash
```

成功后跳至步骤 3 验证。

若失败（网络不通、Connection reset 等），继续尝试方式 B。

#### 方式 B：npm 全局安装

```bash
npm install -g opencode-ai@latest
```

**注意 npm prefix 冲突**：若 `npm config get prefix` 返回非标准路径（如 `/Applications/Codex.app/Contents`），说明 npm global prefix 被其他应用覆盖。此时 `npm install -g` 会安装到错误位置，不会更新实际使用的 opencode 二进制。

检测方法：

```bash
npm config get prefix
```

正常路径应为：
- macOS/Linux（nvm）：`~/.nvm/versions/node/<version>`
- macOS/Linux（Homebrew Node）：`/usr/local`
- Windows：`C:\Program Files\nodejs` 或 `%APPDATA%\npm`

若 prefix 异常，**跳过方式 B**，改用方式 C。

若通过 Homebrew 安装的：

```bash
brew upgrade anomalyco/tap/opencode
```

#### 方式 C：GitHub Release 手动下载（兜底方案）

当方式 A 和 B 都不可用时，直接从 GitHub Release 下载二进制替换。

**步骤 C.1：确认平台和架构**

| 平台 | 架构 | 下载文件 |
|------|------|---------|
| macOS | Apple Silicon (M1/M2/M3/M4) | `opencode-darwin-arm64.zip` |
| macOS | Intel | `opencode-darwin-x64.zip` |
| Linux | ARM64 | `opencode-linux-arm64.zip` |
| Linux | x64 | `opencode-linux-x64.zip` |

```bash
uname -sm
```

**步骤 C.2：查询最新 Release 版本**

```bash
curl -sL https://api.github.com/repos/anomalyco/opencode/releases/latest | grep '"tag_name"'
```

**步骤 C.3：下载并替换**

以 macOS ARM64 为例，将 `<VERSION>` 替换为上一步获取的版本号：

```bash
OLD_BIN=$(which opencode)
cp "$OLD_BIN" "${OLD_BIN}.bak"

curl -sL "https://github.com/anomalyco/opencode/releases/download/<VERSION>/opencode-darwin-arm64.zip" -o /tmp/opencode-update.zip
unzip -o /tmp/opencode-update.zip -d /tmp/opencode-update/
cp /tmp/opencode-update/opencode "$OLD_BIN"
chmod +x "$OLD_BIN"
```

**步骤 C.4：macOS 签名修复（必须）**

从 GitHub Release 下载的 zip 解压后，二进制文件的代码签名可能失效。macOS 会直接 kill 掉未签名或签名无效的二进制。

```bash
codesign --force --deep -s - "$(which opencode)"
```

验证签名：

```bash
codesign -vvv "$(which opencode)"
```

应输出：`valid on disk` 和 `satisfies its Designated Requirement`。

若仍有问题，清除隔离属性：

```bash
xattr -cr "$(which opencode)"
```

**步骤 C.5：清理临时文件**

```bash
rm -rf /tmp/opencode-update.zip /tmp/opencode-update/
```

**判据**：新版本二进制已替换旧版本，签名验证通过。

### 步骤 3：更新验证

确认二进制可执行：

```bash
opencode --version
```

若该命令挂起（某些版本会启动 TUI），改用以下方式验证：

```bash
file $(which opencode)
```

应输出类似：`Mach-O 64-bit executable arm64`（macOS ARM64）。

确认无 `killed` 或 `segfault` 错误。

**判据**：`opencode` 命令可正常启动，无被系统 kill 的现象。

### 步骤 4：回滚（仅在更新失败时）

若更新后 opencode 无法正常运行：

```bash
OLD_BIN=$(which opencode)
cp "${OLD_BIN}.bak" "$OLD_BIN"
```

回滚后重新签名（macOS）：

```bash
codesign --force --deep -s - "$(which opencode)"
```

## 决策表

| 现象 | 原因 | 解决方案 |
|------|------|---------|
| `curl: (35) Recv failure: Connection reset by peer` | 网络不通（防火墙/GFW） | 改用方式 B 或 C |
| `npm install -g` 成功但版本未变 | npm global prefix 被其他应用覆盖 | 检查 `npm config get prefix`，改用方式 C |
| `zsh: killed opencode` | macOS 代码签名无效 | `codesign --force --deep -s - $(which opencode)` |
| `codesign: invalid signature` | 下载的二进制签名被破坏 | 重新执行 `codesign --force --deep -s -` |
| `opencode: command not found` | 更新后 PATH 中的路径变了 | 检查 `which opencode`，确认 PATH 配置 |
| 下载速度极慢 | GitHub CDN 在某些地区受限 | 耐心等待，或配置代理后重试 |

## 参考

- [references/update-troubleshooting.md](references/update-troubleshooting.md) — 详细问题排查指南
- OpenCode 官方安装文档：https://opencode.ai/docs/#install
- GitHub Releases：https://github.com/anomalyco/opencode/releases
