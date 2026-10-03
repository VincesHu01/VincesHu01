#!/usr/bin/env python3
"""Build theme-aware repository cards directly from GitHub repository metadata."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.request
from pathlib import Path


LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "HTML": "#e34c26", "CSS": "#663399", "Swift": "#F05138", "Shell": "#89e051",
}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def request_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "VincesHu01-profile-card-builder",
            **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch(owner: str, repo: str) -> dict:
    return dict(request_json(f"https://api.github.com/repos/{owner}/{repo}"))


def fetch_all(owner: str) -> list[dict]:
    result = request_json(f"https://api.github.com/users/{owner}/repos?type=owner&sort=pushed&direction=desc&per_page=100")
    return [dict(item) for item in result if isinstance(item, dict)]


def wrap(text: str, width: int = 54, lines: int = 2) -> list[str]:
    words = text.replace("\n", " ").split()
    result: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width or not current:
            current = candidate
        else:
            result.append(current)
            current = word
            if len(result) == lines - 1:
                break
    if current and len(result) < lines:
        remaining = " ".join(words[sum(len(line.split()) for line in result):])
        result.append(remaining[: width - 1] + "…" if len(remaining) > width else remaining)
    return result[:lines] or ["No description yet."]


def render(data: dict, accent: str) -> str:
    name = esc(data["name"])
    description = wrap(data.get("description") or "No description yet.")
    language = esc(data.get("language") or "Repository")
    color = LANG_COLORS.get(data.get("language"), accent)
    stars = int(data.get("stargazers_count", 0))
    forks = int(data.get("forks_count", 0))
    updated = str(data.get("pushed_at") or data.get("updated_at") or "")[:10]
    lines = "".join(
        f'<text x="30" y="{94 + i * 21}" class="desc">{esc(line)}</text>'
        for i, line in enumerate(description)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="468" height="178" viewBox="0 0 468 178" role="img" aria-labelledby="title desc">
  <title id="title">{name} GitHub repository</title>
  <desc id="desc">{esc(data.get("description") or "No description yet")}</desc>
  <defs>
    <linearGradient id="edge" x1="0" x2="1"><stop stop-color="{accent}"/><stop offset=".55" stop-color="#ec4899"/><stop offset="1" stop-color="#22d3ee"/></linearGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop class="g1" stop-color="#fff" stop-opacity=".085"/><stop class="g2" offset="1" stop-color="#fff" stop-opacity=".025"/></linearGradient>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path class="grid" d="M24 0H0V24" fill="none" stroke="#94a3b8" stroke-opacity=".055"/></pattern>
    <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <style>
      text{{font-family:Inter,-apple-system,'Segoe UI',sans-serif}}.bg{{fill:#080b18}}.frame{{fill:url(#glass);stroke:#334155}}.name{{fill:#f8fafc;font-size:19px;font-weight:800}}.desc{{fill:#b8c2d6;font-size:13px}}.meta{{fill:#94a3b8;font-size:11px}}.grid{{stroke:#94a3b8}}.pulse{{animation:p 2.4s ease-in-out infinite}}@keyframes p{{50%{{opacity:.35}}}}
      @media(prefers-color-scheme:light){{.bg{{fill:#fff}}.frame{{fill:#f8fafc;stroke:#d0d7de}}.name{{fill:#24292f}}.desc{{fill:#57606a}}.meta{{fill:#6e7781}}.grid{{stroke:#7c3aed;stroke-opacity:.04}}.g1{{stop-color:#7c3aed;stop-opacity:.04}}.g2{{stop-color:#0891b2;stop-opacity:.015}}}}
    </style>
  </defs>
  <rect class="bg" width="468" height="178" rx="16"/>
  <rect width="468" height="178" rx="16" fill="url(#grid)"/>
  <rect class="frame" x="1" y="1" width="466" height="176" rx="15"/>
  <rect x="1" y="1" width="466" height="3" rx="1.5" fill="url(#edge)"/>
  <g transform="translate(29 27)" fill="none" stroke="{accent}" stroke-width="1.8"><path d="M3 2h13a2 2 0 0 1 2 2v15l-5-3-5 3V6H3z"/><circle cx="18" cy="4" r="3" fill="{accent}" filter="url(#glow)" class="pulse"/></g>
  <text x="59" y="48" class="name">{name}</text>
  <text x="438" y="44" text-anchor="end" font-family="monospace" font-size="10" fill="{accent}">LIVE METADATA</text>
  {lines}
  <line x1="29" y1="135" x2="439" y2="135" stroke="url(#edge)" stroke-opacity=".28"/>
  <circle cx="34" cy="154" r="5" fill="{color}"/><text x="47" y="158" class="meta">{language}</text>
  <text x="167" y="158" class="meta">★ {stars}</text><text x="211" y="158" class="meta">⑂ {forks}</text>
  <text x="438" y="158" text-anchor="end" class="meta" font-family="monospace">PUSHED {updated}</text>
</svg>'''


def repo_snapshot(data: dict) -> dict:
    return {
        key: data.get(key)
        for key in (
            "name", "html_url", "description", "language", "stargazers_count",
            "forks_count", "pushed_at", "updated_at", "homepage", "topics",
        )
    }


def latest_markup(repos: list[dict]) -> str:
    cells: list[str] = []
    for index, repo in enumerate(repos[:2], 1):
        name = esc(repo["name"])
        url = esc(repo["html_url"])
        description = esc(repo.get("description") or "No description yet.")
        cells.append(f'''    <td width="50%" valign="top">
      <a href="{url}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/cards/repo-latest-{index}-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/cards/repo-latest-{index}-light.svg"><img src="assets/cards/repo-latest-{index}-light.svg" width="100%" alt="{name}" /></picture></a>
      <br/>
      <b>{name}</b><br/>
      {description}
      <br/><br/>
      <a href="{url}"><code>VIEW SOURCE →</code></a>
    </td>''')
    return '<table>\n  <tr>\n' + "\n".join(cells) + '\n  </tr>\n</table>'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="VincesHu01")
    parser.add_argument("--output", type=Path, default=Path("assets/cards"))
    parser.add_argument("--data", type=Path, default=Path("data/github-projects.json"))
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("repos", nargs="*", default=["timeless-career-intelligence", "ai-news-aggregator", "Apex-workbench", "douji"])
    args = parser.parse_args()
    accents = ["#8b5cf6", "#ec4899", "#22d3ee", "#f59e0b"]
    args.output.mkdir(parents=True, exist_ok=True)
    all_repos = fetch_all(args.owner)
    by_name = {item["name"].lower(): item for item in all_repos}
    for repo, accent in zip(args.repos, accents):
        data = by_name.get(repo.lower()) or fetch(args.owner, repo)
        target = args.output / f"repo-{repo}.svg"
        target.write_text(render(data, accent), encoding="utf-8")
        print(f"OK   {target} <- {data.get('description')}")

    latest = [
        repo for repo in all_repos
        if not repo.get("fork") and not repo.get("archived") and repo.get("name", "").lower() != args.owner.lower()
    ][:3]
    for index, repo in enumerate(latest[:2], 1):
        target = args.output / f"repo-latest-{index}.svg"
        target.write_text(render(repo, accents[index - 1]), encoding="utf-8")
        print(f"OK   {target} <- {repo.get('name')}")

    args.data.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "owner": args.owner,
        "updated_at": max(
            (repo.get("updated_at") or "" for repo in all_repos),
            default="",
        ),
        "latest": [repo_snapshot(repo) for repo in latest],
        "shipped": [repo_snapshot(by_name.get(name.lower()) or fetch(args.owner, name)) for name in args.repos],
    }
    args.data.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.readme.exists() and len(latest) >= 2:
        content = args.readme.read_text(encoding="utf-8")
        replacement = f"<!-- LATEST_BUILDS:START -->\n{latest_markup(latest)}\n<!-- LATEST_BUILDS:END -->"
        updated = re.sub(
            r"<!-- LATEST_BUILDS:START -->.*?<!-- LATEST_BUILDS:END -->",
            replacement,
            content,
            flags=re.DOTALL,
        )
        if updated != content:
            args.readme.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
