#!/usr/bin/env python3
"""Bake adaptive SVGs into deterministic light/dark files.

Embedding prefers-color-scheme inside an SVG can briefly paint the default
theme before the media query resolves. GitHub README pages then appear to
"flash" between themes. This script removes that runtime decision entirely.
"""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULTS = [
    "assets/banner.svg",
    "assets/build-wps.svg",
    "assets/build-academic.svg",
    "assets/capability-map.svg",
    "assets/wave.svg",
    "assets/identity-command-center.svg",
    "assets/now-console-v2.svg",
    "assets/chatgpt-activity.svg",
]


def bake_media(source: str, light: bool) -> str:
    marker = "@media"
    cursor = 0
    output: list[str] = []
    while True:
        start = source.find(marker, cursor)
        if start < 0:
            output.append(source[cursor:])
            break
        condition_end = source.find("{", start)
        if condition_end < 0:
            output.append(source[cursor:])
            break
        condition = source[start:condition_end]
        if "prefers-color-scheme" not in condition or "light" not in condition:
            output.append(source[cursor:condition_end + 1])
            cursor = condition_end + 1
            continue
        depth = 1
        end = condition_end + 1
        while end < len(source) and depth:
            if source[end] == "{":
                depth += 1
            elif source[end] == "}":
                depth -= 1
            end += 1
        output.append(source[cursor:start])
        if light:
            output.append(source[condition_end + 1:end - 1])
        cursor = end
    return "".join(output)


def targets(root: Path, explicit: list[str]) -> list[Path]:
    paths = [root / item for item in (explicit or DEFAULTS)]
    paths.extend(sorted((root / "assets/cards").glob("repo-*.svg")))
    return [path for path in dict.fromkeys(paths) if path.exists() and not path.stem.endswith(("-light", "-dark"))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    for path in targets(args.root, args.paths):
        source = path.read_text(encoding="utf-8")
        if "prefers-color-scheme" not in source:
            continue
        for variant, light in (("dark", False), ("light", True)):
            output = path.with_name(f"{path.stem}-{variant}{path.suffix}")
            output.write_text(bake_media(source, light), encoding="utf-8")
            print(f"OK   {output}")


if __name__ == "__main__":
    main()
