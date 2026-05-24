# OmO 配置模板

根据用户已有的 Provider 组合，选择对应的配置模板。

> 模板中的模型分配基于"贵的模型干重活、便宜的干杂活"原则。用户可根据实际体验调整。

## 模型分层与成本说明

| 层级 | 模型 | 平台 | 成本 | 适用场景 |
|------|------|------|------|----------|
| T0 (免费) | DeepSeek V4 Flash Free | OpenCode Zen | 免费 | 编排调度、快速任务、搜索 |
| T1 (低) | DeepSeek V4 Flash/Pro | OpenCode Go | 低 | 中等任务、备选 |
| T2 (中) | GLM-5, Qwen 3.6 Plus, GLM-5 Turbo | 百炼/智谱 | 中等 | 规划、审查、前端/UI |
| T3 (高) | GLM-5.1 | 智谱/OpenCode Go | 高 | 复杂推理、深度自主 |

**关键原则**：Fallback 链必须以同级或更低级模型结尾，绝不升级回退（成本护栏）。

---

## 模板一：四平台完整版（OpenCode Zen + OpenCode Go + 智谱 + 百炼）

完整 12 Agent、8 Category、4 Provider 配置。适合已开通全部平台的用户。

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  // ===== Agents 配置 =====
  "agents": {
    // 主编排：免费 Flash，ultrawork 用最强 GLM-5.1
    "sisyphus": {
      "model": "opencode/deepseek-v4-flash-free",
      "ultrawork": { "model": "zhipu-coding-plan/glm-5.1" },
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "opencode-go/deepseek-v4-pro",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 深度自主工作：最强编程能力
    "hephaestus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": [
        "zhipu-coding-plan/glm-5.1",
        "zhipu-coding-plan/glm-5-turbo",
        "bailian-coding-plan/glm-5"
      ]
    },

    // 规划师：规划不需要最强模型
    "prometheus": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/glm-5",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 执行编排
    "atlas": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "zhipu-coding-plan/glm-5-turbo",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 审查评估：GLM-5 Turbo 专精评审
    "momus": {
      "model": "zhipu-coding-plan/glm-5-turbo",
      "fallback_models": [
        "bailian-coding-plan/glm-5",
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 架构咨询
    "oracle": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "zhipu-coding-plan/glm-5-turbo",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 规划执行：与 prometheus 同级
    "metis": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/qwen3.5-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 视觉分析
    "multimodal-looker": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "bailian-coding-plan/kimi-k2.5",
        "bailian-coding-plan/qwen3.5-plus"
      ]
    },

    // 文档搜索：免费 Flash
    "librarian": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3-coder-plus"
      ]
    },

    // 代码搜索：免费 Flash
    "explore": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3-coder-plus"
      ]
    },

    // Sisyphus 备用：category 驱动时的备份
    "sisyphus-junior": {
      "model": "opencode-go/deepseek-v4-pro",
      "fallback_models": [
        "opencode/deepseek-v4-flash-free",
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    }
  },

  // ===== Categories 配置 =====
  "categories": {
    // 复杂推理
    "ultrabrain": {
      "model": "zhipu-coding-plan/glm-5.1",
      "fallback_models": [
        "opencode-go/glm-5.1",
        "bailian-coding-plan/glm-5"
      ]
    },

    // 深度自主
    "deep": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "zhipu-coding-plan/glm-5-turbo",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 高优先级未指定
    "unspecified-high": {
      "model": "zhipu-coding-plan/glm-5-turbo",
      "fallback_models": [
        "bailian-coding-plan/glm-5",
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 前端/视觉工程
    "visual-engineering": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/kimi-k2.5",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 艺术/UI
    "artistry": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/kimi-k2.5",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 写作
    "writing": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/qwen3.5-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 快速任务：免费 Flash
    "quick": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3-coder-plus"
      ]
    },

    // 低优先级未指定
    "unspecified-low": {
      "model": "opencode-go/deepseek-v4-pro",
      "fallback_models": [
        "opencode/deepseek-v4-flash-free",
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    }
  },

  // ===== 运行时回退 =====
  // 400 包含上下文溢出场景
  "runtime_fallback": {
    "enabled": true,
    "retry_on_errors": [400, 429, 500, 502, 503, 504],
    "max_fallback_attempts": 3,
    "cooldown_seconds": 60,
    "notify_on_fallback": true
  },

  // ===== 功能开关 =====
  "hashline_edit": true,
  "sisyphus_agent": {
    "planner_enabled": true,
    "replace_plan": true
  },
  "notification": { "force_enable": true },
  "experimental": {
    "aggressive_truncation": true,
    "task_system": true
  }
}
```

---

## 模板二：三平台版（OpenCode Zen + OpenCode Go + 百炼，无智谱）

适配未开通智谱平台的用户。将智谱模型替换为百炼/OpenCode Go 同级模型。

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  // ===== Agents 配置 =====
  "agents": {
    // 主编排：免费 Flash，ultrawork 用 OpenCode Go GLM-5.1
    "sisyphus": {
      "model": "opencode/deepseek-v4-flash-free",
      "ultrawork": { "model": "opencode-go/glm-5.1" },
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "opencode-go/deepseek-v4-pro",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 深度自主工作
    "hephaestus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": [
        "bailian-coding-plan/glm-5",
        "opencode-go/qwen3.6-plus"
      ]
    },

    // 规划师
    "prometheus": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/glm-5",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 执行编排
    "atlas": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 审查评估：无智谱时用百炼 GLM-5
    "momus": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 架构咨询
    "oracle": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 规划执行
    "metis": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/qwen3.5-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 视觉分析
    "multimodal-looker": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "bailian-coding-plan/kimi-k2.5",
        "bailian-coding-plan/qwen3.5-plus"
      ]
    },

    // 文档搜索：免费 Flash
    "librarian": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3-coder-plus"
      ]
    },

    // 代码搜索：免费 Flash
    "explore": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3-coder-plus"
      ]
    },

    // Sisyphus 备用
    "sisyphus-junior": {
      "model": "opencode-go/deepseek-v4-pro",
      "fallback_models": [
        "opencode/deepseek-v4-flash-free",
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    }
  },

  // ===== Categories 配置 =====
  "categories": {
    // 复杂推理：无智谱时用 OpenCode Go GLM-5.1
    "ultrabrain": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": [
        "bailian-coding-plan/glm-5",
        "opencode-go/qwen3.6-plus"
      ]
    },

    // 深度自主
    "deep": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 高优先级未指定：无智谱时用百炼 GLM-5
    "unspecified-high": {
      "model": "bailian-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    },

    // 前端/视觉工程
    "visual-engineering": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/kimi-k2.5",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 艺术/UI
    "artistry": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/kimi-k2.5",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 写作
    "writing": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "bailian-coding-plan/qwen3.5-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 快速任务：免费 Flash
    "quick": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3-coder-plus"
      ]
    },

    // 低优先级未指定
    "unspecified-low": {
      "model": "opencode-go/deepseek-v4-pro",
      "fallback_models": [
        "opencode/deepseek-v4-flash-free",
        "opencode-go/deepseek-v4-flash",
        "bailian-coding-plan/qwen3.6-plus"
      ]
    }
  },

  // ===== 运行时回退 =====
  "runtime_fallback": {
    "enabled": true,
    "retry_on_errors": [400, 429, 500, 502, 503, 504],
    "max_fallback_attempts": 3,
    "cooldown_seconds": 60,
    "notify_on_fallback": true
  },

  // ===== 功能开关 =====
  "hashline_edit": true,
  "sisyphus_agent": {
    "planner_enabled": true,
    "replace_plan": true
  },
  "notification": { "force_enable": true },
  "experimental": {
    "aggressive_truncation": true,
    "task_system": true
  }
}
```

---

## 模板三：双平台版（OpenCode Zen + OpenCode Go，无智谱无百炼）

仅使用 OpenCode Zen 免费层 + OpenCode Go 付费层。适合只开通 OpenCode 的用户。

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  // ===== Agents 配置 =====
  "agents": {
    // 主编排：免费 Flash，ultrawork 用 OpenCode Go GLM-5.1
    "sisyphus": {
      "model": "opencode/deepseek-v4-flash-free",
      "ultrawork": { "model": "opencode-go/glm-5.1" },
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "opencode-go/deepseek-v4-pro",
        "opencode-go/qwen3.6-plus"
      ]
    },

    // 深度自主工作
    "hephaestus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 规划师
    "prometheus": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/glm-5",
        "opencode-go/deepseek-v4-pro",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 执行编排
    "atlas": {
      "model": "opencode-go/glm-5",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 审查评估
    "momus": {
      "model": "opencode-go/glm-5",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 架构咨询
    "oracle": {
      "model": "opencode-go/glm-5",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 规划执行
    "metis": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.5-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 视觉分析
    "multimodal-looker": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/kimi-k2.5",
        "opencode-go/qwen3.5-plus"
      ]
    },

    // 文档搜索：免费 Flash
    "librarian": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "opencode-go/qwen3-coder-plus"
      ]
    },

    // 代码搜索：免费 Flash
    "explore": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "opencode-go/qwen3-coder-plus"
      ]
    },

    // Sisyphus 备用
    "sisyphus-junior": {
      "model": "opencode-go/deepseek-v4-pro",
      "fallback_models": [
        "opencode/deepseek-v4-flash-free",
        "opencode-go/deepseek-v4-flash",
        "opencode-go/qwen3.6-plus"
      ]
    }
  },

  // ===== Categories 配置 =====
  "categories": {
    // 复杂推理
    "ultrabrain": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 深度自主
    "deep": {
      "model": "opencode-go/glm-5",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 高优先级未指定
    "unspecified-high": {
      "model": "opencode-go/glm-5",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 前端/视觉工程
    "visual-engineering": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/kimi-k2.5",
        "opencode-go/qwen3.5-plus",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 艺术/UI
    "artistry": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/kimi-k2.5",
        "opencode-go/qwen3.5-plus",
        "opencode/deepseek-v4-flash-free"
      ]
    },

    // 写作
    "writing": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.5-plus",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 快速任务：免费 Flash
    "quick": {
      "model": "opencode/deepseek-v4-flash-free",
      "fallback_models": [
        "opencode-go/deepseek-v4-flash",
        "opencode-go/qwen3-coder-plus"
      ]
    },

    // 低优先级未指定
    "unspecified-low": {
      "model": "opencode-go/deepseek-v4-pro",
      "fallback_models": [
        "opencode/deepseek-v4-flash-free",
        "opencode-go/deepseek-v4-flash",
        "opencode-go/qwen3.6-plus"
      ]
    }
  },

  // ===== 运行时回退 =====
  "runtime_fallback": {
    "enabled": true,
    "retry_on_errors": [400, 429, 500, 502, 503, 504],
    "max_fallback_attempts": 3,
    "cooldown_seconds": 60,
    "notify_on_fallback": true
  },

  // ===== 功能开关 =====
  "hashline_edit": true,
  "sisyphus_agent": {
    "planner_enabled": true,
    "replace_plan": true
  },
  "notification": { "force_enable": true },
  "experimental": {
    "aggressive_truncation": true,
    "task_system": true
  }
}
```

---

## 模型选择原则

| 场景 | 推荐模型 | 平台 | 成本 |
|------|---------|------|------|
| 编排调度 (sisyphus) | DeepSeek V4 Flash Free | OpenCode Zen | 免费 |
| 快速任务 (quick/explore/librarian) | DeepSeek V4 Flash Free | OpenCode Zen | 免费 |
| 中等任务 (unspecified-low) | DeepSeek V4 Pro | OpenCode Go | 低 |
| 规划 (prometheus/metis) | Qwen 3.6 Plus | 百炼 / OpenCode Go | 中等 |
| 复杂自主 (deep) | GLM-5 | 百炼 / OpenCode Go | 中等 |
| 审查评估 (momus/unspecified-high) | GLM-5 Turbo | 智谱 | 中等 |
| 架构咨询 (oracle) | GLM-5 | 百炼 / OpenCode Go | 中等 |
| 前端/UI/视觉 (visual-engineering/artistry) | Qwen 3.6 Plus | 百炼 / OpenCode Go | 中等 |
| 写作 (writing) | Qwen 3.6 Plus | 百炼 / OpenCode Go | 中等 |
| 复杂推理 (ultrabrain/ultrawork) | GLM-5.1 | 智谱 / OpenCode Go | 高 |

### Fallback 链设计原则

1. **成本护栏**：Fallback 链必须以同级或更低级模型结尾，绝不升级回退
2. **跨平台备份**：优先同模型不同平台（如 `bailian-coding-plan/glm-5` → `opencode-go/glm-5`）
3. **免费兜底**：关键 Agent 的 Fallback 链尾部应包含免费模型作为最后防线
4. **错误码覆盖**：`retry_on_errors` 包含 400（上下文溢出）、429（限流）、5xx（服务端错误）

### Provider 前缀对照表

| 前缀 | 平台 | 成本档位 |
|------|------|----------|
| `opencode/` | OpenCode Zen | 免费 |
| `opencode-go/` | OpenCode Go | 付费（低-中） |
| `zhipu-coding-plan/` | 智谱 | 付费（中-高） |
| `bailian-coding-plan/` | 百炼 | 付费（中） |