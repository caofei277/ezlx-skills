# 完整配置模板（多 Provider + MCP）

以下模板同时配置智谱和阿里云百炼两个 Provider，并包含 MCP Puppeteer。

使用时需设置环境变量：
- `ZHIPU_API_KEY` — 智谱 API Key
- `DASHSCOPE_API_KEY` — 阿里云百炼 API Key

环境变量持久化方式：
- macOS/Linux：将 `export ZHIPU_API_KEY="xxx"` 写入 `~/.bashrc` 或 `~/.zshrc`
- Windows PowerShell：`[Environment]::SetEnvironmentVariable("ZHIPU_API_KEY", "xxx", "User")`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "zhipu-coding-plan/glm-5.1",
  "provider": {
    "bailian-coding-plan": {
      "npm": "@ai-sdk/anthropic",
      "name": "阿里云 Coding Plan",
      "options": {
        "baseURL": "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1",
        "apiKey": "{env:DASHSCOPE_API_KEY}"
      },
      "models": {
        "qwen3.5-plus": {
          "name": "Qwen3.5 Plus",
          "modalities": { "input": ["text", "image"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
          "limit": { "context": 1000000, "output": 65536 }
        },
        "qwen3-coder-next": {
          "name": "Qwen3 Coder Next",
          "modalities": { "input": ["text"], "output": ["text"] },
          "limit": { "context": 262144, "output": 65536 }
        },
        "glm-5": {
          "name": "GLM-5",
          "modalities": { "input": ["text"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
          "limit": { "context": 202752, "output": 131072 }
        }
      }
    },
    "zhipu-coding-plan": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "智谱 Coding Plan",
      "options": {
        "baseURL": "https://open.bigmodel.cn/api/coding/paas/v4",
        "apiKey": "{env:ZHIPU_API_KEY}"
      },
      "models": {
        "glm-5": {
          "name": "GLM-5",
          "modalities": { "input": ["text"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
          "limit": { "context": 202752, "output": 131072 }
        },
        "glm-5.1": {
          "name": "GLM-5.1",
          "modalities": { "input": ["text"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
          "limit": { "context": 202752, "output": 131072 }
        }
      }
    }
  },
  "mcp": {
    "puppeteer": {
      "type": "local",
      "command": ["${NPX_CMD}", "-y", "@modelcontextprotocol/server-puppeteer"],
      "enabled": true
    }
  }
}
```

> `${NPX_CMD}` 为占位符，生成时替换为：
> - Windows: `C:\\Program Files\\nodejs\\npx.cmd`
> - macOS/Linux: `npx`

## 切换默认模型

修改顶层 `model` 字段即可：

| 值 | 说明 |
|----|------|
| `zhipu-coding-plan/glm-5.1` | 智谱 GLM-5.1（默认） |
| `zhipu-coding-plan/glm-5` | 智谱 GLM-5 |
| `bailian-coding-plan/qwen3.5-plus` | 百炼 Qwen3.5 Plus |
| `bailian-coding-plan/glm-5` | 百炼 GLM-5 |

运行时临时切换：`opencode -m <provider>/<model>`
