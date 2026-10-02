#!/usr/bin/env python3
"""把每日贡献数据渲染成一张 tokyonight 风格的「贡献活跃度」面积图 SVG。

数据源：https://github-contributions-api.jogruber.de/v4/<user>?y=last
（github-readme-activity-graph 的公共 Vercel 实例已被作者暂停，所以自己画，
生成的 SVG 会被提交回仓库，README 只引用静态文件。）

用法：python3 activity_graph.py contrib.json > activity.svg
"""
import json
import sys
from datetime import date

W, H = 880, 210
PAD_L, PAD_R, PAD_T, PAD_B = 18, 18, 46, 34
BG = "#0d1117"
LINE = "#8b5cf6"
TITLE = "#c9d1d9"
MUTED = "#6e7681"
FONT = "Segoe UI, Ubuntu, Helvetica Neue, Helvetica, Arial, sans-serif"


def load(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    days = data.get("contributions") or []
    out = []
    for item in days:
        try:
            y, m, d = (int(p) for p in item["date"].split("-"))
        except (KeyError, ValueError, AttributeError):
            continue
        out.append((date(y, m, d), int(item.get("count") or 0)))
    out.sort(key=lambda x: x[0])
    if not out:
        raise SystemExit("empty contribution data")
    return out


def weekly(days):
    """按自然周聚合，得到 ~53 个点。"""
    buckets, labels = [], []
    for day, count in days:
        monday = day.toordinal() - day.weekday()
        if not buckets or buckets[-1][0] != monday:
            buckets.append([monday, 0])
            labels.append(day)
        buckets[-1][1] += count
    return [v for _, v in buckets], labels


def catmull(points):
    """Catmull-Rom 转三次贝塞尔，得到平滑曲线。"""
    if len(points) < 2:
        return ""
    d = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    p = [points[0]] + list(points) + [points[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d.append(
            f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        )
    return " ".join(d)


def main():
    days = load(sys.argv[1])
    values, labels = weekly(days)
    total = sum(v for _, v in days)

    x0, x1 = PAD_L, W - PAD_R
    y0, y1 = PAD_T, H - PAD_B
    top = max(max(values), 4)
    n = max(len(values) - 1, 1)

    pts = [
        (x0 + (x1 - x0) * i / n, y1 - (y1 - y0) * (v / top))
        for i, v in enumerate(values)
    ]
    line = catmull(pts)
    area = f"{line} L {pts[-1][0]:.1f} {y1} L {pts[0][0]:.1f} {y1} Z"

    # 月份标签：每个月第一次出现的位置
    months = []
    seen = set()
    for i, day in enumerate(labels):
        key = (day.year, day.month)
        if key in seen:
            continue
        seen.add(key)
        months.append((x0 + (x1 - x0) * i / n, day.strftime("%b")))

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="{total} contributions in the last year">',
        "<defs>",
        '<linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{LINE}" stop-opacity="0.55"/>',
        f'<stop offset="100%" stop-color="{LINE}" stop-opacity="0"/>',
        "</linearGradient>",
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
        f'<text x="{PAD_L}" y="30" fill="{TITLE}" font-family="{FONT}" '
        f'font-size="16" font-weight="600">'
        f"{total} contributions in the last year</text>",
        f'<path d="{area}" fill="url(#ag)"/>',
        f'<path d="{line}" fill="none" stroke="{LINE}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>',
    ]
    for x, name in months:
        svg.append(
            f'<text x="{x:.1f}" y="{H - 12}" fill="{MUTED}" font-family="{FONT}" '
            f'font-size="11" text-anchor="middle">{name}</text>'
        )
    svg.append("</svg>")
    print("\n".join(svg))


if __name__ == "__main__":
    main()
