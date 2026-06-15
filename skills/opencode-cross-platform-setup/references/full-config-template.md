# 完整配置模板（多 Provider + MCP）

> **关于 OpenCode Go**：OpenCode Go 是内置提供商，通过 TUI 内的 `/connect` 命令配置，无需在配置文件中手动编写。以下模板仅用于第三方 Provider（阿里云百炼 + 智谱 + 火山方舟）。

> **关于 OpenCode Zen**：OpenCode Zen 提供免费的 DeepSeek V4 Flash Free，无需配置 Provider。在 OmO 中使用 `opencode/deepseek-v4-flash-free` 引用。

> **智谱 Pro 成本提醒**：GLM-5.1 和 GLM-5-Turbo 高峰期（14:00-18:00 UTC+8）消耗 3 倍额度，非高峰期消耗 2 倍（限时福利：6月底前非高峰仅 1 倍）。GLM-4.7 固定 1 倍消耗。日常开发优先使用 GLM-4.7 和 DeepSeek Free。

同时配置智谱和阿里云百炼两个 Provider，并包含 MCP Puppeteer。

使用时需设置环境变量：
- `ZHIPU_API_KEY` — 智谱 API Key
- `DASHSCOPE_API_KEY` — 阿里云百炼 API Key
- `ARK_API_KEY` — 火山方舟 API Key（如使用 volcengine-plan）

环境变量持久化方式：
- macOS/Linux：将 `export ZHIPU_API_KEY="xxx"` 写入 `~/.bashrc` 或 `~/.zshrc`
- Windows PowerShell：`[Environment]::SetEnvironmentVariable("ZHIPU_API_KEY", "xxx", "User")`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode-go/deepseek-v4-flash",
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
        "qwen3.6-plus": {
          "name": "Qwen3.6 Plus",
          "modalities": { "input": ["text", "image"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
          "limit": { "context": 1000000, "output": 65536 }
        },
        "qwen3-coder-next": {
          "name": "Qwen3 Coder Next",
          "modalities": { "input": ["text"], "output": ["text"] },
          "limit": { "context": 262144, "output": 65536 }
        },
        "qwen3-coder-plus": {
          "name": "Qwen3 Coder Plus",
          "modalities": { "input": ["text"], "output": ["text"] },
          "limit": { "context": 1000000, "output": 65536 }
        },
        "qwen3-max-2026-01-23": {
          "name": "Qwen3 Max 2026-01-23",
          "modalities": { "input": ["text"], "output": ["text"] },
          "limit": { "context": 262144, "output": 32768 }
        },
        "MiniMax-M2.5": {
          "name": "MiniMax M2.5",
          "modalities": { "input": ["text"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
          "limit": { "context": 196608, "output": 24576 }
        },
        "glm-5": {
          "name": "GLM-5",
          "modalities": { "input": ["text"], "output": ["text"] },
          "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
"limit": { "context": 200000, "output": 128000 }
         },
         "glm-4.7": {
           "name": "GLM-4.7",
           "modalities": { "input": ["text"], "output": ["text"] },
           "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
           "limit": { "context": 200000, "output": 128000 }
         },
         "kimi-k2.5": {
           "name": "Kimi K2.5",
           "modalities": { "input": ["text", "image"], "output": ["text"] },
           "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
           "limit": { "context": 262144, "output": 32768 }
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
          "glm-5.2": {
            "name": "GLM-5.2",
            "modalities": { "input": ["text"], "output": ["text"] },
            "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
            "limit": { "context": 200000, "output": 128000 }
          },
          "glm-5-turbo": {
            "name": "GLM-5 Turbo",
            "modalities": { "input": ["text"], "output": ["text"] },
            "limit": { "context": 200000, "output": 128000 }
          },
          "glm-4.7": {
            "name": "GLM-4.7",
            "modalities": { "input": ["text"], "output": ["text"] },
            "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
            "limit": { "context": 200000, "output": 128000 }
          },
          "glm-4.5-air": {
            "name": "GLM-4.5-Air",
            "modalities": { "input": ["text"], "output": ["text"] },
            "limit": { "context": 200000, "output": 128000 }
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

---

## 火山方舟 Coding Plan 配置

可通过替换顶层 `model` 和添加 `volcengine-plan` provider 来使用火山方舟。

使用前设置环境变量：
- `ARK_API_KEY` — 火山方舟 API Key

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "volcengine-plan/ark-code-latest",
  "provider": {
    "volcengine-plan": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Volcano Engine",
      "options": {
        "baseURL": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "apiKey": "{env:ARK_API_KEY}"
      },
      "models": {
        "ark-code-latest": {
          "name": "ark-code-latest",
          "limit": { "context": 256000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        },
        "doubao-seed-code": {
          "name": "doubao-seed-code",
          "limit": { "context": 256000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        },
        "doubao-seed-2.0-code": {
          "name": "doubao-seed-2.0-code",
          "limit": { "context": 256000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        },
        "doubao-seed-2.0-pro": {
          "name": "doubao-seed-2.0-pro",
          "limit": { "context": 256000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        },
        "doubao-seed-2.0-lite": {
          "name": "doubao-seed-2.0-lite",
          "limit": { "context": 256000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        },
        "deepseek-v4-flash": {
          "name": "deepseek-v4-flash",
          "limit": { "context": 1024000, "output": 4096 }
        },
        "deepseek-v4-pro": {
          "name": "deepseek-v4-pro",
          "limit": { "context": 1024000, "output": 4096 }
        },
        "glm-5.1": {
          "name": "glm-5.1",
          "limit": { "context": 200000, "output": 4096 },
          "modalities": { "input": ["text"], "output": ["text"] }
        },
        "minimax-m2.7": {
          "name": "minimax-m2.7",
          "limit": { "context": 200000, "output": 4096 },
          "modalities": { "input": ["text"], "output": ["text"] }
        },
        "minimax-m3": {
          "name": "minimax-m3",
          "limit": { "context": 512000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        },
        "kimi-k2.6": {
          "name": "kimi-k2.6",
          "limit": { "context": 256000, "output": 4096 },
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        }
      }
    }
  }
}
```

> 完整模型列表及配置见 [provider-templates.md](references/provider-templates.md#火山方舟-coding-plan-volcengine-plan)。

---

## 切换默认模型

修改顶层 `model` 字段即可。

| 值 | 说明 |
|----|------|
| `opencode/deepseek-v4-flash-free` | OpenCode Zen - DeepSeek V4 Flash Free（**免费**） |
| `opencode-go/deepseek-v4-flash` | OpenCode Go - DeepSeek V4 Flash |
| `opencode-go/deepseek-v4-pro` | OpenCode Go - 长输出 384K |
| `opencode-go/qwen3.6-plus` | OpenCode Go - 1M 上下文 |
| `opencode-go/glm-5.2` | OpenCode Go - 最强编程能力 |
| `bailian-coding-plan/qwen3.5-plus` | 百炼 Qwen3.5 Plus |
| `bailian-coding-plan/glm-5` | 百炼 GLM-5 |
| `zhipu-coding-plan/glm-5.2` | 智谱 GLM-5.2 |
| `zhipu-coding-plan/glm-5-turbo` | 智谱 GLM-5-Turbo |
| `zhipu-coding-plan/glm-4.7` | 智谱 GLM-4.7 |
| `zhipu-coding-plan/glm-4.5-air` | 智谱 GLM-4.5-Air |
| `volcengine-plan/ark-code-latest` | 火山方舟 Ark Code Latest（控制台管理） |
| `volcengine-plan/doubao-seed-code` | 火山方舟 豆包 Seed Code |
| `volcengine-plan/doubao-seed-2.0-code` | 火山方舟 豆包 Seed 2.0 Code |
| `volcengine-plan/doubao-seed-2.0-pro` | 火山方舟 豆包 Seed 2.0 Pro |
| `volcengine-plan/doubao-seed-2.0-lite` | 火山方舟 豆包 Seed 2.0 Lite |
| `volcengine-plan/deepseek-v4-flash` | 火山方舟 DeepSeek V4 Flash（1M 上下文） |
| `volcengine-plan/deepseek-v4-pro` | 火山方舟 DeepSeek V4 Pro（1M 上下文） |
| `volcengine-plan/glm-5.1` | 火山方舟 GLM-5.1 |
| `volcengine-plan/minimax-m2.7` | 火山方舟 MiniMax M2.7 |
| `volcengine-plan/minimax-m3` | 火山方舟 MiniMax M3（512K 上下文） |
| `volcengine-plan/kimi-k2.6` | 火山方舟 Kimi K2.6 |

运行时临时切换：`opencode -m <provider>/<model>`
