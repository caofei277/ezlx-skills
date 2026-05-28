# OmO-slim 无损卸载指南

> **核心原则**：只移除 OmO-slim 相关内容，**不动**用户原有的 `provider`、`mcp` 等配置。

---

## 卸载步骤

### 步骤 1：备份当前配置（可选但推荐）

```bash
# Windows
copy "%USERPROFILE%\.config\opencode\opencode.json" "%USERPROFILE%\.config\opencode\opencode.json.bak"
copy "%USERPROFILE%\.config\opencode\oh-my-opencode-slim.jsonc" "%USERPROFILE%\.config\opencode\oh-my-opencode-slim.jsonc.bak"

# Mac/Linux
cp ~/.config/opencode/opencode.json ~/.config/opencode/opencode.json.bak
cp ~/.config/opencode/oh-my-opencode-slim.jsonc ~/.config/opencode/oh-my-opencode-slim.jsonc.bak
```

### 步骤 2：移除插件注册

打开 `opencode.json`，找到 `plugin` 数组，删除 `"oh-my-opencode-slim"` 条目。

**卸载前**：
```json
{
  "plugin": ["oh-my-opencode-slim"],
  "provider": { ... }
}
```

**卸载后**：
```json
{
  "provider": { ... }
}
```

> 如果 `plugin` 数组删空后变成 `"plugin": []`，可以直接删除整个 `"plugin"` 字段。

如果用户不确定怎么改，可以用以下命令（需要 jq）：

```bash
# Mac/Linux
jq 'del(.plugin)' ~/.config/opencode/opencode.json > /tmp/oc.json && mv /tmp/oc.json ~/.config/opencode/opencode.json

# Windows（PowerShell，手动编辑更可靠）
```

### 步骤 3：删除 OmO-slim 配置文件

```bash
# Windows
del "%USERPROFILE%\.config\opencode\oh-my-opencode-slim.jsonc" 2>nul
del "%USERPROFILE%\.config\opencode\oh-my-opencode-slim.json" 2>nul
del "%USERPROFILE%\.config\opencode\oh-my-opencode-slim.jsonc.bak" 2>nul
del "%USERPROFILE%\.config\opencode\oh-my-opencode-slim.json.bak" 2>nul

# Mac/Linux
rm -f ~/.config/opencode/oh-my-opencode-slim.jsonc
rm -f ~/.config/opencode/oh-my-opencode-slim.json
rm -f ~/.config/opencode/oh-my-opencode-slim.jsonc.bak
rm -f ~/.config/opencode/oh-my-opencode-slim.json.bak
```

### 步骤 4：删除 Skills（可选）

如果安装了捆绑 Skills：

```bash
# Windows
rmdir /s /q "%USERPROFILE%\.config\opencode\skills\simplify" 2>nul
rmdir /s /q "%USERPROFILE%\.config\opencode\skills\codemap" 2>nul
rmdir /s /q "%USERPROFILE%\.config\opencode\skills\clonedeps" 2>nul

# Mac/Linux
rm -rf ~/.config/opencode/skills/simplify
rm -rf ~/.config/opencode/skills/codemap
rm -rf ~/.config/opencode/skills/clonedeps
```

### 步骤 5：删除项目级 OmO-slim 配置（可选）

如果项目目录下有 OmO-slim 相关文件：

```bash
rm -f .opencode/oh-my-opencode-slim.jsonc
rm -f .opencode/oh-my-opencode-slim.json
```

### 步骤 6：删除 OmO-slim 工作目录（可选）

```bash
rm -rf .slim/
```

> `.slim/` 目录包含 OmO-slim 运行时状态（deepwork 计划、克隆依赖等）。如果不需要保留这些数据，可以删除。

### 步骤 7：验证卸载

```bash
opencode --version
```

确认输出中**不再包含**任何 OmO-slim 相关信息。

启动 OpenCode：

```bash
opencode
```

确认：
1. 按 **Tab** 切换恢复为只有 Build / Plan 等 OpenCode 内置 Agent（不再有 Orchestrator / Council）
2. `/models` 仍然显示用户原有的 Provider 模型

**判据**：Agent 切换恢复正常，模型列表完整，Provider 配置未受影响。

---

## 卸载后不会丢失的内容

| 内容 | 是否保留 |
|------|---------|
| `opencode.json` 中的 `provider` 配置 | ✅ 保留 |
| `opencode.json` 中的 `mcp` 配置 | ✅ 保留 |
| `opencode.json` 中的 `model` 默认模型设置 | ✅ 保留 |
| `/connect` 认证的 API Key | ✅ 保留（在 `~/.local/share/opencode/auth.json`） |
| OmO-slim 生成的计划文件（`.slim/deepwork/`） | ❌ 随 `.slim/` 删除（步骤 6） |
| OmO-slim 的克隆依赖（`.slim/clonedeps/`） | ❌ 随 `.slim/` 删除（步骤 6） |
| OmO-slim 的工作状态 | ❌ 随 `.slim/` 删除 |

---

## 回滚到备份

如果卸载后出现问题，恢复备份：

```bash
# Windows
copy "%USERPROFILE%\.config\opencode\opencode.json.bak" "%USERPROFILE%\.config\opencode\opencode.json"

# Mac/Linux
cp ~/.config/opencode/opencode.json.bak ~/.config/opencode/opencode.json
```

---

## 重新安装

如果卸载后想重新使用 OmO-slim，重新执行安装流程：

```bash
bunx oh-my-opencode-slim@latest install --no-tui --skills=yes --preset=opencode-go
```

---

## 常见卸载问题

### Q: 卸载后 Tab 没有 Agent 切换？

**正常现象**：卸载 OmO-slim 后 Tab 切换会恢复为 OpenCode 内置的 Plan / Build 等通用 Agent。如果连这些都没有：

**检查**：
1. `opencode.json` 中 `plugin` 数组是否已清空
2. 重启 OpenCode

### Q: 卸载后模型列表消失？

**检查**：
- Provider 配置是否完整
- 运行 `opencode auth status` 检查认证状态

### Q: 卸载后配置文件损坏？

**恢复备份**：
```bash
cp ~/.config/opencode/opencode.json.bak ~/.config/opencode/opencode.json
```

---

## 配置文件路径汇总

| 平台 | 配置文件路径 |
|------|-------------|
| Windows | `%USERPROFILE%\.config\opencode\` |
| Mac/Linux | `~/.config/opencode/` |

| 文件 | 说明 |
|------|------|
| `opencode.json` | OpenCode 主配置（provider、plugin） |
| `oh-my-opencode-slim.jsonc` | OmO-slim 配置（preset、agents） |
| `auth.json` | API Key 认证信息（在 `~/.local/share/opencode/`） |
| `skills/` | Skills 目录 |

---

## 安全提示

- **不要删除 `provider` 配置**：卸载只移除 plugin 和 OmO-slim 配置
- **不要删除 `auth.json`**：API Key 在认证文件中，卸载不会影响
- **备份重要**：卸载前备份 `opencode.json`，以防意外