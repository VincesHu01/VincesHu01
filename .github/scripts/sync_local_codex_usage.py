#!/usr/bin/env python3
"""Sync exact per-day Codex token counters from local ChatGPT session logs.

This script is intentionally local-only: it reads ~/.codex session events and
writes aggregate counts to the public profile data file. It never reads or
publishes prompts, responses, credentials, filenames, or conversation titles.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def session_files(codex_dir: Path) -> list[Path]:
    candidates: dict[str, Path] = {}
    for folder in (codex_dir / "sessions", codex_dir / "archived_sessions"):
        if not folder.exists():
            continue
        for path in folder.rglob("*.jsonl"):
            existing = candidates.get(path.name)
            if existing is None or path.stat().st_size > existing.stat().st_size:
                candidates[path.name] = path
    return list(candidates.values())


def daily_totals(codex_dir: Path) -> dict[str, int]:
    totals: dict[str, int] = {}
    for path in session_files(codex_dir):
        previous = 0
        try:
            lines = path.open(encoding="utf-8")
        except OSError:
            continue
        with lines:
            for line in lines:
                if '"type":"token_count"' not in line:
                    continue
                try:
                    record = json.loads(line)
                    usage = record["payload"]["info"]["total_token_usage"]
                    current = int(usage["total_tokens"])
                    timestamp = dt.datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    continue
                delta = current - previous if current >= previous else current
                previous = current
                if delta <= 0:
                    continue
                day = timestamp.astimezone(LOCAL_TZ).date().isoformat()
                totals[day] = totals.get(day, 0) + delta
    return totals


def streaks(totals: dict[str, int], today: dt.date) -> tuple[int, int]:
    days = sorted(dt.date.fromisoformat(day) for day, tokens in totals.items() if tokens > 0)
    if not days:
        return 0, 0
    longest = run = 1
    for previous, current in zip(days, days[1:]):
        run = run + 1 if current == previous + dt.timedelta(days=1) else 1
        longest = max(longest, run)
    active = set(days)
    cursor = today if today in active else today - dt.timedelta(days=1)
    current = 0
    while cursor in active:
        current += 1
        cursor -= dt.timedelta(days=1)
    return longest, current


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex")
    args = parser.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    totals = daily_totals(args.codex_dir)
    collected_total = sum(totals.values())

    baseline = data.setdefault("sync_baseline", {})
    if "collected_tokens" not in baseline:
        baseline["collected_tokens"] = collected_total
        baseline["lifetime_tokens"] = int(data.get("lifetime_tokens", collected_total))
    data["lifetime_tokens"] = int(baseline["lifetime_tokens"]) + max(
        0, collected_total - int(baseline["collected_tokens"])
    )
    data["daily"] = [{"date": day, "tokens": totals[day]} for day in sorted(totals)]
    data["peak_tokens"] = max(int(data.get("peak_tokens", 0)), max(totals.values(), default=0))

    now = dt.datetime.now(LOCAL_TZ)
    longest, current = streaks(totals, now.date())
    data["longest_streak"] = max(int(data.get("longest_streak", 0)), longest)
    data["current_streak"] = current
    data["updated_at"] = now.strftime("%Y-%m-%d %H:%M CST")
    data["source"] = "local Codex token_count events"

    args.data.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # GitHub's image proxy can otherwise keep serving an older SVG after the
    # data file changes. A content-derived README version stamp gives each
    # telemetry refresh a fresh image URL without changing the asset path.
    readme = args.data.parent.parent / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        version = now.strftime("%Y%m%d%H%M")
        refreshed = re.sub(
            r"assets/chatgpt-activity\.svg(?:\?v=[^\"]+)?",
            f"assets/chatgpt-activity.svg?v={version}",
            content,
        )
        if refreshed != content:
            readme.write_text(refreshed, encoding="utf-8")


if __name__ == "__main__":
    main()
