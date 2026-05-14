# Provider 配置模板

## OpenCode Go（内置提供商，推荐）

> ⚠️ **不要手动配置！** OpenCode Go 是官方内置提供商，已预配置所有参数。在 TUI 中使用 `/connect` 命令添加。

| 模型 ID | 名称 | Context | Output | Thinking | 输入模态 |
|---------|------|---------|--------|----------|---------|
| `opencode-go/glm-5` | GLM-5 | 200K | 128K | enabled | text |
| `opencode-go/glm-5.1` | GLM-5.1 | 200K | 128K | enabled | text |
| `opencode-go/kimi-k2.5` | Kimi K2.5 | 256K | 32K | enabled | text, image |
| `opencode-go/kimi-k2.6` | Kimi K2.6 | 256K | 96K | enabled | text, image |
| `opencode-go/mimo-v2.5` | MiMo-V2.5 | 256K* | 32K* | enabled | text |
| `opencode-go/mimo-v2.5-pro` | MiMo-V2.5-Pro | 256K* | 32K* | enabled | text |
| `opencode-go/minimax-m2.5` | MiniMax M2.5 | 204.8K | 32K | enabled | text |
| `opencode-go/minimax-m2.7` | MiniMax M2.7 | 204.8K | 32K | enabled | text |
| `opencode-go/qwen3.5-plus` | Qwen3.5 Plus | 1M | 64K | enabled | text, image |
| `opencode-go/qwen3.6-plus` | Qwen3.6 Plus | 1M | 64K | enabled | text, image |
| `opencode-go/deepseek-v4-pro` | DeepSeek V4 Pro | 1M | 384K | enabled | text |
| `opencode-go/deepseek-v4-flash` | DeepSeek V4 Flash | 1M | 384K | enabled | text |

*标注 `*` 的为估算值*

### 智能路由说明

OpenCode Go 根据模型自动选择 API 端点：
- **MiniMax 模型** → `/v1/messages`（Anthropic 兼容）
- **Qwen 模型** → `/v1/chat/completions`（Alibaba 兼容）
- **其他模型** → `/v1/chat/completions`（OpenAI 兼容）

### 配置方式

```
opencode → /connect → 选择 "OpenCode Go" → 输入 API Key → /models 验证
```

### 使用限制

| 周期 | 额度 |
|------|------|
| 5小时 | $12 |
| 每周 | $30 |
| 每月 | $60 |

超出后可启用 "Use balance"（消耗 Zen 积分）或切换至免费模型/第三方 Provider。

---

## 智谱 Coding Plan (zhipu-coding-plan)

- **npm SDK**: `@ai-sdk/openai-compatible`
- **baseURL**: `https://open.bigmodel.cn/api/coding/paas/v4`
- **API Key 环境变量**: `ZHIPU_API_KEY`（配置中写 `{env:ZHIPU_API_KEY}`）
- **获取地址**: https://open.bigmodel.cn → Coding Plan 套餐 → API Key 管理
- **密钥格式**: `{API_KEY}.{SECRET_KEY}`（两部分组成）

### 可用模型

| 模型 ID | 名称 | context | output | thinking | 输入模态 |
|---------|------|---------|--------|----------|---------|
| `glm-5` | GLM-5 | 202752 | 131072 | enabled (8192) | text |
| `glm-5-turbo` | GLM-5 Turbo | 202752 | 131072 | 无 | text |
| `glm-4.7` | GLM-4.7 | 202752 | 16384 | enabled (8192) | text |
| `glm-5.1` | GLM-5.1 | 202752 | 131072 | enabled (8192) | text |

### Provider 配置片段

```json
{
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
      "glm-5-turbo": {
        "name": "GLM-5 Turbo",
        "modalities": { "input": ["text"], "output": ["text"] },
        "limit": { "context": 202752, "output": 131072 }
      },
      "glm-4.7": {
        "name": "GLM-4.7",
        "modalities": { "input": ["text"], "output": ["text"] },
        "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
        "limit": { "context": 202752, "output": 16384 }
      },
      "glm-5.1": {
        "name": "GLM-5.1",
        "modalities": { "input": ["text"], "output": ["text"] },
        "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
        "limit": { "context": 202752, "output": 131072 }
      }
    }
  }
}
```

---

## 阿里云百炼 Coding Plan (bailian-coding-plan)

- **npm SDK**: `@ai-sdk/anthropic`
- **baseURL**: `https://coding.dashscope.aliyuncs.com/apps/anthropic/v1`
- **API Key 环境变量**: `DASHSCOPE_API_KEY`（配置中写 `{env:DASHSCOPE_API_KEY}`）
- **获取地址**: https://bailian.console.aliyun.com → API Key 管理
- **密钥格式**: `sk-sp-{32位字符}`

### 可用模型

| 模型 ID | 名称 | context | output | thinking | 输入模态 |
|---------|------|---------|--------|----------|---------|
| `qwen3.5-plus` | Qwen3.5 Plus | 1000000 | 65536 | enabled (8192) | text, image |
| `qwen3.6-plus` | Qwen3.6 Plus | 1000000 | 65536 | enabled (8192) | text, image |
| `qwen3-max-2026-01-23` | Qwen3 Max 2026-01-23 | 262144 | 32768 | 无 | text |
| `qwen3-coder-next` | Qwen3 Coder Next | 262144 | 65536 | 无 | text |
| `qwen3-coder-plus` | Qwen3 Coder Plus | 1000000 | 65536 | 无 | text |
| `MiniMax-M2.5` | MiniMax M2.5 | 196608 | 24576 | enabled (8192) | text |
| `glm-5` | GLM-5 | 202752 | 131072 | enabled (8192) | text |
| `glm-4.7` | GLM-4.7 | 202752 | 16384 | enabled (8192) | text |
| `kimi-k2.5` | Kimi K2.5 | 262144 | 32768 | enabled (8192) | text, image |

### Provider 配置片段

```json
{
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
      "qwen3-max-2026-01-23": {
        "name": "Qwen3 Max 2026-01-23",
        "modalities": { "input": ["text"], "output": ["text"] },
        "limit": { "context": 262144, "output": 32768 }
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
        "limit": { "context": 202752, "output": 131072 }
      },
      "glm-4.7": {
        "name": "GLM-4.7",
        "modalities": { "input": ["text"], "output": ["text"] },
        "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
        "limit": { "context": 202752, "output": 16384 }
      },
      "kimi-k2.5": {
        "name": "Kimi K2.5",
        "modalities": { "input": ["text", "image"], "output": ["text"] },
        "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
        "limit": { "context": 262144, "output": 32768 }
      }
    }
  }
}
```
