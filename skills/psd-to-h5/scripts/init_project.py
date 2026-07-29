#!/usr/bin/env python3
"""Create a draft PSD-to-H5 project with a flow.json input template."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from font_audit import audit_project_fonts, scan_psd_paths, suggested_mapping


def fail(message: str) -> None:
    print(f"[psd-to-h5] error: {message}", file=sys.stderr)
    raise SystemExit(2)


def flow_path_for(source: Path, root: Path) -> str:
    """Store a PSD path relative to flow.json, even when it lives outside root."""
    return Path(os.path.relpath(source.expanduser().resolve(), root)).as_posix()


def screen_id_for(source: Path, used: set[str]) -> str:
    """Use the PSD filename as a useful initial page id and keep ids unique."""
    base = source.stem.strip() or "页面"
    candidate = base
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New project directory")
    parser.add_argument("--name", default="PSD 转 H5 项目")
    parser.add_argument("--design-width", type=int, default=750)
    parser.add_argument("--design-height", type=int, default=1630)
    parser.add_argument("--psd", action="append", default=[], help="PSD/PSB source to scan for required fonts; repeat for multiple files")
    args = parser.parse_args()

    if args.design_width <= 0 or args.design_height <= 0:
        fail("design dimensions must be positive")
    root = args.output.expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        fail(f"project directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("psd", "notes", "assets", "fonts", "output", "review"):
        (root / directory).mkdir()

    flow = {
        "version": 1,
        "project": {
            "name": args.name,
            "designWidth": args.design_width,
            "designHeight": args.design_height,
            "outputDir": "output",
            "textMode": "semantic",
            "fonts": {},
        },
        "screens": [],
        "transitions": [
            {
                "from": "请替换页面",
                "trigger": "请替换交互元素",
                "to": "请替换页面",
                "overlay": "请替换弹层",
                "description": "请用中文描述这次点击、弹窗或页面跳转。",
            }
        ],
        "_generatedBy": "psd-to-h5/init_project.py",
        "_guide": {
            "version": {"作用": "协议版本，保持为 1。", "示例": 1},
            "project": {"作用": "整个 H5 项目的公共配置。", "示例": "project 对象"},
            "project.name": {"作用": "项目名称，用于标题和构建信息。", "示例": "个人中心 H5"},
            "project.designWidth": {"作用": "PSD 设计稿宽度，必须与 PSD 画布一致。", "示例": args.design_width},
            "project.designHeight": {"作用": "PSD 设计稿高度，必须与 PSD 画布一致。", "示例": args.design_height},
            "project.outputDir": {"作用": "构建产物目录，相对于 flow.json。", "示例": "output"},
            "project.textMode": {"作用": "字体齐全并成功压缩后是否使用 WebFont 语义文字；失败时自动回退 PNG。", "示例": "semantic"},
            "project.fonts": {"作用": "PSD 字体名到字体源文件的映射，key 必须和 PSD 字体名一致。", "示例": {"SourceHanSansCN-Regular": {"file": "fonts/SourceHanSansCN-Regular.otf", "format": "otf", "family": "Source Han Sans CN"}}},
            "project.fonts[].file": {"作用": "用户放入 fonts/ 目录的 TTF 或 OTF 源字体路径。", "示例": "fonts/SourceHanSansCN-Regular.otf"},
            "project.fonts[].format": {"作用": "源字体格式的辅助标记，填写 ttf 或 otf；实际读取路径以同一项的 file 为准，二者不一致时不会改写 file。", "示例": "otf"},
            "project.fonts[].family": {"作用": "页面使用的字体族显示名称。", "示例": "Source Han Sans CN"},
            "project.fonts[].weight": {"作用": "字体粗细，400 为常规，500 为中等，700 为粗体；可选。", "示例": 400},
            "project.fonts[].style": {"作用": "字体样式，normal 或 italic；可选。", "示例": "normal"},
            "screens[]": {"作用": "独立页面列表，每个 screens 项代表一个页面。", "示例": "我的、订单列表、商品详情分别配置为不同 screen。"},
            "screens[].id": {"作用": "页面唯一 ID，页面跳转时使用。", "示例": "我的"},
            "screens[].default": {"作用": "该页面默认 PSD 文件路径。", "示例": "psd/我的默认.psd"},
            "screens[].description": {"作用": "页面用途和设计说明。", "示例": "个人中心默认页面。"},
            "screens[].notes": {"作用": "可选的设计说明 Markdown 文件路径。", "示例": "notes/我的页面.md"},
            "screens[].elements[]": {"作用": "该页面上的可点击区域，不代表新页面。", "示例": "红包分享、订单入口、设置按钮。"},
            "screens[].elements[].id": {"作用": "交互触发器 ID，必须和 transitions.trigger 对应。", "示例": "红包分享"},
            "screens[].elements[].layer": {"作用": "用于定位点击区域的 PSD 图层名称；找不到时使用 bounds。", "示例": "红包分享"},
            "screens[].elements[].bounds": {"作用": "可选点击区域，格式为 [left, top, right, bottom]，使用 PSD 坐标。", "示例": [419, 1023, 507, 1046]},
            "screens[].elements[].description": {"作用": "说明点击区域的业务意图和预期结果。", "示例": "点击红包分享，打开页面内分享弹层。"},
            "screens[].elements[].action": {"作用": "可选的人类可读动作说明，不参与路由匹配。", "示例": "打开分享红包弹窗"},
            "screens[].overlays[]": {"作用": "属于当前页面的弹窗、抽屉、遮罩、底部弹层，不会创建独立页面。", "示例": "分享红包、资产明细弹窗、筛选抽屉。"},
            "screens[].overlays[].id": {"作用": "页面内 overlay 的唯一 ID。", "示例": "分享红包"},
            "screens[].overlays[].psd": {"作用": "overlay 对应 PSD 文件路径；应与默认页面保持画布尺寸和坐标对齐。", "示例": "psd/我的-分享红包.psd"},
            "screens[].overlays[].base": {"作用": "overlay 覆盖的基础页面，通常写当前 screen；不写时默认当前页面。", "示例": "我的:default"},
            "screens[].overlays[].excludeLayers": {"作用": "排除 overlay PSD 中重复的基础背景层，避免覆盖默认页面。", "示例": ["背景", "图层 14"]},
            "screens[].overlays[].description": {"作用": "说明弹层相对于基础页面发生了什么变化。", "示例": "从底部弹出分享红包弹层。"},
            "transitions[]": {"作用": "描述页面跳转或页面内 overlay 打开/关闭。", "示例": "我的点击订单入口跳转到订单列表。"},
            "transitions[].from": {"作用": "触发前页面；有 overlay 时写 页面ID#overlayID。", "示例": "我的#分享红包"},
            "transitions[].trigger": {"作用": "触发器，必须对应当前状态 elements[].id。", "示例": "关闭红包分享"},
            "transitions[].to": {"作用": "目标页面 ID；打开 overlay 时仍填写当前页面，关闭时填写要返回的页面。", "示例": "订单列表"},
            "transitions[].overlay": {"作用": "可选；填写后表示在 to 页面上打开指定 overlay，不填写表示页面跳转或关闭 overlay。", "示例": "分享红包"},
            "transitions[].description": {"作用": "用中文描述交互业务意图，便于 AI 和人工理解。", "示例": "点击订单入口，进入订单列表页面。"}
        },
        "_examples": {
            "pageJump": {"from": "我的", "trigger": "订单入口", "to": "订单列表", "description": "从我的页面跳转到订单列表页面。"},
            "openOverlay": {"from": "我的", "trigger": "红包分享", "to": "我的", "overlay": "分享红包", "description": "在我的页面上打开分享红包弹层。"},
            "closeOverlay": {"from": "我的#分享红包", "trigger": "关闭红包分享", "to": "我的", "description": "关闭页面内弹层并返回我的页面。"}
        },
        "_instructions": [
            "请替换示例页面、PSD 路径、页面说明、交互元素和状态跳转。",
            "独立页面配置在 screens[]；页面内弹窗、抽屉或遮罩配置在 overlays[]。",
            "跨页面跳转只填写 transitions.to；打开页面内 overlay 时额外填写 transitions.overlay。",
            "JSON 不支持 // 注释，因此字段说明和示例集中放在同一个文件的 _guide 与 _examples 中，构建时会忽略它们。",
            "初始化时可使用 --psd 文件路径重复传入 PSD；程序会读取文本图层并把所需字体写入 project.fonts。没有在初始化时传入 PSD 时，放入 psd/ 后运行 analyze_fonts.py flow.json --update。",
            "字体文件请按 project.fonts 中的 file 路径放入 fonts/，构建时会自动检查、子集化为 WOFF2 并引入页面。",
            "填写完成后对 AI 说“开始”，即可执行切图、组装和浏览器校验。",
        ],
    }
    used_ids: set[str] = set()
    if args.psd:
        # Real PSD inputs are already registered as screens; leave interactions
        # empty until the user describes them instead of retaining fake routes.
        flow["transitions"] = []
        for raw_path in args.psd:
            source = Path(raw_path).expanduser().resolve()
            screen_id = screen_id_for(source, used_ids)
            flow["screens"].append(
                {
                    "id": screen_id,
                    "default": flow_path_for(source, root),
                    "description": f"由 {source.name} 初始化的独立页面；请补充页面用途、用户目标和交互说明。",
                    "elements": [],
                    "overlays": [],
                }
            )
    else:
        flow["screens"] = [
            {
                "id": "请替换页面",
                "default": "psd/页面默认.psd",
                "description": "请描述这个页面的用途、主要内容和用户目标。",
                "elements": [
                    {
                        "id": "请替换交互元素",
                        "layer": "图层名称，或直接填写 bounds",
                        "description": "请描述用户点击的位置、触发原因和预期结果。",
                        "action": "请填写对应的页面跳转或状态变化",
                    }
                ],
                "overlays": [
                    {
                        "id": "请替换弹层",
                        "psd": "psd/页面弹层.psd",
                        "description": "请描述这个弹层相对于默认页面发生了什么变化。",
                    }
                ],
            }
        ]
    if args.psd:
        scan = scan_psd_paths((Path(item) for item in args.psd), root)
        project = flow["project"]
        for item in scan["required"]:
            project["fonts"].setdefault(item["name"], suggested_mapping(item["name"]))
        audit = audit_project_fonts(scan["required"], project, root)
        flow["_fontAudit"] = {
            "说明": "初始化时从 PSD 文本图层读取的字体清单；字体文件必须由用户放入 fonts/ 并在 project.fonts 中确认路径。",
            "required": scan["required"],
            "missingMapping": audit["missing_mapping"],
            "missingSource": audit["missing_source"],
            "scanErrors": scan["errors"],
        }
    else:
        flow["_fontAudit"] = {
            "说明": "初始化时尚未提供 PSD；填写 screens[].default 和 overlays[].psd 后运行 analyze_fonts.py flow.json --update。",
            "required": [],
            "missingMapping": [],
            "missingSource": [],
            "scanErrors": [],
        }
    (root / "flow.json").write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"project": str(root), "flow": str(root / "flow.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
