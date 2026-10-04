#!/usr/bin/env python3
"""Normalize github-readme-stats language cards to the stats-card canvas."""

from pathlib import Path
import re
import sys


def normalize(path: Path) -> None:
    svg = path.read_text(encoding="utf-8")
    bar_match = re.search(r'<mask id="rect-mask">\s*<rect[^>]*width="([\d.]+)"', svg, flags=re.S)
    compact_body = float(bar_match.group(1)) <= 300 if bar_match else False
    svg = re.sub(r'(<svg\s+[^>]*?width=")\d+("[^>]*?height=")\d+("[^>]*?viewBox="0 0 )\d+ \d+("[^>]*?>)',
                 r'\g<1>467\g<2>195\g<3>467 195\g<4>', svg, count=1, flags=re.S)
    svg = re.sub(r'(data-testid="card-bg"[\s\S]*?width=")\d+("\s)', r'\g<1>466\g<2>', svg, count=1)
    title_x = 108 if compact_body else 25
    body_x = 83 if compact_body else 0
    svg = re.sub(r'(data-testid="card-title"\s+transform="translate\()\d+,\s*\d+(\)")',
                 rf'\g<1>{title_x}, 40\g<2>', svg, count=1)
    svg = re.sub(r'(data-testid="main-card-body"\s+transform="translate\()\d+,\s*\d+(\)")',
                 rf'\g<1>{body_x}, 70\g<2>', svg, count=1)
    path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    targets = sys.argv[1:] or [
        "assets/cards/top-langs.svg",
        "assets/cards/top-langs-light.svg",
    ]
    for arg in targets:
        normalize(Path(arg))
