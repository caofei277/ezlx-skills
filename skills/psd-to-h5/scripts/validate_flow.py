#!/usr/bin/env python3
"""Validate a PSD-to-H5 flow.json without modifying the project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def issue(message: str, errors: list[str], warnings: list[str], strict: bool = False) -> None:
    (errors if strict else warnings).append(message)


def state_key(screen_id: str, state_id: str) -> str:
    return f"{screen_id}:{state_id}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flow", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat missing PSD files as errors")
    args = parser.parse_args()
    flow_path = args.flow.expanduser().resolve()
    try:
        data: dict[str, Any] = json.loads(flow_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"error: cannot read JSON: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    if data.get("version") != 1:
        errors.append("version must be 1")
    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
        project = {}
    for key in ("designWidth", "designHeight"):
        if not isinstance(project.get(key), int) or project[key] <= 0:
            errors.append(f"project.{key} must be a positive integer")

    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        errors.append("screens must be a non-empty array")
        screens = []
    known_states: set[str] = set()
    seen_screens: set[str] = set()
    base_dir = flow_path.parent

    for screen in screens:
        if not isinstance(screen, dict):
            errors.append("each screen must be an object")
            continue
        screen_id = screen.get("id")
        if not isinstance(screen_id, str) or not screen_id:
            errors.append("each screen needs a non-empty id")
            continue
        if screen_id in seen_screens:
            errors.append(f"duplicate screen id: {screen_id}")
        seen_screens.add(screen_id)
        default_psd = screen.get("default")
        if not isinstance(default_psd, str):
            errors.append(f"{screen_id}.default must be a PSD path")
        else:
            path = (base_dir / default_psd).resolve()
            if not path.is_file():
                issue(f"missing PSD: {default_psd}", errors, warnings, args.strict)
        known_states.add(state_key(screen_id, "default"))
        states = screen.get("states", [])
        if not isinstance(states, list):
            errors.append(f"{screen_id}.states must be an array")
            states = []
        seen_states: set[str] = {"default"}
        for state in states:
            if not isinstance(state, dict):
                errors.append(f"{screen_id}.states entries must be objects")
                continue
            state_id = state.get("id")
            psd_path = state.get("psd")
            if not isinstance(state_id, str) or not state_id:
                errors.append(f"{screen_id} state needs a non-empty id")
                continue
            if state_id in seen_states:
                errors.append(f"duplicate state id: {screen_id}:{state_id}")
            seen_states.add(state_id)
            known_states.add(state_key(screen_id, state_id))
            if state.get("mode", "overlay") not in ("overlay", "route", "page"):
                errors.append(f"invalid mode for {screen_id}:{state_id}")
            if not isinstance(psd_path, str):
                errors.append(f"{screen_id}:{state_id}.psd must be a PSD path")
            elif not (base_dir / psd_path).resolve().is_file():
                issue(f"missing PSD: {psd_path}", errors, warnings, args.strict)
        elements = screen.get("elements", [])
        if not isinstance(elements, list):
            errors.append(f"{screen_id}.elements must be an array")
        else:
            element_ids: set[str] = set()
            for element in elements:
                if not isinstance(element, dict) or not isinstance(element.get("id"), str):
                    errors.append(f"{screen_id} elements need string ids")
                elif element["id"] in element_ids:
                    errors.append(f"duplicate element id: {screen_id}:{element['id']}")
                else:
                    element_ids.add(element["id"])

    transitions = data.get("transitions", [])
    if not isinstance(transitions, list):
        errors.append("transitions must be an array")
        transitions = []
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            errors.append(f"transition {index} must be an object")
            continue
        for key in ("from", "trigger", "to"):
            if not isinstance(transition.get(key), str) or not transition[key]:
                errors.append(f"transition {index} needs {key}")
        for key in ("from", "to"):
            target = transition.get(key)
            if isinstance(target, str):
                normalized = target if ":" in target else state_key(target, "default")
                if normalized not in known_states:
                    errors.append(f"transition {index} references unknown state: {target}")

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"valid: {len(seen_screens)} screen(s), {len(known_states)} state(s), {len(transitions)} transition(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
