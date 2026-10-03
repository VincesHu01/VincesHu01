#!/usr/bin/env python3
"""Render an embeddable ChatGPT token activity card from profile analytics JSON."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path


def compact(value: int | None) -> str:
    if value is None:
        return "—"
    for divisor, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if value >= divisor:
            number = value / divisor
            if number < 10:
                return f"{number:.2f}".rstrip("0").rstrip(".") + suffix
            return f"{number:.1f}{suffix}" if number < 100 else f"{number:.0f}{suffix}"
    return f"{value:,}"


def duration(minutes: int | None) -> str:
    if minutes is None:
        return "—"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m" if hours else f"{mins}m"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(data: dict) -> str:
    daily = {
        dt.date.fromisoformat(item["date"]): int(item["tokens"])
        for item in data.get("daily", [])
        if item.get("date") and item.get("tokens") is not None
    }
    today = max(daily, default=dt.date.today())
    start = today - dt.timedelta(days=370)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # Sunday
    peak_daily = max(daily.values(), default=1)
    palette = ["#172033", "#123d56", "#0e7490", "#22d3ee", "#a78bfa", "#ec4899"]

    cells: list[str] = []
    for offset in range(371):
        day = start + dt.timedelta(days=offset)
        col, row = divmod(offset, 7)
        x, y = 42 + col * 17, 246 + row * 17
        tokens = daily.get(day, 0)
        if tokens <= 0:
            level = 0
        else:
            ratio = tokens / peak_daily
            level = 1 + sum(ratio >= threshold for threshold in (0.01, 0.05, 0.15, 0.35))
        title = f"{day.isoformat()}: {tokens:,} tokens" if day in daily else f"{day.isoformat()}: no recorded activity"
        cells.append(f'<g><title>{esc(title)}</title><rect class="heat heat-{level}" x="{x}" y="{y}" width="13" height="13" rx="3" fill="{palette[level]}"/></g>')

    latest_tokens = daily.get(today)
    latest_label = f"{today.isoformat()} · {latest_tokens:,} TOKENS" if latest_tokens is not None else "AWAITING FIRST EXACT DAILY SYNC"
    updated = data.get("updated_at", "pending")
    username = data.get("username", "vinceshu01")
    totals = [
        ("LIFETIME TOKENS", compact(data.get("lifetime_tokens")), "#a78bfa"),
        ("DAILY PEAK", compact(data.get("peak_tokens")), "#ec4899"),
        ("LONGEST TASK", duration(data.get("longest_task_minutes")), "#22d3ee"),
        ("LONGEST STREAK", f'{data.get("longest_streak", "—")} days', "#fbbf24"),
        ("CURRENT STREAK", f'{data.get("current_streak", "—")} days', "#34d399"),
    ]
    stats = []
    for i, (label, value, color) in enumerate(totals):
        x = 30 + i * 188
        stats.append(f'''<g transform="translate({x} 92)">
          <rect class="stat" width="174" height="86" rx="15" fill="url(#glass)" stroke="{color}" stroke-opacity=".34"/>
          <circle cx="20" cy="22" r="4" fill="{color}" filter="url(#glow)"/>
          <text x="32" y="26" class="label muted">{label}</text>
          <text x="16" y="63" class="value bright">{esc(value)}</text>
        </g>''')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="390" viewBox="0 0 1000 390" role="img" aria-labelledby="title desc">
  <title id="title">ChatGPT daily token activity for @{esc(username)}</title>
  <desc id="desc">Daily token consumption, lifetime total, peak day, longest task, and activity streaks.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#060816"/><stop offset=".5" stop-color="#10102a"/><stop offset="1" stop-color="#071d25"/></linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#8b5cf6"/><stop offset=".48" stop-color="#ec4899"/><stop offset="1" stop-color="#22d3ee"/></linearGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#fff" stop-opacity=".035"/></linearGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#94a3b8" stroke-opacity=".05"/></pattern>
    <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <style>text{{font-family:Inter,'Segoe UI',Arial,sans-serif}}.bg{{fill:url(#bg)}}.grid-bg{{fill:url(#grid)}}.stat{{fill:url(#glass)}}.mono{{font-family:'SFMono-Regular',Consolas,monospace}}.bright{{fill:#f8fafc}}.muted{{fill:#94a3b8}}.label{{font-size:10px;font-weight:700;letter-spacing:1.35px}}.value{{font-size:25px;font-weight:800}}.pulse{{animation:p 2.3s ease-in-out infinite}}@keyframes p{{50%{{opacity:.3}}}}@media(prefers-color-scheme:light){{.bg{{fill:#fff}}.grid-bg{{opacity:.3}}.stat{{fill:#f8fafc}}.bright{{fill:#24292f}}.muted{{fill:#64748b}}.heat-0{{fill:#ebedf0}}.heat-1{{fill:#cffafe}}.heat-2{{fill:#67e8f9}}.heat-3{{fill:#22d3ee}}.heat-4{{fill:#a78bfa}}.heat-5{{fill:#db2777}}}}</style>
  </defs>
  <rect class="bg" width="1000" height="390" rx="22"/><rect class="grid-bg" width="1000" height="390" rx="22"/>
  <rect x=".75" y=".75" width="998.5" height="388.5" rx="21.25" fill="none" stroke="url(#edge)" stroke-width="1.5" stroke-opacity=".8"/>
  <circle cx="34" cy="38" r="5" fill="#34d399" filter="url(#glow)" class="pulse"/>
  <text x="50" y="35" class="label" fill="#c4b5fd">CHATGPT TOKEN TELEMETRY</text><text x="50" y="55" class="mono" font-size="11" fill="#64748b">ACTUAL DAILY CONSUMPTION · NOT REMAINING QUOTA</text>
  <text x="966" y="37" text-anchor="end" class="mono" font-size="12" fill="#22d3ee">@{esc(username)}</text><text x="966" y="55" text-anchor="end" class="mono" font-size="10" fill="#64748b">SYNC {esc(updated)}</text>
  {''.join(stats)}
  <text x="30" y="218" class="label" fill="#67e8f9">365-DAY TOKEN ACTIVITY</text><text x="970" y="218" text-anchor="end" class="mono" font-size="11" fill="#94a3b8">{esc(latest_label)}</text>
  {''.join(cells)}
  <text x="42" y="381" class="mono" font-size="10" fill="#64748b">OLDER</text><text x="943" y="381" text-anchor="end" class="mono" font-size="10" fill="#64748b">MORE</text>
  <rect x="949" y="370" width="10" height="10" rx="2" fill="#123d56"/><rect x="963" y="370" width="10" height="10" rx="2" fill="#22d3ee"/><rect x="977" y="370" width="10" height="10" rx="2" fill="#ec4899"/>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data), encoding="utf-8")


if __name__ == "__main__":
    main()
