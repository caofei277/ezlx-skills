# OmO 配置模板

根据用户已有的 Provider 组合，选择对应的配置模板。

> 模板中的模型分配基于"贵的模型干重活、便宜的干杂活"原则。用户可根据实际体验调整。

## 模板一：OpenCode Go + 智谱 + 百炼（三平台完整版）

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  // 主编排：DeepSeek V4 Flash 便宜且强，适合编排调度
  // ultrawork 模式用更强的 GLM-5.1
  "agents": {
    "sisyphus": {
      "model": "opencode-go/deepseek-v4-flash",
      "ultrawork": { "model": "opencode-go/glm-5.1" },
      "fallback_models": [
        "zhipu-coding-plan/glm-5.1",
        "bailian-coding-plan/glm-5",
        "opencode-go/kimi-k2.6"
      ]
    },

    // 深度自主工作：GLM-5.1 最强编程能力
    "hephaestus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": [
        "zhipu-coding-plan/glm-5.1",
        "opencode-go/deepseek-v4-pro"
      ]
    },

    // 规划师：GLM-5 推理强
    "prometheus": {
      "model": "zhipu-coding-plan/glm-5",
      "fallback_models": [
        "opencode-go/glm-5.1",
        "bailian-coding-plan/glm-5"
      ]
    },

    // 执行编排：Kimi K2.6 上下文大
    "atlas": {
      "model": "opencode-go/kimi-k2.6",
      "fallback_models": [
        "opencode-go/glm-5.1",
        "bailian-coding-plan/kimi-k2.5"
      ]
    },

    // 架构咨询：Qwen 3.6 Plus 1M 上下文，适合分析大量代码
    "oracle": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": [
        "opencode-go/qwen3.6-plus",
        "zhipu-coding-plan/glm-5.1"
      ]
    },

    // 文档搜索：Qwen 3.5 Plus 便宜且 1M 上下文
    "librarian": {
      "model": "bailian-coding-plan/qwen3.5-plus",
      "fallback_models": [
        "opencode-go/qwen3.5-plus"
      ]
    },

    // 代码搜索：DeepSeek Flash 快
    "explore": {
      "model": "opencode-go/deepseek-v4-flash",
      "fallback_models": [
        "bailian-coding-plan/qwen3-coder-plus",
        "opencode-go/qwen3.5-plus"
      ]
    },

    // 视觉分析：Kimi K2.6 支持图片输入
    "multimodal-looker": {
      "model": "opencode-go/kimi-k2.6",
      "fallback_models": [
        "opencode-go/kimi-k2.5",
        "bailian-coding-plan/kimi-k2.5"
      ]
    }
  },

  // 按任务类型分配模型
  "categories": {
    "visual-engineering": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": ["opencode-go/qwen3.6-plus"]
    },
    "ultrabrain": {
      "model": "zhipu-coding-plan/glm-5.1",
      "fallback_models": ["opencode-go/glm-5.1", "bailian-coding-plan/glm-5"]
    },
    "deep": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": ["zhipu-coding-plan/glm-5.1", "bailian-coding-plan/glm-5"]
    },
    "artistry": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": ["opencode-go/qwen3.6-plus"]
    },
    "quick": {
      "model": "opencode-go/deepseek-v4-flash",
      "fallback_models": ["bailian-coding-plan/qwen3-coder-plus"]
    },
    "unspecified-low": {
      "model": "opencode-go/deepseek-v4-flash",
      "fallback_models": ["bailian-coding-plan/qwen3.5-plus", "opencode-go/qwen3.5-plus"]
    },
    "unspecified-high": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": ["zhipu-coding-plan/glm-5.1", "opencode-go/kimi-k2.6"]
    },
    "writing": {
      "model": "bailian-coding-plan/qwen3.5-plus",
      "fallback_models": ["opencode-go/qwen3.5-plus"]
    }
  },

  // 运行时回退：额度用完（429）自动切平台
  "runtime_fallback": {
    "enabled": true,
    "retry_on_errors": [429, 500, 502, 503, 504],
    "max_fallback_attempts": 3,
    "cooldown_seconds": 60,
    "notify_on_fallback": true
  },

  // 功能开关
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

## 模板二：OpenCode Go + 百炼（双平台版）

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  "agents": {
    "sisyphus": {
      "model": "opencode-go/deepseek-v4-flash",
      "ultrawork": { "model": "opencode-go/glm-5.1" },
      "fallback_models": [
        "bailian-coding-plan/glm-5",
        "opencode-go/kimi-k2.6"
      ]
    },
    "hephaestus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": ["opencode-go/deepseek-v4-pro"]
    },
    "prometheus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": ["bailian-coding-plan/glm-5"]
    },
    "atlas": {
      "model": "opencode-go/kimi-k2.6",
      "fallback_models": ["bailian-coding-plan/kimi-k2.5"]
    },
    "oracle": {
      "model": "bailian-coding-plan/qwen3.6-plus",
      "fallback_models": ["opencode-go/qwen3.6-plus"]
    },
    "librarian": {
      "model": "bailian-coding-plan/qwen3.5-plus",
      "fallback_models": ["opencode-go/qwen3.5-plus"]
    },
    "explore": {
      "model": "opencode-go/deepseek-v4-flash",
      "fallback_models": ["bailian-coding-plan/qwen3-coder-plus"]
    }
  },

  "categories": {
    "visual-engineering": { "model": "bailian-coding-plan/qwen3.6-plus", "fallback_models": ["opencode-go/qwen3.6-plus"] },
    "ultrabrain": { "model": "opencode-go/glm-5.1", "fallback_models": ["bailian-coding-plan/glm-5"] },
    "deep": { "model": "opencode-go/glm-5.1", "fallback_models": ["bailian-coding-plan/glm-5"] },
    "quick": { "model": "opencode-go/deepseek-v4-flash", "fallback_models": ["bailian-coding-plan/qwen3-coder-plus"] },
    "unspecified-low": { "model": "opencode-go/deepseek-v4-flash" },
    "unspecified-high": { "model": "opencode-go/glm-5.1", "fallback_models": ["opencode-go/kimi-k2.6"] },
    "writing": { "model": "bailian-coding-plan/qwen3.5-plus", "fallback_models": ["opencode-go/qwen3.5-plus"] }
  },

  "runtime_fallback": {
    "enabled": true,
    "retry_on_errors": [429, 500, 502, 503, 504],
    "max_fallback_attempts": 3,
    "cooldown_seconds": 60
  },

  "hashline_edit": true,
  "experimental": { "aggressive_truncation": true, "task_system": true }
}
```

## 模板三：仅 OpenCode Go（单平台版）

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json",

  "agents": {
    "sisyphus": {
      "model": "opencode-go/deepseek-v4-flash",
      "ultrawork": { "model": "opencode-go/glm-5.1" },
      "fallback_models": ["opencode-go/kimi-k2.6", "opencode-go/qwen3.6-plus"]
    },
    "hephaestus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": ["opencode-go/deepseek-v4-pro"]
    },
    "prometheus": {
      "model": "opencode-go/glm-5.1",
      "fallback_models": ["opencode-go/kimi-k2.6"]
    },
    "atlas": {
      "model": "opencode-go/kimi-k2.6",
      "fallback_models": ["opencode-go/glm-5.1"]
    },
    "oracle": {
      "model": "opencode-go/qwen3.6-plus",
      "fallback_models": ["opencode-go/glm-5.1"]
    },
    "librarian": { "model": "opencode-go/qwen3.5-plus" },
    "explore": { "model": "opencode-go/deepseek-v4-flash" }
  },

  "categories": {
    "visual-engineering": { "model": "opencode-go/qwen3.6-plus" },
    "ultrabrain": { "model": "opencode-go/glm-5.1" },
    "deep": { "model": "opencode-go/glm-5.1" },
    "quick": { "model": "opencode-go/deepseek-v4-flash" },
    "unspecified-low": { "model": "opencode-go/deepseek-v4-flash" },
    "unspecified-high": { "model": "opencode-go/glm-5.1" },
    "writing": { "model": "opencode-go/qwen3.5-plus" }
  },

  "runtime_fallback": {
    "enabled": true,
    "retry_on_errors": [429, 500, 502, 503, 504]
  },

  "hashline_edit": true,
  "experimental": { "aggressive_truncation": true, "task_system": true }
}
```

## 模型选择原则

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 编排调度（Sisyphus） | DeepSeek V4 Flash | 快、便宜、够用 |
| 复杂推理（ultrawork/ultrabrain） | GLM-5.1 | 最强编程能力 |
| 前端/UI（visual-engineering） | Qwen 3.6 Plus | 视觉理解强，1M 上下文 |
| 搜索/快速任务（quick/explore） | DeepSeek V4 Flash | 快且便宜 |
| 文档/写作（writing/librarian） | Qwen 3.5 Plus | 1M 上下文，便宜 |
| 大上下文任务（atlas/oracle） | Kimi K2.6 / Qwen 3.6 Plus | 上下文窗口大 |
| 跨平台备份 | 同款模型不同前缀 | 额度用完自动切换 |
