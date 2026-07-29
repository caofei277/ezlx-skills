#!/usr/bin/env python3
"""Create a draft PSD-to-H5 project with a flow.json input template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"[psd-to-h5] error: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New project directory")
    parser.add_argument("--name", default="PSD 转 H5 项目")
    parser.add_argument("--design-width", type=int, default=750)
    parser.add_argument("--design-height", type=int, default=1630)
    args = parser.parse_args()

    if args.design_width <= 0 or args.design_height <= 0:
        fail("design dimensions must be positive")
    root = args.output.expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        fail(f"project directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("psd", "notes", "assets", "output", "review"):
        (root / directory).mkdir()

    flow = {
        "version": 1,
        "project": {
            "name": args.name,
            "designWidth": args.design_width,
            "designHeight": args.design_height,
            "outputDir": "output",
        },
        "screens": [
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
                "states": [
                    {
                        "id": "请替换状态",
                        "psd": "psd/页面状态.psd",
                        "mode": "overlay",
                        "description": "请描述这个状态相对于默认页面发生了什么变化。",
                    }
                ],
            }
        ],
        "transitions": [
            {
                "from": "请替换页面:default",
                "trigger": "请替换交互元素",
                "to": "请替换页面:请替换状态",
                "description": "请用中文描述这次点击、弹窗或页面跳转。",
            }
        ],
        "_instructions": [
            "请替换示例页面、PSD 路径、页面说明、交互元素和状态跳转。",
            "弹窗、抽屉或遮罩状态请使用 mode=overlay。",
            "同一个页面的不同状态必须保持画布尺寸和坐标对齐。",
            "填写完成后对 AI 说“开始”，即可执行切图、组装和浏览器校验。",
        ],
    }
    (root / "flow.json").write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"project": str(root), "flow": str(root / "flow.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
