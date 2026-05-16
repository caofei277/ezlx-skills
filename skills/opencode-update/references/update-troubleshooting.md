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

改用 GitHub Release 手动下载方式（方式 C）更新，或临时修正 npm prefix：

```bash
# 查看正确的 npm prefix（nvm 用户）
npm config get prefix
# 如果异常，可临时修正：
npm config set prefix ~/.nvm/versions/node/$(node -v)
```

---

## 问题 3：`curl -fsSL https://opencode.ai/install | bash` 失败

### 现象

```
curl: (35) Recv failure: Connection reset by peer
```

或

```
curl: (7) Failed to connect to opencode.ai
```

### 原因

- 网络防火墙或 GFW 阻断了 `opencode.ai` 的连接
- DNS 解析失败
- 代理未正确配置

### 解决

1. 检查网络连通性：`curl -sI https://opencode.ai`
2. 若配置了代理，确保环境变量已设置：
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:7890
   ```
3. 改用方式 B（npm）或方式 C（GitHub Release 直接下载）

---

## 问题 4：GitHub Release 下载超时或极慢

### 现象

```bash
curl -sL https://github.com/anomalyco/opencode/releases/download/v1.15.0/opencode-darwin-arm64.zip -o /tmp/opencode.zip
# 长时间无响应或速度极慢
```

### 原因

GitHub releases 的 CDN（`objects.githubusercontent.com`）在某些地区（如中国大陆）访问受限。

### 解决

1. 配置代理后重试
2. 使用 GitHub 镜像加速（如 `https://ghfast.top/https://github.com/...`）
3. 通过 npm 下载（`npm pack opencode-ai` 获取包，但通常不含平台二进制）

---

## 问题 5：更新后 `opencode --version` 挂起

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

# 或直接启动 opencode 进入 TUI，在界面内查看版本
```

也可以通过 npm 查询最新版本对比：

```bash
npm view opencode-ai version
```

---

## 问题 6：备份文件清理

更新成功后，旧版本备份文件可安全删除：

```bash
rm -f $(which opencode).bak
```

若需回滚，在删除备份前执行：

```bash
cp $(which opencode).bak $(which opencode)
codesign --force --deep -s - $(which opencode)  # macOS
```
