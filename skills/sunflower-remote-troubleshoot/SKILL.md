---
name: sunflower-remote-troubleshoot
description: 向日葵远程控制无法连接、卡在"正在登录远程桌面"、GUI假活等问题的系统化诊断与修复方案。覆盖 macOS 15 (Sequoia) 环境。
metadata:
  display_name: 向日葵远程连接故障排查
  version: "1"
  compatibility:
    - macOS
    - sunflower
    - awesun
---

# 向日葵远程连接故障排查

## 何时使用

- 向日葵客户端进程在运行，但远程端连不上（提示"正在连接"、"正在登录远程桌面"后卡死）
- 向日葵显示在线，但远程控制请求超时或无响应
- 向日葵运行一段时间后远程端"找不到该设备"或"设备离线"
- 重启向日葵后仍卡在"正在登录远程桌面"画面
- macOS 升级后向日葵无法正常工作

## 不适用

- 向日葵客户端本身未安装（应先去官网下载安装）
- 向日葵账号登录相关问题（忘记密码、账号冻结——联系向日葵客服）
- 网络完全不通（Mac 完全无法上网）
- 其他远程控制软件（TeamViewer、AnyDesk、Chrome Remote Desktop）

## 前置条件

- macOS 终端（Terminal / iTerm2）可用
- 向日葵（AweSun）客户端已安装
- `lsof`、`netstat`、`launchctl` 等 macOS 内建工具

## 架构说明

向日葵在 macOS 上由三个组件构成：

| 组件 | 位置 | 权限 | 说明 |
|------|------|------|------|
| **AweSun GUI** | `/Applications/AweSun.app` | 用户 | 主界面，负责 UI 和网络通信 |
| **AweSun --mod=service** | `/Applications/AweSun.app/Contents/Helpers/AweSun` | root | 后台服务（LaunchDaemon） |
| **AweSun_Helper** | `/Library/Application Support/Oray/AweSun/AweSun.app/ Contents/Helpers/AweSun_Helper` | root | 特权助手（LaunchDaemon，屏幕捕获） |
| **desktopagent** | 通过 `com.oray.awesun.desktopagent` 管理 | 用户 | 桌面代理，负责屏幕流传输 |

## 诊断流程

### 第一步：确认向日葵进程是否在运行

```bash
# 查看所有向日葵相关进程
ps aux | grep -iE "AweSun|Sunlogin" | grep -v grep
```

**正常状态**（应有 3 个进程）：
```
caofei  PID  ... /Applications/AweSun.app/Contents/MacOS/AweSun          # GUI 主进程
root    PID  ... /Applications/AweSun.app/Contents/Helpers/AweSun --mod=service  # 服务
root    PID  ... /Library/.../AweSun_Helper -m server                     # 特权助手
```

如果缺少任意一个进程，向日葵功能将不完整。

### 第二步：检查网络连接（核心诊断）

向日葵进程"假活"是 macOS 版的常见问题——**进程在运行但网络层已崩溃**。

```bash
# 检查向日葵是否有到 Oray 服务器的网络连接
/usr/sbin/lsof -iTCP -sTCP:ESTABLISHED -P 2>/dev/null | grep -iE "awe|sun|oray"
```

**健康状态**——应有 4~6 条到 Oray/阿里云服务器的已建立连接：
```
AweSun  TCP  bogon:64090->47.97.194.30:https (ESTABLISHED)
AweSun  TCP  bogon:64174->121.199.35.89:https (ESTABLISHED)
AweSun  TCP  bogon:64175->121.199.35.89:https (ESTABLISHED)
AweSun  TCP  bogon:63990->47.97.113.168:https (ESTABLISHED)
AweSun  TCP  bogon:64196->60.28.220.199:https (ESTABLISHED)
```

**异常状态**——输出为空或只有 1~2 条。此时尽管进程在运行，向日葵云端服务器收不到这台设备的信令，远程端会显示"设备离线"或连接请求无法送达。

### 第三步：检查 macOS 权限（如果卡在"登录远程桌面"）

```bash
# 检查 AweSun 是否已授权 Screen Recording
sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client, service, auth_value FROM access \
   WHERE (client LIKE '%AweSun%' OR client LIKE '%Sunlogin%' OR client LIKE '%oray%') \
   AND service='kTCCServiceScreenCapture';"
```

返回空则说明**屏幕录制权限未授权**，需要手动前往：
- **系统设置 → 隐私与安全性 → 屏幕录制** → 确保 AweSun 已勾选
- **系统设置 → 隐私与安全性 → 辅助功能** → 确保 AweSun 已勾选

> macOS 15 (Sequoia) 对隐私权限管理更严格。重启 App、macOS 更新后可能重置权限状态。

## 修复方案

### 方案 A：网络层"假活"——重启 GUI 主进程

当 `lsof` 检查显示无可用的 ESTABLISHED 连接时：

```bash
# 1. 强制杀掉向日葵 GUI 进程
kill $(pgrep -f '/Applications/AweSun.app/Contents/MacOS/AweSun$')

# 2. 确认进程已退出
ps aux | grep -i AweSun | grep -v grep

# 3. 重新启动向日葵
open /Applications/AweSun.app

# 4. 等待 5~10 秒，验证网络连接已恢复
sleep 10
/usr/sbin/lsof -iTCP -sTCP:ESTABLISHED -P 2>/dev/null | grep -iE "awe|sun|oray"
```

出现 4 条以上 `ESTABLISHED` 连接即为恢复。

### 方案 B：卡在"正在登录远程桌面"——重启 desktopagent

当 GUI 重启后远程端能连上但卡在"正在登录远程桌面"不动：

```bash
# 重启向日葵的桌面代理组件
launchctl kickstart -k gui/$(id -u)/com.oray.awesun.desktopagent

# 重启客户端启动服务
launchctl kickstart -k gui/$(id -u)/com.oray.awesun.client.startup

# 验证服务已重启
launchctl list | grep -i oray
```

`desktopagent` 的 PID 变化说明已成功重启。

### 方案 C：完整重启（组合方案）

如果上述单一方案无效，执行完整重启流程：

```bash
# 1. 杀掉所有向日葵进程（包括后台服务）
kill $(pgrep -f 'AweSun') 2>/dev/null
sudo kill $(pgrep -f 'AweSun_Helper') 2>/dev/null || true

# 2. 通过 launchctl 重启 LaunchDaemon
sudo launchctl bootout system/com.oray.awesun.helper 2>/dev/null || true
sudo launchctl bootout system/com.oray.awesun.service 2>/dev/null || true
sleep 2

sudo launchctl bootstrap system /Library/LaunchDaemons/com.oray.awesun.helper.plist 2>/dev/null || true
sudo launchctl bootstrap system /Library/LaunchDaemons/com.oray.awesun.service.plist 2>/dev/null || true
sleep 3

# 3. 重新打开 GUI
open /Applications/AweSun.app

# 4. 重启用户级服务
launchctl kickstart -k gui/$(id -u)/com.oray.awesun.desktopagent
launchctl kickstart -k gui/$(id -u)/com.oray.awesun.client.startup

# 5. 验证
sleep 10
/usr/sbin/lsof -iTCP -sTCP:ESTABLISHED -P 2>/dev/null | grep -iE "awe|sun|oray"
```

> ⚠️ `sudo` 需要终端有 `sudo` 密码输入能力。如无交互式终端，可跳过方案 C 中的 `sudo` 命令，仅执行方案 A+B。

### 方案 D：授予屏幕录制权限

如果修复后远程端能连接但看到的画面是黑屏或冻结，通常是 macOS 隐私权限问题：

```bash
# 打开隐私设置面板（引导用户授权）
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
```

手动操作路径：
1. **系统设置 → 隐私与安全性**
2. **屏幕录制** → 点击锁图标解锁
3. 确保 **AweSun** 已勾选（如不在列表中，点击 `+` 添加 `/Applications/AweSun.app`）
4. **辅助功能** → 同样确保 AweSun 已勾选
5. 重新启动 AweSun

## 预防措施

向日葵在 macOS 上长时间运行后容易网络层僵死，建议：

### 定期重启

```bash
# 创建定时重启脚本
cat > ~/Library/LaunchAgents/com.user.restart-sunflower.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.restart-sunflower</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>kill $(pgrep -f '/Applications/AweSun.app/Contents/MacOS/AweSun$') 2>/dev/null; sleep 3; open /Applications/AweSun.app</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>4</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.user.restart-sunflower.plist
```

这样每天早上 4:00 向日葵会自动重启一次。

### 避免 Mac 休眠

向日葵在 Mac 休眠后会断开连接：

```bash
# 检查当前休眠设置
pmset -g | grep sleep

# 防止系统休眠
sudo pmset -a disablesleep 1

# 或使用 caffeinate 保持唤醒
caffeinate -d &
```

### 监控检查

```bash
# 快速检查向日葵健康状况
if /usr/sbin/lsof -iTCP -sTCP:ESTABLISHED -P 2>/dev/null | grep -qiE "awe.*sun.*ESTABLISHED"; then
    echo "[OK] 向日葵网络连接正常"
else
    echo "[WARN] 向日葵无网络连接，尝试修复..."
    kill $(pgrep -f '/Applications/AweSun.app/Contents/MacOS/AweSun$') 2>/dev/null
    sleep 3
    open /Applications/AweSun.app
fi
```

## 常见问题速查

| 现象 | 最可能原因 | 首选方案 |
|------|-----------|---------|
| 进程在但连不上 | GUI 网络层假活 | 方案 A：重启 GUI |
| 卡在"登录远程桌面" | desktopagent 失活 | 方案 B：重启 desktopagent |
| 连接后黑屏/冻结 | 屏幕录制权限丢失 | 方案 D：重新授权 |
| 远程端显示设备离线 | 网络断开 / 进程崩溃 | 方案 C：完整重启 |
| macOS 升级后无法使用 | 权限被重置 | 方案 D：重新授权 |

## 输出

- 已定位向日葵无法远程连接的根本原因
- 向日葵已恢复与 Oray 服务器的网络连接（4+ 条 ESTABLISHED TCP 连接）
- desktopagent 组件已刷新
- （如需要）macOS 隐私权限已重新授权

## 验证检查

```bash
echo "=== 进程检查 ==="
ps aux | grep -iE "AweSun|Sunlogin" | grep -v grep

echo "=== 网络连接检查 ==="
/usr/sbin/lsof -iTCP -sTCP:ESTABLISHED -P 2>/dev/null | grep -iE "awe|sun|oray"

echo "=== LaunchAgent 检查 ==="
launchctl list | grep -i oray
```

验证标准：
- ✅ 3 个向日葵进程（GUI + service + helper）全部运行
- ✅ 4+ 条到 Oray 服务器的 ESTABLISHED 连接
- ✅ desktopagent PID 为最近启动的时间
- ✅ 从另一台设备能成功远程控制本机
