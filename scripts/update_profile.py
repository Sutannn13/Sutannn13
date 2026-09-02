#!/usr/bin/env python3
"""Refresh the self-hosted data visuals used by the GitHub profile.

GitHub and WakaTime failures preserve the last known-good assets. The only
optional runtime dependency is Pillow, used for the contribution animation.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # Keep the previous animation when Pillow is unavailable.
    Image = ImageDraw = ImageFont = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
ASSETS_PATH = ROOT / "assets"
STATS_PATH = ASSETS_PATH / "live-stats.svg"
ACTIVITY_PATH = ASSETS_PATH / "activity-loop.gif"
PROJECTS_PATH = ASSETS_PATH / "projects"
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

PROJECTS = [
    {
        "repo": "Skill-Path-AI",
        "file": "skill-path-ai.svg",
        "label": "01 / AI CAREER PRODUCT",
        "title": "Skill Path AI",
        "description": "Transforms a user's current profile into a practical skill roadmap and career direction.",
        "live": "https://skill-path-ai-kappa.vercel.app",
    },
    {
        "repo": "mau-s-kitchen",
        "file": "maus-kitchen.svg",
        "label": "02 / BUSINESS OPERATIONS",
        "title": "Mau's Kitchen",
        "description": "A customer and admin experience for menu discovery, ordering, and daily operations.",
        "live": "https://maus-kitchen.pages.dev",
    },
    {
        "repo": "press-release-auto-generate",
        "file": "press-release.svg",
        "label": "03 / WORKFLOW AUTOMATION",
        "title": "Press Release Generator",
        "description": "Turns structured 5W+1H field notes into consistent, usable communication drafts.",
        "live": "",
    },
    {
        "repo": "solar-system-ar",
        "file": "solar-system-ar.svg",
        "label": "04 / IMMERSIVE WEB",
        "title": "Solar System AR",
        "description": "An interactive browser learning experience combining product UI and augmented reality.",
        "live": "https://solar-system-ar-sigma.vercel.app",
    },
]


def request_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = dict(headers)
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def fetch_contributions() -> dict[str, Any]:
    if not GITHUB_TOKEN:
        return {}
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { contributionCount date weekday }
            }
          }
        }
      }
    }
    """
    result = request_json(
        "https://api.github.com/graphql",
        GITHUB_HEADERS,
        {"query": query, "variables": {"login": OWNER}},
    )
    if not isinstance(result, dict) or result.get("errors"):
        raise RuntimeError(f"Unexpected GitHub GraphQL response: {result.get('errors') if isinstance(result, dict) else 'invalid data'}")
    user = ((result.get("data") or {}).get("user") or {})
    return ((user.get("contributionsCollection") or {}).get("contributionCalendar") or {})


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

    contributions: dict[str, Any] = {}
    try:
        contributions = fetch_contributions()
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
        print(f"Contribution calendar unavailable; preserving its last animation: {error}")

    return {
        "public_repos": int(user.get("public_repos") or len(public_repos)),
        "original_projects": len(original_repos),
        "stars": stars,
        "top_language": languages.most_common(1)[0][0] if languages else "N/A",
        "languages": dict(languages.most_common(6)),
        "repositories": [
            {
                "name": repo.get("name", ""),
                "language": repo.get("language") or "Multi-stack",
                "stars": int(repo.get("stargazers_count") or 0),
                "pushed_at": repo.get("pushed_at") or "",
            }
            for repo in original_repos
        ],
        "contributions": contributions,
    }


def load_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def svg_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def write_if_changed(path: Path, content: str | bytes) -> bool:
    previous = path.read_bytes() if path.exists() else b""
    output = content.encode("utf-8") if isinstance(content, str) else content
    if previous == output:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)
    return True


def render_stats_svg(snapshot: dict[str, Any]) -> str:
    metrics = [
        ("PUBLIC REPOS", snapshot.get("public_repos", 0)),
        ("ORIGINAL BUILDS", snapshot.get("original_projects", 0)),
        ("STARS EARNED", snapshot.get("stars", 0)),
        ("TOP LANGUAGE", snapshot.get("top_language", "N/A")),
    ]
    metric_blocks = []
    for index, (label, value) in enumerate(metrics):
        x = 62 + index * 280
        metric_blocks.append(
            f'<text x="{x}" y="130" class="metric">{svg_text(value)}</text>'
            f'<text x="{x}" y="158" class="label">{svg_text(label)}</text>'
        )

    languages = snapshot.get("languages") or {}
    total = max(sum(int(value) for value in languages.values()), 1)
    cursor = 62.0
    segments, legend = [], []
    for index, (language, count) in enumerate(languages.items()):
        count = int(count)
        width = 1076 * count / total
        color = LANGUAGE_COLORS.get(language, LANGUAGE_COLORS["Other"])
        segments.append(f'<rect x="{cursor:.1f}" y="246" width="{width:.1f}" height="14" fill="{color}" rx="7" />')
        legend_x = 62 + (index % 3) * 358
        legend_y = 300 + (index // 3) * 29
        legend.append(
            f'<circle cx="{legend_x + 6}" cy="{legend_y - 5}" r="5" fill="{color}" />'
            f'<text x="{legend_x + 20}" y="{legend_y}" class="legend">{svg_text(language)}  {round(count / total * 100)}%</text>'
        )
        cursor += width

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" role="img" aria-labelledby="title desc">
  <title id="title">Live GitHub observatory for Sutan Arlie Johan</title>
  <desc id="desc">Repository, original build, star, and primary-language statistics refreshed from GitHub.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#061020"/><stop offset=".55" stop-color="#0A1730"/><stop offset="1" stop-color="#111331"/></linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#22D3EE"/><stop offset=".52" stop-color="#6366F1"/><stop offset="1" stop-color="#A855F7"/></linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="24"/></filter>
  </defs>
  <style>
    .eyebrow{{fill:#67E8F9;font:700 15px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:2px}}
    .metric{{fill:#F8FAFC;font:700 38px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}
    .label{{fill:#91A4BD;font:600 13px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1.1px}}
    .section{{fill:#C9D8E8;font:600 15px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}
    .legend{{fill:#B9C9DB;font:500 14px ui-monospace,SFMono-Regular,Menlo,monospace}}
  </style>
  <rect width="1200" height="360" rx="18" fill="url(#bg)"/><circle cx="1060" cy="40" r="125" fill="#4F46E5" opacity=".18" filter="url(#glow)"/><circle cx="75" cy="340" r="105" fill="#06B6D4" opacity=".13" filter="url(#glow)"/>
  <rect x="1" y="1" width="1198" height="358" rx="17" fill="none" stroke="#27405F"/><rect x="62" y="37" width="44" height="4" rx="2" fill="url(#accent)"/><text x="120" y="45" class="eyebrow">REPOSITORY TELEMETRY / LIVE</text>
  {''.join(metric_blocks)}
  <line x1="62" y1="194" x2="1138" y2="194" stroke="#263953"/><text x="62" y="228" class="section">Language signal across original public repositories</text><rect x="62" y="246" width="1076" height="14" rx="7" fill="#1E293B"/>
  {''.join(segments)}{''.join(legend)}
</svg>'''


def repo_metadata(snapshot: dict[str, Any], name: str) -> dict[str, Any]:
    for repo in snapshot.get("repositories") or []:
        if str(repo.get("name", "")).lower() == name.lower():
            return repo
    return {"name": name, "language": "Multi-stack", "stars": 0, "pushed_at": ""}


def human_date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc).strftime("%b %Y").upper()
    except (ValueError, AttributeError):
        return "LIVE METADATA"


def render_project_svg(project: dict[str, str], metadata: dict[str, Any]) -> str:
    language = svg_text(metadata.get("language") or "Multi-stack")
    stars = int(metadata.get("stars") or 0)
    updated = human_date(str(metadata.get("pushed_at") or ""))
    deployment = "DEPLOYMENT LINKED" if project["live"] else "SOURCE AVAILABLE"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="580" height="245" viewBox="0 0 580 245" role="img" aria-labelledby="title desc">
  <title id="title">{svg_text(project['title'])}</title><desc id="desc">{svg_text(project['description'])}</desc>
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#071322"/><stop offset=".58" stop-color="#0C1730"/><stop offset="1" stop-color="#171238"/></linearGradient><linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#22D3EE"/><stop offset=".52" stop-color="#6366F1"/><stop offset="1" stop-color="#A855F7"/></linearGradient></defs>
  <style>.over{{fill:#67E8F9;font:700 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:1.5px}}.name{{fill:#F8FAFC;font:700 25px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}.body{{fill:#AFC2D7;font:500 14px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}}.meta{{fill:#BDD5E7;font:600 12px ui-monospace,SFMono-Regular,Menlo,monospace}}.status{{fill:#C4B5FD;font:700 11px ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.6px}}</style>
  <rect width="580" height="245" rx="17" fill="url(#bg)"/><rect x="1" y="1" width="578" height="243" rx="16" fill="none" stroke="#2A4160"/><rect x="0" y="0" width="580" height="3" rx="2" fill="url(#line)"/>
  <text x="34" y="43" class="over">{svg_text(project['label'])}</text><circle cx="528" cy="38" r="14" fill="#0D2436" stroke="#22D3EE"/><circle cx="528" cy="38" r="4" fill="#22D3EE"/>
  <text x="34" y="87" class="name">{svg_text(project['title'])}</text>
  <text x="34" y="121" class="body">{svg_text(project['description'][:70])}</text><text x="34" y="143" class="body">{svg_text(project['description'][70:])}</text>
  <line x1="34" y1="169" x2="546" y2="169" stroke="#263B55"/><circle cx="40" cy="198" r="5" fill="{LANGUAGE_COLORS.get(str(metadata.get('language')), '#64748B')}"/><text x="53" y="203" class="meta">{language}</text><text x="208" y="203" class="meta">★ {stars}</text><text x="284" y="203" class="meta">UPDATED {updated}</text>
  <rect x="34" y="218" width="145" height="2" rx="1" fill="url(#line)"/><text x="401" y="224" class="status">{deployment}</text>
</svg>'''


def contribution_days(calendar: dict[str, Any]) -> list[dict[str, Any]]:
    days = []
    for week in calendar.get("weeks") or []:
        days.extend(day for day in (week.get("contributionDays") or []) if isinstance(day, dict))
    return days[-364:]


def current_streak(days: list[dict[str, Any]]) -> int:
    by_date = {str(day.get("date")): int(day.get("contributionCount") or 0) for day in days}
    cursor = date.today()
    if by_date.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)
    streak = 0
    while by_date.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def load_activity_fonts() -> tuple[Any, Any, Any]:
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    mono = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    return (
        ImageFont.truetype(bold, 27),
        ImageFont.truetype(mono, 13),
        ImageFont.truetype(regular, 15),
    )


def render_activity_gif(calendar: dict[str, Any]) -> bytes | None:
    if Image is None or ImageDraw is None or ImageFont is None:
        print("Pillow is unavailable; keeping the previous contribution animation.")
        return None
    days = contribution_days(calendar)
    if not days:
        return None

    width, height, frame_count = 1200, 310, 32
    title_font, mono_font, body_font = load_activity_fonts()
    total = int(calendar.get("totalContributions") or sum(int(day.get("contributionCount") or 0) for day in days))
    active = sum(int(day.get("contributionCount") or 0) > 0 for day in days)
    streak = current_streak(days)
    maximum = max(int(day.get("contributionCount") or 0) for day in days) or 1

    parsed = []
    for day in days:
        try:
            parsed.append((date.fromisoformat(str(day.get("date"))), int(day.get("contributionCount") or 0)))
        except ValueError:
            continue
    if not parsed:
        return None
    first_sunday = parsed[0][0] - timedelta(days=(parsed[0][0].weekday() + 1) % 7)
    grid: dict[tuple[int, int], int] = {}
    for day_date, count in parsed:
        delta = (day_date - first_sunday).days
        grid[(delta // 7, (day_date.weekday() + 1) % 7)] = count
    week_count = min(52, max((week for week, _ in grid), default=51) + 1)
    week_shift = max(0, max((week for week, _ in grid), default=51) - 51)

    colors = [(18, 31, 49), (11, 87, 92), (8, 132, 139), (34, 197, 188), (103, 232, 249)]
    frames = []
    for frame in range(frame_count):
        image = Image.new("RGB", (width, height), (5, 12, 25))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.rounded_rectangle((1, 1, width - 2, height - 2), radius=18, fill=(7, 17, 34), outline=(43, 67, 96), width=1)
        draw.ellipse((1010, -120, 1260, 130), fill=(79, 70, 229, 38))
        draw.text((52, 37), "CONTRIBUTION SIGNAL", font=mono_font, fill=(103, 232, 249))
        draw.text((52, 66), "A year of shipping, in motion.", font=title_font, fill=(246, 250, 255))
        draw.text((760, 46), f"{total} CONTRIBUTIONS", font=mono_font, fill=(207, 225, 240))
        draw.text((760, 72), f"{active} ACTIVE DAYS   /   {streak} DAY STREAK", font=mono_font, fill=(166, 193, 215))
        draw.line((52, 112, 1148, 112), fill=(38, 58, 82), width=1)

        cell, gap = 13, 4
        grid_x, grid_y = 190, 139
        scan_week = int((frame / frame_count) * 56) - 2
        for week in range(52):
            x = grid_x + week * (cell + gap)
            if abs(week - scan_week) <= 2:
                alpha = max(0, 28 - abs(week - scan_week) * 9)
                draw.rounded_rectangle((x - 3, grid_y - 8, x + cell + 3, grid_y + 7 * (cell + gap)), radius=5, fill=(34, 211, 238, alpha))
            for weekday in range(7):
                count = grid.get((week + week_shift, weekday), 0)
                level = 0 if count == 0 else min(4, 1 + int(3 * math.sqrt(count / maximum)))
                color = colors[level]
                pulse = 0
                if count > 0 and (week * 7 + weekday + frame) % 31 == 0:
                    pulse = 16
                y = grid_y + weekday * (cell + gap)
                draw.rounded_rectangle((x, y, x + cell, y + cell), radius=3, fill=(*tuple(min(255, c + pulse) for c in color), 255))

        draw.text((52, 144), "MON", font=mono_font, fill=(120, 149, 174))
        draw.text((52, 178), "WED", font=mono_font, fill=(120, 149, 174))
        draw.text((52, 212), "FRI", font=mono_font, fill=(120, 149, 174))
        draw.text((52, 259), "LOW", font=mono_font, fill=(105, 133, 158))
        for index, color in enumerate(colors):
            x = 91 + index * 20
            draw.rounded_rectangle((x, 258, x + 13, 271), radius=3, fill=color)
        draw.text((194, 259), "HIGH", font=mono_font, fill=(105, 133, 158))
        draw.text((928, 259), "SOURCE / GITHUB GRAPHQL", font=mono_font, fill=(105, 133, 158))
        frames.append(image)

    palette = frames[0].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for frame in frames]
    from io import BytesIO

    output = BytesIO()
    indexed[0].save(output, format="GIF", save_all=True, append_images=indexed[1:], duration=95, loop=0, optimize=True, disposal=1)
    return output.getvalue()


def fetch_wakatime() -> dict[str, Any]:
    encoded_key = base64.b64encode(WAKATIME_API_KEY.encode("utf-8")).decode("ascii")
    headers = {"Accept": "application/json", "Authorization": f"Basic {encoded_key}", "User-Agent": "Sutannn13-profile-readme"}
    result = request_json("https://wakatime.com/api/v1/users/current/stats/last_7_days", headers)
    if not isinstance(result, dict) or not isinstance(result.get("data"), dict):
        raise RuntimeError("Unexpected WakaTime response")
    return result["data"]


def render_wakatime_markdown(stats: dict[str, Any]) -> str:
    languages = [item for item in stats.get("languages", []) if item.get("name")][:6]
    total = stats.get("human_readable_total") or stats.get("human_readable_daily_average") or "No recorded time"
    rows = []
    for item in languages:
        name = str(item.get("name", "Other"))[:18]
        percent = float(item.get("percent") or 0)
        filled = max(0, min(20, round(percent / 5)))
        rows.append(f"{name:<18} {'█' * filled}{'░' * (20 - filled)} {percent:>5.1f}%  {item.get('text', '')}")
    chart = "\n".join(rows) if rows else "No WakaTime language activity was recorded."
    return f"**Last 7 days:** {total}\n\n```text\n{chart}\n```"


def update_wakatime_section(readme: str, block: str) -> str:
    pattern = re.compile(r"(<!--START_SECTION:waka-->).*?(<!--END_SECTION:waka-->)", flags=re.DOTALL)
    if not pattern.search(readme):
        raise RuntimeError("WakaTime markers are missing from README.md")
    return pattern.sub(rf"\1\n{block}\n\2", readme, count=1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, help="Use an offline public-data snapshot instead of calling GitHub.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        snapshot = load_snapshot(args.snapshot) if args.snapshot else fetch_github_snapshot()
        stats_changed = write_if_changed(STATS_PATH, render_stats_svg(snapshot))
        print("Repository telemetry updated." if stats_changed else "Repository telemetry already current.")

        project_changes = 0
        for project in PROJECTS:
            metadata = repo_metadata(snapshot, project["repo"])
            project_changes += write_if_changed(PROJECTS_PATH / project["file"], render_project_svg(project, metadata))
        print(f"Project cards updated: {project_changes}.")

        activity = render_activity_gif(snapshot.get("contributions") or {})
        if activity is not None:
            changed = write_if_changed(ACTIVITY_PATH, activity)
            print("Contribution animation updated." if changed else "Contribution animation already current.")
        else:
            print("No contribution calendar available; keeping the previous animation.")
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
        print(f"GitHub data unavailable; keeping the last known-good assets: {error}")

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
