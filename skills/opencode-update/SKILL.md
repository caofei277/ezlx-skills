---
name: opencode-update
description: 安全更新 OpenCode 到最新版本，处理 macOS 代码签名、npm prefix 冲突、GFW 网络不通等常见更新失败问题。内置代理检测与 GitHub 镜像加速方案。
metadata:
  display_name: OpenCode 更新
  version: "2"
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
- 用户反馈 `curl -fsSL https://opencode.ai/install | bash` 或 `opencode upgrade` 失败
- 用户在中国大陆网络环境下无法正常更新

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

#### 0.1 检测当前 opencode 安装情况

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
| `~/.opencode/bin/opencode` | curl 官方安装脚本 | 方式 A → D → E |
| `~/.nvm/versions/node/.../opencode` | npm global | 方式 B |
| `/usr/local/bin/opencode` | Homebrew | 方式 B（brew） |
| 其他 | 需确认 | 方式 D 或 E |

#### 0.2 网络环境检测（中国大陆用户关键步骤）

opencode 的更新涉及两个网络端点，它们的可达性不同：

| 端点 | 用途 | 中国大陆可达性 |
|------|------|---------------|
| `opencode.ai` | 官方安装脚本 | 通常可达（Cloudflare CDN） |
| `github.com` | Release 二进制下载 | **大概率被 GFW 干扰** |
| `api.github.com` | 查询 Release 信息 | 部分可达 |

**执行网络检测**：

```bash
curl -sI --connect-timeout 5 https://opencode.ai 2>&1 | head -3
```

```bash
curl -sI --connect-timeout 5 https://github.com 2>&1 | head -3
```

```bash
echo $HTTPS_PROXY
```

**诊断结果**：

| 现象 | 结论 | 推荐方式 |
|------|------|---------|
| GitHub 返回 `HTTP/2 200` | 网络正常 | 方式 A → B → D |
| GitHub 返回 `Connection reset by peer` | GFW 干扰，需代理 | 方式 C → E |
| GitHub 超时无响应 | GFW 封锁 | 方式 C → E |
| `HTTPS_PROXY` 已设置 | 已配置代理 | 方式 A → B → D |

**判据**：已确定 opencode 安装路径、当前版本和网络环境。

### 步骤 1：查询最新版本

```bash
npm view opencode-ai version
```

若当前版本已是最新，告知用户并结束。

**判据**：已确认最新版本号，判断是否需要更新。

### 步骤 2：执行更新（按优先级尝试）

#### 方式 A：官方安装脚本（推荐，网络通畅时首选）

```bash
curl -fsSL https://opencode.ai/install | bash
```

成功后跳至步骤 3 验证。

> **说明**：该脚本的下载源仍是 GitHub Releases，若 GitHub 不可达，此方式会失败。

若失败（`Connection reset` / 超时），根据步骤 0.2 的检测结果：
- 有代理 → 方式 C（代理更新）
- 无代理 → 方式 D（npm）或方式 E（GitHub 镜像）

#### 方式 B：npm 全局安装（适合 npm 安装的用户）

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

若 prefix 异常，**跳过方式 B**，改用方式 D 或 E。

若通过 Homebrew 安装的：

```bash
brew upgrade anomalyco/tap/opencode
```

#### 方式 C：代理更新（GFW 环境首选）

当 `github.com` 不可达（`Connection reset by peer` / 超时）且用户本地有代理工具（Clash / V2Ray / Shadowrocket 等）时使用。

**步骤 C.1：确认代理端口**

常见代理端口：

| 代理工具 | 默认 HTTP 端口 | 默认 SOCKS5 端口 |
|----------|---------------|-----------------|
| Clash (ClashX Pro) | 7890 | 7891 |
| V2RayU | 1087 | 1080 |
| Surge | 6152 | 6153 |
| Shadowrocket | — | 1080 |
| Quantumult X | — | 1080 |

若不确定，询问用户代理端口。

**步骤 C.2：设置代理环境变量**

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
```

> 将 `7890` 替换为用户实际的代理端口。

**步骤 C.3：通过代理执行官方安装脚本**

```bash
curl -fsSL https://opencode.ai/install | bash
```

成功后清除代理环境变量（可选）：

```bash
unset HTTPS_PROXY HTTP_PROXY
```

成功后跳至步骤 3 验证。

若代理方式也失败（代理未启动、端口错误等），继续方式 D 或 E。

#### 方式 D：GitHub Release 手动下载

当方式 A、B、C 都不可用时，直接从 GitHub Release 下载二进制替换。

> **如果 GitHub 不可达**：在命令前加上代理 `export HTTPS_PROXY=http://127.0.0.1:7890`，或改用方式 E（镜像加速）。

**步骤 D.1：确认平台和架构**

| 平台 | 架构 | 下载文件 |
|------|------|---------|
| macOS | Apple Silicon (M1/M2/M3/M4) | `opencode-darwin-arm64.zip` |
| macOS | Intel | `opencode-darwin-x64.zip` |
| Linux | ARM64 | `opencode-linux-arm64.zip` |
| Linux | x64 | `opencode-linux-x64.zip` |

```bash
uname -sm
```

**步骤 D.2：查询最新 Release 版本**

```bash
curl -sL https://api.github.com/repos/anomalyco/opencode/releases/latest | grep '"tag_name"'
```

**步骤 D.3：下载并替换**

以 macOS ARM64 为例，将 `<VERSION>` 替换为上一步获取的版本号：

```bash
OLD_BIN=$(which opencode)
cp "$OLD_BIN" "${OLD_BIN}.bak"

curl -sL "https://github.com/anomalyco/opencode/releases/download/<VERSION>/opencode-darwin-arm64.zip" -o /tmp/opencode-update.zip
unzip -o /tmp/opencode-update.zip -d /tmp/opencode-update/
cp /tmp/opencode-update/opencode "$OLD_BIN"
chmod +x "$OLD_BIN"
```

**步骤 D.4：macOS 签名修复（必须）**

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

**步骤 D.5：清理临时文件**

```bash
rm -rf /tmp/opencode-update.zip /tmp/opencode-update/
```

**判据**：新版本二进制已替换旧版本，签名验证通过。

#### 方式 E：GitHub 镜像加速下载（无代理时的终极方案）

当用户在中国大陆，既无法直接访问 GitHub，也没有代理可用时，使用 GitHub 镜像服务下载。

**步骤 E.1：确认最新版本**

```bash
npm view opencode-ai version
```

> `npm view` 通常不需要访问 GitHub，走 npm registry（可达）。

**步骤 E.2：使用镜像下载**

常用 GitHub Release 镜像（将 `<URL>` 替换为原始 GitHub 下载链接）：

| 镜像服务 | 用法 | 说明 |
|----------|------|------|
| ghfast.top | `https://ghfast.top/<URL>` | 推荐，速度快 |
| gh-proxy.com | `https://gh-proxy.com/<URL>` | 备选 |
| ghproxy.cn | `https://ghproxy.cn/<URL>` | 备选 |

以 macOS ARM64 为例，将 `<VERSION>` 替换为实际版本号：

```bash
OLD_BIN=$(which opencode)
cp "$OLD_BIN" "${OLD_BIN}.bak"

GITHUB_URL="https://github.com/anomalyco/opencode/releases/download/<VERSION>/opencode-darwin-arm64.zip"
MIRROR_URL="https://ghfast.top/${GITHUB_URL}"

curl -sL "$MIRROR_URL" -o /tmp/opencode-update.zip
unzip -o /tmp/opencode-update.zip -d /tmp/opencode-update/
cp /tmp/opencode-update/opencode "$OLD_BIN"
chmod +x "$OLD_BIN"
```

> **注意**：镜像服务可能不稳定，若一个失败，换另一个尝试。镜像链接格式为 `https://镜像域名/https://github.com/...原始路径...`。

**步骤 E.3：macOS 签名修复（必须）**

```bash
codesign --force --deep -s - "$(which opencode)"
codesign -vvv "$(which opencode)"
```

**步骤 E.4：清理临时文件**

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

## 更新方式选择流程图

```
开始更新
  │
  ├─ 步骤 0.2 检测网络
  │
  ├─ GitHub 可达？
  │   ├─ 是 → 方式 A（官方脚本）
  │   │        ├─ 成功 → 验证
  │   │        └─ 失败 → 方式 B（npm）
  │   │                   ├─ prefix 正常 → 安装 → 验证
  │   │                   └─ prefix 异常 → 方式 D（手动下载）
  │   │
  │   └─ 否（Connection reset / 超时）
  │       │
  │       ├─ 有代理？
  │       │   ├─ 是 → 方式 C（代理更新）
  │       │   │        ├─ 成功 → 验证
  │       │   │        └─ 失败 → 方式 D（代理 + 手动下载）
  │       │   │
  │       │   └─ 否 → 方式 E（镜像加速）
  │       │            ├─ 成功 → 验证
  │       │            └─ 失败 → 引导用户配置代理
  │       │
  │       └─ npm prefix 正常？→ 方式 B（npm，不依赖 GitHub）
```

## 决策表

| 现象 | 原因 | 解决方案 |
|------|------|---------|
| `curl: (35) Recv failure: Connection reset by peer` | GFW 对 `github.com` TLS 握手注入 RST | 方式 C（代理）或方式 E（镜像） |
| `curl: (7) Failed to connect to opencode.ai` | DNS 解析失败或网络中断 | 检查 DNS / 网络连接 |
| `npm install -g` 成功但版本未变 | npm global prefix 被其他应用覆盖 | 检查 `npm config get prefix`，改用方式 D 或 E |
| `zsh: killed opencode` | macOS 代码签名无效 | `codesign --force --deep -s - $(which opencode)` |
| `codesign: invalid signature` | 下载的二进制签名被破坏 | 重新执行 `codesign --force --deep -s -` |
| `opencode: command not found` | 更新后 PATH 中的路径变了 | 检查 `which opencode`，确认 PATH 配置 |
| GitHub 下载速度极慢 | GFW 对 `objects.githubusercontent.com` 限速 | 方式 C（代理）或方式 E（镜像） |
| 镜像下载也失败 | 镜像服务不稳定 | 换一个镜像，或引导用户配置代理 |
| `opencode upgrade` 大概率失败 | 命令内部走 GitHub Releases，被 GFW 干扰 | 使用本文档的方式 C 或 E 替代 |

## 参考

- [references/update-troubleshooting.md](references/update-troubleshooting.md) — 详细问题排查指南
- OpenCode 官方安装文档：https://opencode.ai/docs/#install
- GitHub Releases：https://github.com/anomalyco/opencode/releases
