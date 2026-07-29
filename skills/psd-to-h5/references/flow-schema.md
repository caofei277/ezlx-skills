# Flow Schema

Use `flow.json` only when the task has multiple screens or multiple visual states. A single PSD can go directly to `export_psd.py`. Generate user-facing descriptions and notes in Chinese by default. Keep schema keys and protocol enum values stable for the scripts.

## Core Objects

- `project`: name, design dimensions, and output directory.
- `screens[]`: route-level screens. Each screen has one `default` PSD, optional `states[]`, and optional `elements[]`.
- `states[]`: alternate full-canvas PSDs for the same screen. Use `mode: "overlay"` for dialogs/drawers and `mode: "route"` or `"page"` for page-level states.
- `elements[]`: user-described interaction targets. Prefer a stable `id`, a PSD `layer` name, and a plain-language `description`. Use `bounds: [left, top, right, bottom]` when no reliable layer name exists.
- `transitions[]`: state graph edges with `from`, `trigger`, and `to` values. State keys use `screen:state`, with `screen` shorthand meaning `screen:default`.

## Authoring Rules

1. Keep all PSDs for one screen at the same canvas size and alignment.
2. Treat each alternate PSD as a complete visual state unless the state is explicitly supplied as a separate overlay asset. This keeps screenshots and state transitions deterministic.
3. Describe design intent in `description` fields. Explain what an element means, what a click should do, and which state should appear.
4. Use stable IDs that describe intent, such as `open-settings`, `asset-card`, and `close-dialog`. Do not use generated layer indexes as IDs.
5. Keep route transitions and overlay transitions explicit. Do not infer a destructive action or a business API from visual appearance alone.
6. For long design notes, place a Markdown note beside the PSD under `notes/` and reference its path from the screen or state with `notes`.

## Example

```json
{
  "version": 1,
  "project": {"name": "个人中心", "designWidth": 750, "designHeight": 1630, "outputDir": "output"},
  "screens": [
    {
      "id": "个人中心",
      "default": "psd/个人中心默认.psd",
      "description": "个人中心默认页面，包含资产、订单、常用功能和底部导航。",
      "elements": [
        {"id": "打开资产明细", "layer": "资产中心", "description": "点击资产中心，打开资产明细弹窗。"}
      ],
      "states": [
        {"id": "资产明细弹窗", "psd": "psd/个人中心资产弹窗.psd", "mode": "overlay", "description": "在个人中心上方打开资产明细弹窗。"}
      ]
    }
  ],
  "transitions": [
    {"from": "个人中心:default", "trigger": "打开资产明细", "to": "个人中心:资产明细弹窗"}
  ]
}
```
