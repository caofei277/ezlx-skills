# OpenCode 更新问题排查指南

## 问题 1：`zsh: killed opencode`（macOS）

### 现象

更新 opencode 二进制后，执行 `opencode` 立即被系统 kill：

```
caofei@bogon ~ % opencode
zsh: killed     opencode
```

### 原因

macOS 对所有可执行文件强制要求有效代码签名。从 GitHub Release 的 zip 包解压出的二进制文件，其嵌入的代码签名会失效（签名与文件内容不匹配）。macOS 内核直接发送 SIGKILL 终止进程，不会弹出任何提示。

### 诊断

```bash
codesign -vvv $(which opencode)
```

若输出 `invalid signature (code or signature have been modified)`，即确认此问题。

### 解决

使用 ad-hoc 签名重新签名：

```bash
codesign --force --deep -s - $(which opencode)
```

验证：

```bash
codesign -vvv $(which opencode)
# 应输出：valid on disk / satisfies its Designated Requirement
```

若仍有问题，清除 macOS 隔离属性：

```bash
xattr -cr $(which opencode)
```

### 背景

- `codesign -s -`：使用 ad-hoc 签名（无开发者证书也能用）
- `--force`：覆盖已有签名
- `--deep`：递归签名 bundle 内的所有代码
- 此操作不影响 opencode 功能，仅满足 macOS 运行时要求

---

## 问题 2：`npm install -g` 成功但版本未变

### 现象

```bash
npm install -g opencode-ai@latest
# changed 2 packages in 10s

opencode --version
# 仍然显示旧版本
```

### 原因

`npm install -g` 将包安装到 `npm config get prefix` 指定的目录。若该 prefix 被其他应用（如 Codex Desktop）覆盖，npm 会将 opencode 安装到那个应用的目录下，而非用户 PATH 中实际使用的 opencode 所在位置。

### 诊断

```bash
npm config get prefix
```

正常值示例：
- `~/.nvm/versions/node/v22.14.0`
- `/usr/local`

异常值示例：
- `/Applications/Codex.app/Contents`（被 Codex Desktop 覆盖）

再检查实际 opencode 路径：

```bash
which opencode
# 例如：/Users/caofei/.opencode/bin/opencode（curl 脚本安装）
```

若 `which` 路径和 npm prefix 不在同一路径树下，说明 npm global 安装无法更新当前使用的 opencode。

### 解决

改用 GitHub Release 镜像/代理下载方式（方式 C）更新，或临时修正 npm prefix：

```bash
# 查看正确的 npm prefix（nvm 用户）
npm config get prefix
# 如果异常，可临时修正：
npm config set prefix ~/.nvm/versions/node/$(node -v)
```

---

## 问题 3：GFW 导致下载静默损坏（最隐蔽的问题）

### 现象

```bash
curl -sL "https://github.com/.../opencode-darwin-arm64.zip" -o /tmp/opencode.zip
echo $?
# 0（curl 没报错！）

ls -la /tmp/opencode.zip
# -rw-r--r-- 35232142 bytes（看起来正常，但实际不完整）

# 正确的文件应为 35243239 bytes
```

替换后 opencode 表面上可以启动，但实际运行的是**损坏或旧版本**的二进制文件。

### 原因

GFW 对 GitHub 的干扰方式不是直接阻断，而是在 TLS 握手阶段注入 RST 包或在数据传输中截断连接。curl 在某些情况下会将不完整的响应保存为文件并返回退出码 0，**不报任何错误**。

这导致：
1. 下载了一个**不完整**的 zip 文件，但 curl 没报错
2. unzip 可能仍然能解压出二进制文件（zip 格式允许部分解压）
3. 解压出的二进制文件是**旧版本**或**损坏**的
4. 替换后以为更新成功，实际版本没变

### 诊断

```bash
# 1. 校验 zip 完整性
unzip -t /tmp/opencode.zip
# 损坏文件：报错 "invalid compressed data" 或 "unexpected end"
# 正常文件：输出 "No errors detected in compressed data"

# 2. 对比文件大小
ls -la /tmp/opencode.zip
# 同版本的正确 zip 大小应一致，若差异超过 1MB 大概率损坏

# 3. 替换后验证二进制
OLD_SIZE=$(stat -f%z $(which opencode).bak 2>/dev/null || stat -c%s $(which opencode).bak 2>/dev/null)
NEW_SIZE=$(stat -f%z $(which opencode) 2>/dev/null || stat -c%s $(which opencode) 2>/dev/null)
echo "Old: ${OLD_SIZE} → New: ${NEW_SIZE}"
# 新旧完全相同 → 替换未生效或下载到同版本

file $(which opencode)
# 正确：Mach-O 64-bit executable arm64
# 错误：ASCII text（下载到 HTML 错误页）
```

### 解决

1. **删除损坏的下载文件**，不要使用它
2. **换用镜像下载**（推荐）：

```bash
GITHUB_URL="https://github.com/anomalyco/opencode/releases/download/<VERSION>/opencode-darwin-arm64.zip"
curl -sL "https://ghfast.top/${GITHUB_URL}" -o /tmp/opencode.zip
```

3. **或使用代理下载**：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
curl -sL "https://github.com/anomalyco/opencode/releases/download/<VERSION>/opencode-darwin-arm64.zip" -o /tmp/opencode.zip
unset HTTPS_PROXY
```

4. **下载后必须校验**：

```bash
unzip -t /tmp/opencode.zip
```

---

## 问题 4：`curl -fsSL https://opencode.ai/install | bash` 失败

### 现象

```
curl: (35) Recv failure: Connection reset by peer
```

### 原因

- `opencode.ai` 本身可达（Cloudflare CDN），但安装脚本内部从 GitHub Releases 下载二进制
- GitHub 被 GFW 干扰 → 脚本下载阶段失败

### 解决

1. 检查 GitHub 连通性：`curl -sI --connect-timeout 5 https://github.com`
2. GitHub 不可达时，不要使用官方脚本，改用方式 C（镜像/代理下载）
3. 若有代理：
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:7890
   curl -fsSL https://opencode.ai/install | bash
   unset HTTPS_PROXY
   ```

---

## 问题 5：GitHub 镜像也不可用

### 现象

镜像服务返回错误或超时。

### 原因

GitHub Release 镜像服务（ghfast.top 等）是第三方免费服务，稳定性不保证。

### 解决

按顺序尝试以下镜像：

```bash
# 1. ghfast.top（推荐）
curl -sL "https://ghfast.top/https://github.com/..." -o /tmp/opencode.zip

# 2. gh-proxy.com
curl -sL "https://gh-proxy.com/https://github.com/..." -o /tmp/opencode.zip

# 3. ghproxy.cn
curl -sL "https://ghproxy.cn/https://github.com/..." -o /tmp/opencode.zip
```

若所有镜像都不可用，引导用户配置代理后直连 GitHub。

---

## 问题 6：更新后 `opencode --version` 挂起

### 现象

```bash
opencode --version
# 没有输出，进程挂起（实际上启动了 TUI）
```

### 原因

部分版本的 opencode 不支持 `--version` 标志，该参数被忽略后直接启动 TUI 界面。

### 解决

不要用 `--version` 验证。改用：

```bash
file $(which opencode)
# Mach-O 64-bit executable arm64
```

也可以通过 npm 查询最新版本对比：

```bash
npm view opencode-ai version
```

---

## 问题 7：备份与回滚

### 备份文件清理

更新成功后，旧版本备份文件可安全删除：

```bash
rm -f $(which opencode).bak
```

### 回滚操作

若更新后 opencode 无法正常运行：

```bash
cp $(which opencode).bak $(which opencode)
codesign --force --deep -s - $(which opencode)  # macOS
```
