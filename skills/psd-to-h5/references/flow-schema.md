# Flow Schema

Use `flow.json` only when the task has multiple screens or multiple visual states. A single PSD can go directly to `export_psd.py`. Generate user-facing descriptions and notes in Chinese by default. Keep schema keys and protocol enum values stable for the scripts.

## Core Objects

- `project`: name, design dimensions, and output directory.
- `screens[]`: independent pages. Each screen has one `default` PSD, optional `overlays[]`, and optional `elements[]`.
- `overlays[]`: dialogs, drawers, masks, bottom sheets, and other visual layers belonging to the current screen. Overlay entries do not have a user-facing `mode` field.
- `base`: optional screen state covered by an overlay. `excludeLayers` can remove duplicate full-canvas base layers from the overlay PSD. The runtime renders the base layers first and overlay layers above them.
- `elements[]`: user-described interaction targets. Prefer a stable `id`, a PSD `layer` name, and a plain-language `description`. Use `bounds: [left, top, right, bottom]` when no reliable layer name exists.
- `project.fonts`: maps the exact font names found in PSD text layers to source files under the project. `validate_flow.py` and `build_flow.py` automatically add suggested mappings for newly discovered names; `scripts/analyze_fonts.py flow.json --update` can be run explicitly for a readable preflight report. The user must place each TTF/OTF file under `fonts/` and confirm the path. The builder audits these files, subsets the glyphs, emits `WOFF2` plus `WOFF`, and injects `@font-face` rules. A build with missing font files is incomplete and exits with code 3 unless `--allow-missing-fonts` is explicitly used.
- `transitions[]`: page and overlay interactions. A page transition uses `from: "页面A"` and `to: "页面B"`; opening an overlay uses `from: "页面A"`, `to: "页面A"`, and `overlay: "弹层ID"`. A transition from an open overlay may use `from: "页面A#弹层ID"`.

## Authoring Rules

1. Keep the default PSD and all overlays for one screen at the same canvas size and alignment.
2. Put every independent page in `screens[]`; put dialogs and drawers inside that page's `overlays[]`.
3. Describe design intent in `description` fields. Explain what an element means, what a click should do, and which state should appear.
4. Use stable IDs that describe intent, such as `open-settings`, `asset-card`, and `close-dialog`. Do not use generated layer indexes as IDs.
5. Keep page transitions and overlay transitions explicit. Do not infer a destructive action or a business API from visual appearance alone.
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
      "overlays": [
        {"id": "资产明细弹窗", "psd": "psd/个人中心资产弹窗.psd", "description": "在个人中心上方打开资产明细弹窗。"}
      ]
    }
  ],
  "transitions": [
    {"from": "个人中心", "trigger": "打开资产明细", "to": "个人中心", "overlay": "资产明细弹窗"}
  ]
}
```
