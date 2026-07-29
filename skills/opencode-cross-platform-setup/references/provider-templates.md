# Provider 配置模板

## OpenCode Zen（免费层，内置）

> OpenCode Zen 提供免费的 DeepSeek V4 Flash Free，无需 API Key，安装 OpenCode 即可使用。

| 模型 ID | 名称 | Context | Output | Thinking | 输入模态 | 费用 |
|---------|------|---------|--------|----------|---------|------|
| `opencode/deepseek-v4-flash-free` | DeepSeek V4 Flash Free | 1M | 384K | enabled | text | **免费** |

### 配置方式

无需配置。在 `opencode.json` 中不添加任何 provider 条目即可使用。

在 OmO 配置中直接引用：
```jsonc
{ "model": "opencode/deepseek-v4-flash-free" }
```

### 注意事项

- Provider 前缀是 `opencode/`，**不是** `opencode-zen/`
- 模型 ID 是 `deepseek-v4-flash-free`，**不是** `deepseek-v4-flash`
- 免费额度用完后可通过 OmO fallback 自动切换到付费模型
- 官方文档：https://opencode.ai/docs/zen/
---
## OpenCode Go（内置提供商）

> ⚠️ **不要手动配置！** OpenCode Go 是官方内置提供商，已预配置所有参数。在 TUI 中使用 `/connect` 命令添加。

| 模型 ID | 名称 | Context | Output | Thinking | 输入模态 |
|---------|------|---------|--------|----------|---------|
| `opencode-go/glm-5` | GLM-5 | 200K | 128K | enabled | text |
| `opencode-go/glm-5.2` | GLM-5.2 | 1M | 128K | enabled | text |
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

---

## 智谱 Coding Plan (zhipu-coding-plan)

- **npm SDK**: `@ai-sdk/openai-compatible`
- **baseURL**: `https://open.bigmodel.cn/api/coding/paas/v4`
- **API Key 环境变量**: `ZHIPU_API_KEY`（配置中写 `{env:ZHIPU_API_KEY}`）
- **获取地址**: https://open.bigmodel.cn → Coding Plan 套餐 → API Key 管理
- **密钥格式**: `{API_KEY}.{SECRET_KEY}`（两部分组成）

> **GLM-5.2 说明**：1M 上下文，128K 最大输出（配置中使用 131072）。Provider 文档可能滞后，使用当前可用的提供商模型 ID。GLM-5.2 和 GLM-5-Turbo 为高阶模型，高峰期（14:00-18:00 UTC+8）消耗 3 倍额度，非高峰期消耗 2 倍额度。

### 可用模型

| 模型 ID | 名称 | context | output | thinking | 输入模态 |
|---------|------|---------|--------|----------|---------|
| `glm-5.2` | GLM-5.2 | 1000000 | 131072 | enabled (8192) | text |
| `glm-5-turbo` | GLM-5 Turbo | 200000 | 128000 | 无 | text |
| `glm-4.7` | GLM-4.7 | 200000 | 128000 | enabled (8192) | text |
| `glm-4.5-air` | GLM-4.5-Air | 200000 | 128000 | 无 | text |

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
      "glm-5.2": {
        "name": "GLM-5.2",
        "modalities": { "input": ["text"], "output": ["text"] },
        "options": { "thinking": { "type": "enabled", "budgetTokens": 8192 } },
        "limit": { "context": 1000000, "output": 131072 }
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
| `glm-5` | GLM-5 | 200000 | 128000 | enabled (8192) | text |
| `glm-4.7` | GLM-4.7 | 200000 | 128000 | enabled (8192) | text |
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
  }
}
```

---

## 火山方舟 Coding Plan (volcengine-plan)

- **npm SDK**: `@ai-sdk/openai-compatible`
- **baseURL**: `https://ark.cn-beijing.volces.com/api/coding/v3`
- **API Key 环境变量**: `ARK_API_KEY`（配置中写 `{env:ARK_API_KEY}`）
- **获取地址**: https://console.volcengine.com/coding_plan → 套餐 → API Key 管理
- **注意**: 请勿使用 `https://ark.cn-beijing.volces.com/api/v3` 作为 baseURL，该地址不会消耗 Coding Plan 额度，会产生额外费用

> **GLM-5.2 说明**：1M 上下文，128K 最大输出（配置中使用 131072）。Provider 文档可能滞后，使用当前可用的提供商模型 ID。GLM-5.2 和 GLM-5-Turbo 为高阶模型，高峰期（14:00-18:00 UTC+8）消耗 3 倍额度，非高峰期消耗 2 倍额度。

### 模型配置说明

火山方舟支持两种方式配置模型：

1. **配置 Model Name（配置文件指定）**：在 `models` 节点中指定具体模型 ID，可实时切换
2. **配置 `ark-code-latest`（控制台管理）**：使用 `ark-code-latest` 模型 ID，由控制台动态管理实际使用的模型

> Model Name 支持全小写格式，也支持直接复制开通管理页面中的模型名称。

### 可用模型

| 模型 ID | 名称 | context | output | thinking | 输入模态 |
|---------|------|---------|--------|----------|---------|
| `ark-code-latest` | Ark Code Latest | 256000 | 4096 | 无 | text, image |
| `doubao-seed-code` | 豆包 Seed Code | 256000 | 4096 | 无 | text, image |
| `doubao-seed-2.0-code` | 豆包 Seed 2.0 Code | 256000 | 4096 | 无 | text, image |
| `doubao-seed-2.0-pro` | 豆包 Seed 2.0 Pro | 256000 | 4096 | 无 | text, image |
| `doubao-seed-2.0-lite` | 豆包 Seed 2.0 Lite | 256000 | 4096 | 无 | text, image |
| `deepseek-v4-flash` | DeepSeek V4 Flash | 1024000 | 4096 | 无 | text |
| `deepseek-v4-pro` | DeepSeek V4 Pro | 1024000 | 4096 | 无 | text |
| `glm-5.2` | GLM-5.2 | 1000000 | 131072 | enabled (8192) | text |
| `minimax-m2.7` | MiniMax M2.7 | 200000 | 4096 | 无 | text |
| `minimax-m3` | MiniMax M3 | 512000 | 4096 | 无 | text, image |
| `kimi-k2.6` | Kimi K2.6 | 256000 | 4096 | 无 | text, image |

### Provider 配置片段

```json
{
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
      "glm-5.2": {
        "name": "glm-5.2",
        "limit": { "context": 1000000, "output": 131072 },
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
```

### 注意事项

- `volcengine-plan.models` 节点下有两处（对象键、`name` 字段）需替换为同一 Model Name，切勿遗漏
- 若需开启模型图片理解能力，需在模型配置节点下新增 `"modalities": {"input": ["text", "image"], "output": ["text"]}`
- Model Name 不支持配置为 `Auto`，如需使用请通过控制台切换该模式
- 火山方舟也兼容 Anthropic 接口协议，使用 baseURL: `https://ark.cn-beijing.volces.com/api/coding`（需配合 `@ai-sdk/anthropic` SDK）
