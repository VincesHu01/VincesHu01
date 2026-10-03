#!/usr/bin/env python3
"""Render the Now console from the latest GitHub activity plus profile config."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def compact(text: str, limit: int = 52) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def activity_status(pushed_at: str, now: dt.datetime) -> tuple[str, str]:
    pushed = dt.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    age = max(0, (now - pushed).days)
    if age <= 1:
        return "BUILDING", "#34d399"
    if age <= 7:
        return "SHIP MODE", "#f472b6"
    return "EXPLORING", "#22d3ee"


def render(snapshot: dict, config: dict) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    repos = snapshot.get("latest", [])[:3]
    accents = ["#8b5cf6", "#ec4899", "#22d3ee"]
    icons = ["◈", "✦", "⌕"]
    rows: list[str] = []
    for index, repo in enumerate(repos):
        y = 204 + index * 66
        status, status_color = activity_status(repo.get("pushed_at") or repo.get("updated_at"), now)
        name = compact(repo.get("name") or "untitled", 34).upper()
        description = compact(repo.get("description") or "No description yet.")
        accent = accents[index]
        rows.append(f'''<g transform="translate(34 {y})">
    <rect class="glass" width="552" height="54" rx="13" stroke="{accent}" stroke-opacity=".40"/>
    <rect x="12" y="12" width="30" height="30" rx="9" fill="{accent}" fill-opacity=".16"/><text x="27" y="33" text-anchor="middle" font-size="16" fill="{accent}">{icons[index]}</text>
    <text x="55" y="22" class="label" fill="{accent}">{index + 1:02d} · {esc(name)}</text><text x="55" y="42" class="body bright">{esc(description)}</text>
    <text x="528" y="32" text-anchor="end" class="mono small" fill="{status_color}">{status}</text>
  </g>''')
    while len(rows) < 3:
        rows.append("")
    tags = config.get("learning_orbit", ["PRODUCT STRATEGY", "AGENTIC DESIGN", "GLOBAL"])
    mission = config.get("mission", "Turn messy workflows into useful AI products.")
    words = mission.split()
    split = max(1, len(words) // 2)
    mission_a, mission_b = " ".join(words[:split]), " ".join(words[split:])
    version = now.strftime("v%y.%m.%d")
    synced = snapshot.get("updated_at", "")[:16].replace("T", " ") + " UTC"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="410" viewBox="0 0 1000 410" role="img" aria-labelledby="title desc">
  <title id="title">VincesHu live operating system</title><desc id="desc">A live console generated from recently updated GitHub projects.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#070a18"/><stop offset=".48" stop-color="#10102b"/><stop offset="1" stop-color="#071a24"/></linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#8b5cf6"/><stop offset=".5" stop-color="#ec4899"/><stop offset="1" stop-color="#22d3ee"/></linearGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".10"/><stop offset="1" stop-color="#fff" stop-opacity=".035"/></linearGradient>
    <radialGradient id="orb"><stop stop-color="#a78bfa" stop-opacity=".65"/><stop offset=".5" stop-color="#22d3ee" stop-opacity=".14"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#94a3b8" stroke-opacity=".055"/></pattern>
    <filter id="glow"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <style>text{{font-family:Inter,'Segoe UI',Arial,sans-serif}}.mono{{font-family:'SFMono-Regular',Consolas,monospace}}.bg{{fill:url(#bg)}}.grid-bg{{fill:url(#grid)}}.glass{{fill:url(#glass)}}.core{{fill:#0f172a}}.muted{{fill:#94a3b8}}.bright{{fill:#f8fafc}}.label{{font-size:11px;letter-spacing:1.8px;font-weight:700}}.title{{font-size:25px;font-weight:800}}.body{{font-size:13px}}.small{{font-size:11px}}.chip{{font-size:10px;font-weight:700}}.pulse{{animation:p 2.4s ease-in-out infinite}}.orbit{{transform-origin:835px 206px;animation:spin 12s linear infinite}}@keyframes p{{50%{{opacity:.35}}}}@keyframes spin{{to{{transform:rotate(360deg)}}}}@media(prefers-color-scheme:light){{.bg{{fill:#fff}}.grid-bg{{opacity:.35}}.glass{{fill:#f8fafc}}.core{{fill:#fff}}.muted{{fill:#64748b}}.bright{{fill:#1f2328}}}}</style>
  </defs>
  <rect class="bg" width="1000" height="410" rx="22"/><rect class="grid-bg" width="1000" height="410" rx="22"/><rect x=".75" y=".75" width="998.5" height="408.5" rx="21.25" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
  <rect class="glass" x="24" y="20" width="952" height="46" rx="13" stroke="#94a3b8" stroke-opacity=".18"/><circle cx="47" cy="43" r="5" fill="#34d399" filter="url(#glow)" class="pulse"/>
  <text x="62" y="47" class="label bright">CURRENT OPERATING SYSTEM</text><text x="296" y="47" class="label muted">// GITHUB ACTIVITY FEED</text><text x="883" y="47" text-anchor="end" class="label" fill="#22d3ee">VINCESHU.OS</text><text x="952" y="47" text-anchor="end" class="mono small muted">{version}</text>
  <text x="34" y="100" class="label" fill="#a78bfa">MISSION VECTOR</text><text x="34" y="133" class="title bright">{esc(mission_a)}</text><text x="34" y="163" class="title" fill="#f0abfc">{esc(mission_b)}</text><path d="M34 180H585" stroke="url(#edge)" stroke-width="2" opacity=".8"/>
  {''.join(rows)}
  <circle cx="835" cy="206" r="128" fill="url(#orb)" opacity=".55"/><circle cx="835" cy="206" r="96" fill="none" stroke="#8b5cf6" stroke-opacity=".34" stroke-dasharray="2 8" class="orbit"/><circle cx="835" cy="206" r="67" fill="none" stroke="#22d3ee" stroke-opacity=".25"/><circle class="core" cx="835" cy="206" r="42" stroke="url(#edge)" stroke-width="2" filter="url(#glow)"/><text x="835" y="201" text-anchor="middle" class="label" fill="#8b5cf6">LEARN</text><text x="835" y="220" text-anchor="middle" class="mono small bright">SHIP ↗</text>
  <text x="835" y="91" text-anchor="middle" class="label muted">LEARNING ORBIT</text>
  <g transform="translate(638 321)"><rect width="120" height="28" rx="14" fill="#8b5cf6" fill-opacity=".16" stroke="#8b5cf6"/><text x="60" y="18" text-anchor="middle" class="chip" fill="#8b5cf6">{esc(tags[0])}</text></g><g transform="translate(766 321)"><rect width="126" height="28" rx="14" fill="#ec4899" fill-opacity=".13" stroke="#ec4899"/><text x="63" y="18" text-anchor="middle" class="chip" fill="#ec4899">{esc(tags[1])}</text></g><g transform="translate(900 321)"><rect width="76" height="28" rx="14" fill="#22d3ee" fill-opacity=".13" stroke="#22d3ee"/><text x="38" y="18" text-anchor="middle" class="chip" fill="#0891b2">{esc(tags[2])}</text></g>
  <text x="638" y="381" class="mono small muted">INPUT</text><text x="685" y="381" class="mono small bright">{esc(config.get('input'))}</text><text x="785" y="381" class="mono small muted">OUTPUT</text><text x="838" y="381" class="mono small bright">{esc(config.get('output'))}</text><text x="966" y="294" text-anchor="end" class="mono" font-size="9" fill="#fbbf24">SYNC {esc(synced)}</text>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    args.output.write_text(render(snapshot, config), encoding="utf-8")


if __name__ == "__main__":
    main()
