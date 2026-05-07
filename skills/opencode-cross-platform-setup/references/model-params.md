# 模型参数字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `context` | int | 上下文窗口大小（tokens） |
| `output` | int | 最大输出 tokens |
| `thinking.type` | string | `"enabled"` 启用思考模式；不设置则不启用 |
| `thinking.budgetTokens` | int | 思考预算 tokens（仅 thinking 启用时生效） |
| `modalities.input` | string[] | 输入支持模态：`"text"` / `"image"` |
| `modalities.output` | string[] | 输出支持模态：`"text"` |
