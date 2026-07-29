# OmO-slim 配置模板

根据用户已有的 Provider 组合，选择对应的配置模板。

> 模板中的模型分配基于"免费做杂活、1倍做主力、高阶做重活"原则。用户可根据实际体验调整。

## 模型分层与成本说明

### 双平台版（Zen 免费 + 智谱 Coding Plan）— 长期稳定

| 层级 | 模型 | 平台 | 成本 | Agent 分配 |
|------|------|------|------|-----------|
| T0 (免费) | DeepSeek V4 Flash Free | OpenCode Zen | **免费** | Explorer, Librarian, Designer, Orchestrator（默认） |
| T1 (主力) | GLM-4.7 | 智谱 | 1倍 | Fixer, Orchestrator（zhipu-std） |
| T2 (快速) | GLM-5-Turbo | 智谱 | 中 | Council, Orchestrator（zhipu-fast） |
| T3 (高阶) | GLM-5.2 | 智谱 | ⚠️高峰3倍/非高峰2倍 | Oracle, Orchestrator（zhipu-full） |

> **智谱成本提醒**：GLM-5.2 高峰期（14:00-18:00 UTC+8）消耗 3 倍额度，非高峰期消耗 2 倍。GLM-4.7 固定 1 倍消耗。Orchestrator 默认用免费模型，按需 `/preset` 升级。

---

## 模板一：双平台版（OpenCode Zen + 智谱）— 推荐

> 适合长期稳定配置。4 套 Preset 只有 Orchestrator 模型不同，其余 Agent 所有 Preset 都一样。
> Observer 已禁用（无免费多模态模型）。

```jsonc
{
  "$schema": "https://unpkg.com/oh-my-opencode-slim@latest/oh-my-opencode-slim.schema.json",
  "preset": "zen-free",  // 默认免费编排
  "disabled_agents": ["observer"],  // 无免费多模态模型，禁用
  "presets": {
    "zen-free": {
      "orchestrator": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": ["*"],
        "mcps": ["*", "!context7"]
      },
      "oracle": {
        "model": "zhipu-coding-plan/glm-5.2",
        "variant": "high",
        "skills": ["simplify"],
        "mcps": []
      },
      "council": {
        "model": "zhipu-coding-plan/glm-5-turbo",
        "variant": "high",
        "skills": [],
        "mcps": []
      },
      "librarian": {
        "model": "opencode/deepseek-v4-flash-free",
        "variant": "low",
        "skills": [],
        "mcps": ["websearch", "grep_app"]
      },
      "explorer": {
        "model": "opencode/deepseek-v4-flash-free",
        "variant": "low",
        "skills": [],
        "mcps": []
      },
      "designer": {
        "model": "opencode/deepseek-v4-flash-free",
        "variant": "medium",
        "skills": [],
        "mcps": []
      },
      "fixer": {
        "model": "zhipu-coding-plan/glm-4.7",
        "variant": "low",
        "skills": [],
        "mcps": []
      }
    },
    "zhipu-std": {
      "orchestrator": {
        "model": "zhipu-coding-plan/glm-4.7",
        "skills": ["*"],
        "mcps": ["*", "!context7"]
      }
      // 其余 Agent 同 zen-free
    },
    "zhipu-fast": {
      "orchestrator": {
        "model": "zhipu-coding-plan/glm-5-turbo",
        "skills": ["*"],
        "mcps": ["*", "!context7"]
      }
      // 其余 Agent 同 zen-free
    },
    "zhipu-full": {
      "orchestrator": {
        "model": "zhipu-coding-plan/glm-5.2",
        "skills": ["*"],
        "mcps": ["*", "!context7"]
      }
      // 其余 Agent 同 zen-free
    }
  },
  "council": {
    "default_preset": "balanced",
    "timeout": 180000,
    "councillor_execution_mode": "parallel",
    "councillor_retries": 3,
    "presets": {
      "balanced": {
        "alpha": {
          "model": "zhipu-coding-plan/glm-5.2",
          "prompt": "Focus on correctness and edge cases."
        },
        "beta": {
          "model": "zhipu-coding-plan/glm-4.7",
          "prompt": "Focus on performance and trade-offs."
        },
        "gamma": {
          "model": "opencode/deepseek-v4-flash-free",
          "prompt": "Focus on user experience and implementation."
        }
      }
    }
  }
}
```

### 4 套 Preset 说明

| Preset | Orchestrator | 其余 Agent | 升级时机 |
|--------|-------------|-----------|---------|
| `zen-free` | deepseek-free（免费） | 全部相同 | 默认，先试试 |
| `zhipu-std` | glm-4.7（1倍） | 全部相同 | 免费委派不准 |
| `zhipu-fast` | glm-5-turbo（中等） | 全部相同 | std 还不够 |
| `zhipu-full` | glm-5.2（高） | 全部相同 | 要求最高 |

### 切换命令

```
/preset zen-free      # 免费（默认）
/preset zhipu-std     # 1倍成本
/preset zhipu-fast    # 中等成本
/preset zhipu-full    # 最强
```

---

## 以下为旧版模板（三平台版，百炼/Go 即将到期）

| 层级 | 模型 | 平台 | 成本 | Agent 分配 |
|------|------|------|------|-----------|
| T0 (免费) | DeepSeek V4 Flash Free | OpenCode Zen | 免费 | Explorer, Librarian |
| T1 (主力) | GLM-4.7 | 智谱 Pro | 1倍 | Fixer |
| T1.5 (前端) | Qwen 3.6 Plus | OpenCode Go | Go额度 | Designer |
| T2 (降级) | DeepSeek V4 Flash/Pro | OpenCode Go | Go额度 | 备选 |
| T2.5 (多模态) | Kimi K2.6 | OpenCode Go | Go额度 | Observer |
| T3 (高阶) | GLM-5.2 | 智谱 Pro | ⚠️高峰3倍/非高峰2倍 | Orchestrator, Oracle |
| T3.5 (共识) | Council 配置驱动 | 多平台 | 高（多模型并行） | Council |

> **智谱 Pro 成本提醒**：GLM-5.2 高峰期（14:00-18:00 UTC+8）消耗 3 倍额度，非高峰期消耗 2 倍。GLM-4.7 固定 1 倍消耗。日常开发优先使用 GLM-4.7 和 DeepSeek Free。

---

## 模板零：三平台版（OpenCode Zen + OpenCode Go + 智谱 Pro）

> 适合同时拥有 OpenCode Go 和 智谱 Pro 的用户。**推荐配置：Orchestrator/Oracle 用 GLM-5.2，Explorer/Librarian 用 DeepSeek Free，Designer 用 Qwen，Fixer 用 GLM-4.7。**

```jsonc
{
  "$schema": "https://unpkg.com/oh-my-opencode-slim@latest/oh-my-opencode-slim.schema.json",

  // ===== Preset 配置 =====
  "preset": "zhipu-go",
  "disabled_agents": [],  // 启用 Observer（需要多模态能力）

  "presets": {
    "zhipu-go": {
      // ===== 高阶 Agent =====
      // Orchestrator: 主协调者，使用最高阶模型
      "orchestrator": {
        "model": "zhipu-coding-plan/glm-5.2",
        "skills": ["*"],  // 所有技能
        "mcps": ["*", "!context7"]  // 所有 MCP，排除 context7
      },

      // Oracle: 架构咨询、深度调试，使用高阶模型 + high variant
      "oracle": {
        "model": "zhipu-coding-plan/glm-5.2",
        "variant": "high",  // 高推理强度
        "skills": ["simplify"],  // 代码简化技能
        "mcps": []  // 无 MCP，专注代码分析
      },

      // Council: 多模型共识合成，使用高阶模型
      "council": {
        "model": "zhipu-coding-plan/glm-5-turbo",
        "variant": "high",
        "skills": [],
        "mcps": []
      },

      // ===== 免费 Agent =====
      // Librarian: 文档搜索，使用免费模型
      "librarian": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": ["websearch", "context7", "grep_app"]  // Web搜索 + 文档 + 代码搜索 MCP
      },

      // Explorer: 代码侦察，使用免费模型
      "explorer": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": []  // 无 MCP，专注文件操作
      },

      // ===== 中等 Agent =====
      // Designer: UI/UX 实现，使用前端模型
      "designer": {
        "model": "opencode-go/qwen3.6-plus",
        "variant": "medium",
        "skills": [],
        "mcps": []
      },

      // Observer: 视觉分析（图片/PDF），使用多模态模型
      "observer": {
        "model": "opencode-go/kimi-k2.6",
        "skills": [],
        "mcps": []
      },

      // ===== 主力 Agent =====
      // Fixer: 快速实现，使用主力模型（1倍消耗）
      "fixer": {
        "model": "zhipu-coding-plan/glm-4.7",
        "skills": [],
        "mcps": []
      }
    }
  },

  // ===== Council 配置 =====
  // 多模型共识系统：并行调用多个模型，合成答案
  "council": {
    "default_preset": "balanced",
    "timeout": 180000,  // 3分钟超时
    "councillor_execution_mode": "parallel",  // 并行执行
    "councillor_retries": 3,
    "presets": {
      // 平衡预设：三个不同平台的模型
      "balanced": {
        "alpha": {
          "model": "zhipu-coding-plan/glm-5.2",
          "prompt": "Focus on correctness and edge cases."
        },
        "beta": {
          "model": "opencode-go/deepseek-v4-pro",
          "prompt": "Focus on performance and implementation details."
        },
        "gamma": {
          "model": "opencode-go/qwen3.6-plus",
          "prompt": "Focus on user experience and maintainability."
        }
      },
      // 深度预设：两个高阶模型对比
      "deep": {
        "primary": {
          "model": "zhipu-coding-plan/glm-5.2",
          "prompt": "Provide the primary recommendation."
        },
        "reviewer": {
          "model": "zhipu-coding-plan/glm-5-turbo",
          "prompt": "Challenge the primary recommendation and identify weaknesses."
        }
      },
      // 快速预设：免费模型快速讨论
      "quick": {
        "a": {
          "model": "opencode/deepseek-v4-flash-free"
        },
        "b": {
          "model": "opencode-go/deepseek-v4-flash"
        }
      }
    }
  },

  // ===== 运行时回退 =====
  // 当模型返回空响应时自动重试
  "fallback": {
    "enabled": false,  // OmO-slim 默认不启用自动 fallback
    "retry_on_empty": true
  },

  // ===== 功能开关 =====
  "autoUpdate": true,  // 自动更新插件
  "sessionManager": {
    "maxSessionsPerAgent": 2,
    "readContextMinLines": 10,
    "readContextMaxFiles": 8
  }
}
```

---

## 模板一：双平台版（OpenCode Zen + OpenCode Go，无智谱）

仅使用 OpenCode Zen 免费层 + OpenCode Go 付费层。适合只开通 OpenCode 的用户。

```jsonc
{
  "$schema": "https://unpkg.com/oh-my-opencode-slim@latest/oh-my-opencode-slim.schema.json",

  "preset": "go-only",
  "disabled_agents": [],

  "presets": {
    "go-only": {
      // Orchestrator: 使用 OpenCode Go 最高阶模型
      "orchestrator": {
        "model": "opencode-go/glm-5.2",
        "skills": ["*"],
        "mcps": ["*", "!context7"]
      },

      // Oracle: 使用 OpenCode Go 高阶模型
      "oracle": {
        "model": "opencode-go/deepseek-v4-pro",
        "variant": "high",
        "skills": ["simplify"],
        "mcps": []
      },

      // Council: 使用 OpenCode Go 高阶模型
      "council": {
        "model": "opencode-go/glm-5",
        "variant": "high",
        "skills": [],
        "mcps": []
      },

      // Librarian: 使用免费模型
      "librarian": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": ["websearch", "context7", "grep_app"]
      },

      // Explorer: 使用免费模型
      "explorer": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": []
      },

      // Designer: 使用 OpenCode Go 前端模型
      "designer": {
        "model": "opencode-go/qwen3.6-plus",
        "variant": "medium",
        "skills": [],
        "mcps": []
      },

      // Observer: 使用 OpenCode Go 多模态模型
      "observer": {
        "model": "opencode-go/kimi-k2.6",
        "skills": [],
        "mcps": []
      },

      // Fixer: 使用 OpenCode Go 主力模型
      "fixer": {
        "model": "opencode-go/deepseek-v4-pro",
        "skills": [],
        "mcps": []
      }
    }
  },

  "council": {
    "default_preset": "go-council",
    "timeout": 180000,
    "councillor_execution_mode": "parallel",
    "presets": {
      "go-council": {
        "alpha": {
          "model": "opencode-go/glm-5.2",
          "prompt": "Focus on correctness."
        },
        "beta": {
          "model": "opencode-go/deepseek-v4-pro",
          "prompt": "Focus on performance."
        },
        "gamma": {
          "model": "opencode-go/qwen3.6-plus",
          "prompt": "Focus on UX."
        }
      }
    }
  }
}
```

---

## 模板二：免费版（仅 OpenCode Zen）

仅使用 OpenCode Zen 免费层。适合不付费的用户。

```jsonc
{
  "$schema": "https://unpkg.com/oh-my-opencode-slim@latest/oh-my-opencode-slim.schema.json",

  "preset": "zen-free",
  "disabled_agents": ["observer"],  // 无多模态能力，禁用 Observer

  "presets": {
    "zen-free": {
      // Orchestrator: 使用免费模型
      "orchestrator": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": ["*"],
        "mcps": ["*"]
      },

      // Oracle: 使用免费模型
      "oracle": {
        "model": "opencode/deepseek-v4-flash-free",
        "variant": "high",
        "skills": ["simplify"],
        "mcps": []
      },

      // Council: 使用免费模型（单模型讨论）
      "council": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": []
      },

      // Librarian: 使用免费模型
      "librarian": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": ["websearch", "grep_app"]
      },

      // Explorer: 使用免费模型
      "explorer": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": []
      },

      // Designer: 使用免费模型
      "designer": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": []
      },

      // Fixer: 使用免费模型
      "fixer": {
        "model": "opencode/deepseek-v4-flash-free",
        "skills": [],
        "mcps": []
      }
    }
  },

  "council": {
    "default_preset": "single",
    "councillor_execution_mode": "serial",  // 单模型串行
    "presets": {
      "single": {
        "main": {
          "model": "opencode/deepseek-v4-flash-free"
        }
      }
    }
  }
}
```

---

## Agent 模型选择原则

| Agent | 推荐模型 | 平台 | 成本 | 说明 |
|-------|---------|------|------|------|
| Orchestrator | GLM-5.2 | 智谱 | ⚠️高 | 主协调者，需要强推理和判断 |
| Oracle | GLM-5.2 (high) | 智谱 | ⚠️高 | 架构咨询，需要深度分析 |
| Council | GLM-5-Turbo (high) | 智谱 | ⚠️高 | 多模型合成，需要强总结能力 |
| Librarian | DeepSeek Free | Zen | 免费 | 文档搜索，速度比推理更重要 |
| Explorer | DeepSeek Free | Zen | 免费 | 代码侦察，速度比推理更重要 |
| Designer | Qwen 3.6 Plus | Go | 中等 | UI/UX，需要视觉判断能力 |
| Observer | Kimi K2.6 | Go | 中等 | 图片/PDF 分析，需要多模态 |
| Fixer | GLM-4.7 | 智谱 | 1倍 | 快速实现，可靠性比推理更重要 |

### Skills 分配原则

| Skill | 描述 | 默认 Agent | 说明 |
|-------|------|-----------|------|
| simplify | 代码简化，保持行为 | oracle | 代码审查和简化 |
| codemap | 代码库映射 | orchestrator | 生成代码地图 |
| clonedeps | 依赖源码克隆 | orchestrator | 克隆依赖源码 |

### MCP 权限控制语法

```jsonc
"mcps": ["*"]           // 所有 MCP
"mcps": ["*", "!context7"]  // 所有 MCP，排除 context7
"mcps": ["websearch"]   // 仅 websearch
"mcps": ["websearch", "grep_app"]  // 仅 websearch 和 grep_app
"mcps": []              // 无 MCP
```

### Provider 前缀对照表

| 前缀 | 平台 | 成本档位 |
|------|------|----------|
| `opencode/` | OpenCode Zen | 免费 |
| `opencode-go/` | OpenCode Go | 付费（低-中） |
| `zhipu-coding-plan/` | 智谱 Pro | 付费（中-高） |

---

## 自定义 Preset 示例

### 添加自定义 Preset

```jsonc
{
  "presets": {
    // 现有预设...
    "my-custom": {
      "orchestrator": {
        "model": "opencode-go/glm-5.2",
        "skills": ["codemap", "clonedeps"],  // 仅这两个技能
        "mcps": ["grep_app"]  // 仅代码搜索 MCP
      },
      "oracle": {
        "model": "zhipu-coding-plan/glm-5-turbo",
        "variant": "high",
        "skills": ["simplify"],
        "mcps": []
      },
      // 其他 Agent...
    }
  }
}
```

### 切换 Preset

运行时切换预设：

```
/preset my-custom
```

---

## Council 详细配置

### 单模型串行模式（低成本）

```jsonc
{
  "council": {
    "councillor_execution_mode": "serial",
    "presets": {
      "single": {
        "main": { "model": "zhipu-coding-plan/glm-5.2" }
      }
    }
  }
}
```

### 三模型并行模式（平衡）

```jsonc
{
  "council": {
    "councillor_execution_mode": "parallel",
    "presets": {
      "balanced": {
        "alpha": { "model": "zhipu-coding-plan/glm-5.2" },
        "beta": { "model": "opencode-go/deepseek-v4-pro" },
        "gamma": { "model": "opencode-go/qwen3.6-plus" }
      }
    }
  }
}
```

### 角色分工模式（专业）

```jsonc
{
  "council": {
    "presets": {
      "review-board": {
        "reviewer": {
          "model": "zhipu-coding-plan/glm-5.2",
          "prompt": "Focus on bugs, edge cases, and failure modes."
        },
        "architect": {
          "model": "opencode-go/glm-5",
          "prompt": "Focus on maintainability, boundaries, and long-term design."
        },
        "optimizer": {
          "model": "opencode-go/deepseek-v4-pro",
          "prompt": "Focus on performance, scalability, and resource usage."
        }
      }
    }
  }
}
```

---

## 配置文件路径

| 平台 | 配置文件路径 |
|------|-------------|
| Windows | `%USERPROFILE%\.config\opencode\oh-my-opencode-slim.jsonc` |
| Mac/Linux | `~/.config/opencode/oh-my-opencode-slim.jsonc` |

> **JSONC 支持**：使用 `.jsonc` 扩展名可以添加注释和 trailing commas。如果 `.json` 和 `.jsonc` 同时存在，`.jsonc` 优先。