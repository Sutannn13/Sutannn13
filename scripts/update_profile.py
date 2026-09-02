#!/usr/bin/env python3
"""Refresh the local GitHub snapshot and optional WakaTime section.

The script is intentionally dependency-free so the scheduled workflow has fewer
moving parts. Network failures keep the last known-good profile instead of
failing the whole Action and sending noisy notifications.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
STATS_PATH = ROOT / "assets" / "live-stats.svg"
OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "Sutannn13")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
WAKATIME_API_KEY = os.getenv("WAKATIME_API_KEY", "")

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Sutannn13-profile-readme",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

LANGUAGE_COLORS = {
    "TypeScript": "#5EA2EF",
    "JavaScript": "#F5D547",
    "CSS": "#8B5CF6",
    "Blade": "#F97316",
    "PHP": "#A78BFA",
    "HTML": "#FB7185",
    "Python": "#38BDF8",
    "Other": "#64748B",
}


def request_json(url: str, headers: dict[str, str]) -> dict[str, Any] | list[Any]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch_github_snapshot() -> dict[str, Any]:
    user_url = f"https://api.github.com/users/{urllib.parse.quote(OWNER)}"
    user = request_json(user_url, GITHUB_HEADERS)
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected GitHub user response")

    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        repo_url = (
            f"https://api.github.com/users/{urllib.parse.quote(OWNER)}/repos"
            f"?type=owner&sort=pushed&per_page=100&page={page}"
        )
        chunk = request_json(repo_url, GITHUB_HEADERS)
        if not isinstance(chunk, list):
            raise RuntimeError("Unexpected GitHub repository response")
        repos.extend(item for item in chunk if isinstance(item, dict))
        if len(chunk) < 100:
            break
        page += 1

    public_repos = [repo for repo in repos if not repo.get("private")]
    original_repos = [repo for repo in public_repos if not repo.get("fork")]
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in original_repos)
    languages = Counter(
        str(repo["language"])
        for repo in original_repos
        if repo.get("language") and not repo.get("archived")
    )

    return {
        "public_repos": int(user.get("public_repos") or len(public_repos)),
        "original_projects": len(original_repos),
        "stars": stars,
        "top_language": languages.most_common(1)[0][0] if languages else "N/A",
        "languages": dict(languages.most_common(6)),
    }


def load_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def svg_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_stats_svg(snapshot: dict[str, Any]) -> str:
    metrics = [
        ("PUBLIC REPOS", snapshot.get("public_repos", 0)),
        ("ORIGINAL PROJECTS", snapshot.get("original_projects", 0)),
        ("STARS EARNED", snapshot.get("stars", 0)),
        ("TOP LANGUAGE", snapshot.get("top_language", "N/A")),
    ]
    metric_blocks: list[str] = []
    for index, (label, value) in enumerate(metrics):
        x = 62 + index * 280
        metric_blocks.append(
            f'<text x="{x}" y="126" class="metric">{svg_text(value)}</text>'
            f'<text x="{x}" y="153" class="label">{svg_text(label)}</text>'
        )

    languages = snapshot.get("languages") or {}
    total = max(sum(int(value) for value in languages.values()), 1)
    bar_x = 62
    bar_y = 238
    bar_width = 1076
    segments: list[str] = []
    legend: list[str] = []
    cursor = bar_x
    for index, (language, count) in enumerate(languages.items()):
        count = int(count)
        width = bar_width * count / total
        color = LANGUAGE_COLORS.get(language, LANGUAGE_COLORS["Other"])
        segments.append(
            f'<rect x="{cursor:.1f}" y="{bar_y}" width="{width:.1f}" height="16" '
            f'fill="{color}" rx="8" />'
        )
        legend_x = 62 + (index % 3) * 358
        legend_y = 292 + (index // 3) * 29
        percent = round(count / total * 100)
        legend.append(
            f'<circle cx="{legend_x + 6}" cy="{legend_y - 5}" r="5" fill="{color}" />'
            f'<text x="{legend_x + 20}" y="{legend_y}" class="legend">'
            f'{svg_text(language)}  {percent}%</text>'
        )
        cursor += width

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" role="img" aria-labelledby="title desc">
  <title id="title">Live GitHub snapshot for Sutan Arlie Johan</title>
  <desc id="desc">Public repository, original project, star, and primary-language statistics.</desc>
  <defs>
    <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07101F" />
      <stop offset="0.55" stop-color="#0B1630" />
      <stop offset="1" stop-color="#101331" />
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#22D3EE" />
      <stop offset="0.5" stop-color="#6366F1" />
      <stop offset="1" stop-color="#A855F7" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="24" />
    </filter>
  </defs>
  <style>
    .eyebrow {{ fill:#67E8F9; font:700 15px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:2px; }}
    .metric {{ fill:#F8FAFC; font:700 38px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .label {{ fill:#91A4BD; font:600 13px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:1.2px; }}
    .section {{ fill:#C9D8E8; font:600 15px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; }}
    .legend {{ fill:#B9C9DB; font:500 14px ui-monospace, SFMono-Regular, Menlo, monospace; }}
  </style>
  <rect width="1200" height="360" rx="18" fill="url(#background)" />
  <circle cx="1035" cy="44" r="110" fill="#4F46E5" opacity="0.20" filter="url(#glow)" />
  <circle cx="90" cy="330" r="95" fill="#06B6D4" opacity="0.15" filter="url(#glow)" />
  <rect x="1" y="1" width="1198" height="358" rx="17" fill="none" stroke="#27405F" />
  <rect x="62" y="37" width="44" height="4" rx="2" fill="url(#line)" />
  <text x="120" y="45" class="eyebrow">LIVE GITHUB SNAPSHOT</text>
  {''.join(metric_blocks)}
  <line x1="62" y1="190" x2="1138" y2="190" stroke="#263953" />
  <text x="62" y="221" class="section">Primary languages across original public repositories</text>
  <rect x="62" y="238" width="1076" height="16" rx="8" fill="#1E293B" />
  {''.join(segments)}
  {''.join(legend)}
</svg>
'''


def fetch_wakatime() -> dict[str, Any]:
    encoded_key = base64.b64encode(WAKATIME_API_KEY.encode("utf-8")).decode("ascii")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {encoded_key}",
        "User-Agent": "Sutannn13-profile-readme",
    }
    result = request_json(
        "https://wakatime.com/api/v1/users/current/stats/last_7_days",
        headers,
    )
    if not isinstance(result, dict) or not isinstance(result.get("data"), dict):
        raise RuntimeError("Unexpected WakaTime response")
    return result["data"]


def render_wakatime_markdown(stats: dict[str, Any]) -> str:
    languages = [item for item in stats.get("languages", []) if item.get("name")][:6]
    total = stats.get("human_readable_total") or stats.get("human_readable_daily_average") or "No recorded time"
    rows: list[str] = []
    for item in languages:
        name = str(item.get("name", "Other"))[:18]
        percent = float(item.get("percent") or 0)
        filled = max(0, min(20, round(percent / 5)))
        bar = "█" * filled + "░" * (20 - filled)
        rows.append(f"{name:<18} {bar} {percent:>5.1f}%  {item.get('text', '')}")

    chart = "\n".join(rows) if rows else "No WakaTime language activity was recorded."
    return f"**Last 7 days:** {total}\n\n```text\n{chart}\n```"


def update_wakatime_section(readme: str, block: str) -> str:
    pattern = re.compile(
        r"(<!--START_SECTION:waka-->).*?(<!--END_SECTION:waka-->)",
        flags=re.DOTALL,
    )
    if not pattern.search(readme):
        raise RuntimeError("WakaTime markers are missing from README.md")
    return pattern.sub(rf"\1\n{block}\n\2", readme, count=1)


def write_if_changed(path: Path, content: str) -> bool:
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if previous == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="Use an offline public-data snapshot instead of calling GitHub.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        snapshot = load_snapshot(args.snapshot) if args.snapshot else fetch_github_snapshot()
        changed = write_if_changed(STATS_PATH, render_stats_svg(snapshot))
        print("GitHub snapshot updated." if changed else "GitHub snapshot already current.")
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
        print(f"GitHub data unavailable; keeping the last known-good snapshot: {error}")
        return 0

    if not WAKATIME_API_KEY:
        print("WakaTime secret is not configured; leaving its README block unchanged.")
        return 0

    try:
        readme = README_PATH.read_text(encoding="utf-8")
        updated = update_wakatime_section(readme, render_wakatime_markdown(fetch_wakatime()))
        changed = write_if_changed(README_PATH, updated)
        print("WakaTime block updated." if changed else "WakaTime block already current.")
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
        print(f"WakaTime unavailable; keeping the last known-good block: {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
