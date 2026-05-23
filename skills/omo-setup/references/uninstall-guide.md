# OmO 无损卸载指南

> **核心原则**：只移除 OmO 相关内容，**不动**用户原有的 `provider`、`mcp` 等配置。

## 卸载步骤

### 步骤 1：备份当前配置（可选但推荐）

```bash
# Windows
copy "%USERPROFILE%\.config\opencode\opencode.json" "%USERPROFILE%\.config\opencode\opencode.json.bak"

# Mac/Linux
cp ~/.config/opencode/opencode.json ~/.config/opencode/opencode.json.bak
```

### 步骤 2：移除插件注册

打开 `opencode.json`，找到 `plugin` 数组，删除 `"oh-my-openagent"` 和 `"oh-my-opencode"` 条目。

**卸载前**：
```json
{
  "plugin": ["oh-my-openagent"],
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

### 步骤 3：删除 OmO 配置文件

```bash
# 用户级配置
# Windows
del "%USERPROFILE%\.config\opencode\oh-my-openagent.jsonc" 2>nul
del "%USERPROFILE%\.config\opencode\oh-my-openagent.json" 2>nul
del "%USERPROFILE%\.config\opencode\oh-my-opencode.jsonc" 2>nul
del "%USERPROFILE%\.config\opencode\oh-my-opencode.json" 2>nul

# Mac/Linux
rm -f ~/.config/opencode/oh-my-openagent.jsonc
rm -f ~/.config/opencode/oh-my-openagent.json
rm -f ~/.config/opencode/oh-my-opencode.jsonc
rm -f ~/.config/opencode/oh-my-opencode.json
```

### 步骤 4：删除项目级 OmO 配置（可选）

如果项目目录下有 OmO 相关文件：

```bash
rm -f .opencode/oh-my-openagent.jsonc
rm -f .opencode/oh-my-openagent.json
rm -f .opencode/oh-my-opencode.jsonc
rm -f .opencode/oh-my-opencode.json
```

### 步骤 5：删除 OmO 工作目录（可选）

```bash
rm -rf .omo/
```

> `.omo/` 目录包含 OmO 运行时状态（计划、任务、笔记等）。如果不需要保留这些数据，可以删除。

### 步骤 6：验证卸载

```bash
opencode --version
```

确认输出中**不再包含**任何 OmO 相关信息。

启动 OpenCode：

```bash
opencode
```

确认：
1. 按 **Tab** 恢复为 **Plan / Build** 切换（不再是 Sisyphus / Hephaestus 等）
2. `/models` 仍然显示用户原有的 Provider 模型（百炼、智谱、OpenCode Go 等）

**判据**：Tab 恢复 Plan/Build，模型列表完整，Provider 配置未受影响。

## 卸载后不会丢失的内容

| 内容 | 是否保留 |
|------|---------|
| `opencode.json` 中的 `provider` 配置 | ✅ 保留 |
| `opencode.json` 中的 `mcp` 配置 | ✅ 保留 |
| `opencode.json` 中的 `model` 默认模型设置 | ✅ 保留 |
| `/connect` 认证的 API Key | ✅ 保留（在 `~/.local/share/opencode/auth.json`） |
| OmO 生成的计划文件（`.omo/plans/`） | ❌ 随 `.omo/` 删除（步骤 5） |
| OmO 的工作状态 | ❌ 随 `.omo/` 删除 |

## 回滚到备份

如果卸载后出现问题，恢复备份：

```bash
# Windows
copy "%USERPROFILE%\.config\opencode\opencode.json.bak" "%USERPROFILE%\.config\opencode\opencode.json"

# Mac/Linux
cp ~/.config/opencode/opencode.json.bak ~/.config/opencode/opencode.json
```

## 重新安装

如果卸载后想重新使用 OmO，重新执行 `omo-setup` skill 即可。
