#!/usr/bin/env python3
"""Generate agency-grade dual-theme animated 3D SVGs (Superior UI + Frontend Taste).

Materiality & craft upgrades:
- Studio-lit 3D isometric facets with directional gradients, top specular ridge lines,
  and soft Gaussian-blurred tinted contact shadows (never flat solid polygons).
- Machined Double-Bezel (Doppelrand) enclosures on primary focal surfaces + quiet hairline
  enclosures on supporting modules so visual hierarchy breathes instead of card soup.
- Asymmetric 57% / 41.5% featured project split with exact height parity (684x296 & 498x296).
- Button-in-Button trailing icon islands on primary tactile action bars.
- Strict eyebrow restraint, WCAG AA contrast across Dark & Light, prefers-reduced-motion,
  zero em dashes, zero decorative emojis, zero fabricated metrics.
"""

from __future__ import annotations

import html
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

THEMES = {
    "dark": {
        "shell": "#0f1217",
        "shell_border": "#232934",
        "surface": "#151920",
        "surface_deep": "#11141a",
        "surface_warm": "#191719",
        "raised": "#1d222c",
        "border": "#2a313d",
        "border_strong": "#5b6575",
        "rim_top": "#ffffff",
        "rim_op": "0.11",
        "text_primary": "#f3efe6",
        "text_secondary": "#b6b1a6",
        "text_muted": "#969187",
        "accent": "#e57a52",
        "accent_hi": "#f7a889",
        "accent_mid": "#d96c43",
        "accent_lo": "#8c3b1e",
        "brass": "#d9a45b",
        "brass_hi": "#f0cb8d",
        "brass_mid": "#c48d44",
        "brass_lo": "#7c5522",
        "slate_hi": "#394252",
        "slate_mid": "#262d3a",
        "slate_lo": "#181d26",
        "live": "#72c495",
        "live_bg": "#14261d",
        "shadow": "#07090d",
        "ridge": "#fff4e6",
        "ridge_op": "0.26",
        "grain_op": "0.026",
    },
    "light": {
        "shell": "#ebe5da",
        "shell_border": "#d2cabd",
        "surface": "#f7f4ee",
        "surface_deep": "#f1ece3",
        "surface_warm": "#f9f3eb",
        "raised": "#ece6db",
        "border": "#d6cfc2",
        "border_strong": "#766f64",
        "rim_top": "#ffffff",
        "rim_op": "0.85",
        "text_primary": "#161614",
        "text_secondary": "#4a4741",
        "text_muted": "#5c5850",
        "accent": "#b5451b",
        "accent_hi": "#df6b40",
        "accent_mid": "#b5451b",
        "accent_lo": "#78280b",
        "brass": "#7d5318",
        "brass_hi": "#ad7d33",
        "brass_mid": "#7d5318",
        "brass_lo": "#4f330a",
        "slate_hi": "#ede7dc",
        "slate_mid": "#dbd3c5",
        "slate_lo": "#c2b9a9",
        "live": "#1e6b43",
        "live_bg": "#e3f0e8",
        "shadow": "#a99f8e",
        "ridge": "#ffffff",
        "ridge_op": "0.68",
        "grain_op": "0.022",
    },
}

ORIGINAL_LANG_COUNTS = [
    ("TS", "TypeScript", 9, "accent"),
    ("JS", "JavaScript", 4, "brass"),
    ("PY", "Python", 2, "slate"),
    ("CSS", "CSS", 2, "slate"),
    ("PHP", "PHP", 1, "slate"),
    ("BLD", "Blade", 1, "slate"),
    ("HTML", "HTML", 1, "slate"),
]

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"
MONO = "'Cascadia Mono', Consolas, ui-monospace, monospace"


def shared_3d_defs(t: dict) -> str:
    """Reusable studio-lit 3D facet gradients, tinted Gaussian shadows, and micro-grain."""
    return f"""  <defs>
    <filter id="sblur" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="5.5"/>
    </filter>
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>
    </filter>
    <linearGradient id="sl-t" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{t['slate_hi']}"/><stop offset="100%" stop-color="{t['slate_mid']}"/></linearGradient>
    <linearGradient id="sl-l" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{t['slate_mid']}"/><stop offset="100%" stop-color="{t['slate_lo']}"/></linearGradient>
    <linearGradient id="sl-r" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{t['slate_lo']}"/><stop offset="100%" stop-color="{t['shadow']}"/></linearGradient>

    <linearGradient id="ac-t" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{t['accent_hi']}"/><stop offset="100%" stop-color="{t['accent_mid']}"/></linearGradient>
    <linearGradient id="ac-l" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{t['accent_mid']}"/><stop offset="100%" stop-color="{t['accent_lo']}"/></linearGradient>
    <linearGradient id="ac-r" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{t['accent_lo']}"/><stop offset="100%" stop-color="{t['shadow']}"/></linearGradient>

    <linearGradient id="br-t" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{t['brass_hi']}"/><stop offset="100%" stop-color="{t['brass_mid']}"/></linearGradient>
    <linearGradient id="br-l" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{t['brass_mid']}"/><stop offset="100%" stop-color="{t['brass_lo']}"/></linearGradient>
    <linearGradient id="br-r" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{t['brass_lo']}"/><stop offset="100%" stop-color="{t['shadow']}"/></linearGradient>

    <radialGradient id="spot-warm" cx="78%" cy="48%" r="48%">
      <stop offset="0%" stop-color="{t['accent']}" stop-opacity="0.13"/>
      <stop offset="100%" stop-color="{t['accent']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="spot-brass" cx="76%" cy="50%" r="46%">
      <stop offset="0%" stop-color="{t['brass']}" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="{t['brass']}" stop-opacity="0"/>
    </radialGradient>
  </defs>"""


def studio_prism(
    cx: float,
    base_y: float,
    rx: float,
    ry: float,
    height: float,
    tone: str,
    t: dict,
    ridge: bool = True,
) -> str:
    """3D isometric prism shaded with directional studio gradients and specular top bevel ridge."""
    p = {"slate": "sl", "accent": "ac", "brass": "br"}[tone]
    ty = base_y - height
    top_pts = f"{cx:.1f},{ty - ry:.1f} {cx + rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx - rx:.1f},{ty:.1f}"
    left_pts = f"{cx - rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx:.1f},{base_y + ry:.1f} {cx - rx:.1f},{base_y:.1f}"
    right_pts = f"{cx + rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx:.1f},{base_y + ry:.1f} {cx + rx:.1f},{base_y:.1f}"
    ridge_svg = (
        f'<polyline points="{cx - rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx + rx:.1f},{ty:.1f}" '
        f'fill="none" stroke="{t["ridge"]}" stroke-opacity="{t["ridge_op"]}" stroke-width="1.15" stroke-linejoin="round"/>'
        if ridge
        else ""
    )
    return (
        f'<polygon points="{left_pts}" fill="url(#{p}-l)"/>'
        f'<polygon points="{right_pts}" fill="url(#{p}-r)"/>'
        f'<polygon points="{top_pts}" fill="url(#{p}-t)"/>'
        f"{ridge_svg}"
    )


def double_bezel_frame(w: int, h: int, t: dict, surface: str | None = None, spot: str = "", grain: bool = True) -> str:
    """Machined Doppelrand (Double-Bezel) nested container with concentric radii and 1px top specular rim."""
    inner_bg = surface or t["surface"]
    pad = 6
    spot_el = f'<rect x="{pad}" y="{pad}" width="{w-2*pad}" height="{h-2*pad}" rx="10" fill="url(#{spot})"/>' if spot else ""
    grain_el = f'<rect x="{pad}" y="{pad}" width="{w-2*pad}" height="{h-2*pad}" rx="10" filter="url(#grain)" opacity="{t["grain_op"]}"/>' if grain else ""
    return (
        f'<rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="16" fill="{t["shell"]}" stroke="{t["shell_border"]}" stroke-width="1.4"/>'
        f'<rect x="{pad}" y="{pad}" width="{w-2*pad}" height="{h-2*pad}" rx="10" fill="{inner_bg}" stroke="{t["border"]}" stroke-width="1"/>'
        f"{spot_el}{grain_el}"
        f'<line x1="{pad+12}" y1="{pad+1}" x2="{w-pad-12}" y2="{pad+1}" stroke="{t["rim_top"]}" stroke-opacity="{t["rim_op"]}" stroke-width="1"/>'
    )


def quiet_panel_frame(w: int, h: int, t: dict, surface: str | None = None, spot: str = "") -> str:
    """Refined recessed architectural surface without heavy chrome (prevents card soup)."""
    bg = surface or t["surface"]
    spot_el = f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12" fill="url(#{spot})"/>' if spot else ""
    return (
        f'<rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="12" fill="{bg}" stroke="{t["border"]}" stroke-width="1.15"/>'
        f"{spot_el}"
        f'<line x1="16" y1="1.6" x2="{w-16}" y2="1.6" stroke="{t["rim_top"]}" stroke-opacity="{t["rim_op"]}" stroke-width="1"/>'
    )


def build_action_tile(t: dict, title: str, subtitle: str, glyph: str, accent_bar: bool = False, delay: float = 0.0) -> str:
    """Machined tactile navigation tile (260x76) with Button-in-Button trailing chevron island."""
    w, h = 260, 76
    bar_col = t["accent"] if accent_bar else t["brass"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}: {html.escape(subtitle)}">
  <style>
    @keyframes sweep {{
      0%, 74% {{ transform: translateX(-290px); opacity: 0; }}
      84% {{ opacity: 0.4; }}
      94% {{ opacity: 0.4; }}
      100% {{ transform: translateX(290px); opacity: 0; }}
    }}
    @keyframes glyphBob {{
      0%, 100% {{ transform: translateY(0px); }}
      50% {{ transform: translateY(-2.5px); }}
    }}
    .sheen {{ animation: sweep 7.2s cubic-bezier(0.32, 0.72, 0, 1) {delay:.2f}s infinite; }}
    .gbob {{ animation: glyphBob 4.6s cubic-bezier(0.32, 0.72, 0, 1) {delay:.2f}s infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .sheen, .gbob {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  <defs>
    <clipPath id="tc"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12"/></clipPath>
    <linearGradient id="sg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{bar_col}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{bar_col}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{bar_col}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  {quiet_panel_frame(w, h, t)}
  <g clip-path="url(#tc)"><rect x="0" y="0" width="96" height="{h}" fill="url(#sg)" class="sheen"/></g>
  <g class="gbob">{glyph}</g>
  <text x="68" y="36" font-family="{SANS}" font-size="17" font-weight="700" letter-spacing="-0.2" fill="{t['text_primary']}">{html.escape(title)}</text>
  <text x="68" y="56" font-family="{MONO}" font-size="12" fill="{t['text_muted']}">{html.escape(subtitle)}</text>
  <!-- Button-in-Button trailing architectural indicator island -->
  <circle cx="228" cy="38" r="14" fill="{t['raised']}" stroke="{t['border']}" stroke-width="1"/>
  <path d="M225,33 L231,38 L225,43" fill="none" stroke="{bar_col}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def build_action_tiles(t: dict) -> dict[str, str]:
    g_port = studio_prism(37, 50, 12.5, 5.8, 14, "accent", t)
    g_repo = studio_prism(37, 54, 12.5, 5.8, 6.5, "slate", t) + studio_prism(37, 43, 12.5, 5.8, 6.5, "brass", t)
    g_link = studio_prism(31, 52, 9, 4.2, 13, "slate", t) + studio_prism(44, 48, 9, 4.2, 13, "accent", t)
    g_mail = studio_prism(37, 50, 13.5, 6.2, 11, "brass", t)
    return {
        "btn-portfolio": build_action_tile(t, "Portfolio", "sutan.dev", g_port, accent_bar=True, delay=0.0),
        "btn-repos": build_action_tile(t, "Repositories", "22 public", g_repo, accent_bar=False, delay=0.8),
        "btn-linkedin": build_action_tile(t, "LinkedIn", "Profile", g_link, accent_bar=False, delay=1.6),
        "btn-email": build_action_tile(t, "Email", "Direct", g_mail, accent_bar=True, delay=2.4),
    }


def build_cta_bar(t: dict, label: str, tag: str, primary: bool = True) -> str:
    """Machined half-width tactile CTA bar (580x62) with Button-in-Button trailing island."""
    w, h = 580, 62
    stroke = t["accent"] if primary else t["border"]
    icon_col = t["accent"] if primary else t["text_primary"]
    tag_bg = t["live_bg"] if (primary and tag == "LIVE SITE") else t["raised"]
    tag_fg = t["live"] if (primary and tag == "LIVE SITE") else (t["accent"] if primary else t["text_secondary"])
    tag_stroke = t["live"] if (primary and tag == "LIVE SITE") else t["border"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(label)} ({html.escape(tag)})">
  <style>
    @keyframes barSweep {{
      0%, 74% {{ transform: translateX(-620px); opacity: 0; }}
      85% {{ opacity: 0.32; }}
      95% {{ opacity: 0.32; }}
      100% {{ transform: translateX(620px); opacity: 0; }}
    }}
    @keyframes nudge {{
      0%, 100% {{ transform: translateX(0px); }}
      50% {{ transform: translateX(2.5px); }}
    }}
    .bsweep {{ animation: barSweep 7.6s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .nudge {{ animation: nudge 3.8s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .bsweep, .nudge {{ animation: none !important; }} }}
  </style>
  <defs>
    <clipPath id="bc"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12"/></clipPath>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{icon_col}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{icon_col}" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="{icon_col}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="12" fill="{t['surface']}" stroke="{stroke}" stroke-width="1.3"/>
  <line x1="16" y1="1.6" x2="{w-16}" y2="1.6" stroke="{t['rim_top']}" stroke-opacity="{t['rim_op']}" stroke-width="1"/>
  <g clip-path="url(#bc)"><rect x="0" y="0" width="170" height="{h}" fill="url(#bg)" class="bsweep"/></g>

  <text x="26" y="37" font-family="{SANS}" font-size="17" font-weight="700" letter-spacing="-0.2" fill="{t['text_primary']}">{html.escape(label)}</text>

  <rect x="{w-196}" y="17" width="122" height="28" rx="6" fill="{tag_bg}" stroke="{tag_stroke}" stroke-width="1"/>
  <text x="{w-135}" y="35" text-anchor="middle" font-family="{MONO}" font-size="11.5" font-weight="700" fill="{tag_fg}">{html.escape(tag)}</text>

  <!-- Button-in-Button trailing icon island -->
  <circle cx="{w-36}" cy="31" r="16" fill="{t['raised']}" stroke="{t['border']}" stroke-width="1"/>
  <path d="M{w-39},26 L{w-33},31 L{w-39},36" fill="none" stroke="{icon_col}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" class="nudge"/>
</svg>
"""


def build_section_strip(t: dict, index: str, title: str, meta: str) -> str:
    """Clean editorial sans-serif section divider with slow kinetic architectural vernier."""
    w, h = 1200, 58
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}: {html.escape(meta)}">
  <style>
    @keyframes vernier {{
      0% {{ transform: translateX(0px); }}
      50% {{ transform: translateX(240px); }}
      100% {{ transform: translateX(0px); }}
    }}
    .vn {{ animation: vernier 9s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .vn {{ animation: none !important; }} }}
  </style>
  <line x1="0" y1="48" x2="{w}" y2="48" stroke="{t['border']}" stroke-width="1.2"/>
  <rect x="0" y="46.8" width="84" height="2.6" fill="{t['accent']}" class="vn"/>
  <text x="0" y="34" font-family="{MONO}" font-size="13.5" font-weight="700" fill="{t['accent']}">{html.escape(index)}</text>
  <text x="38" y="36" font-family="{SANS}" font-size="27" font-weight="700" letter-spacing="-0.6" fill="{t['text_primary']}">{html.escape(title)}</text>
  <text x="{w}" y="34" text-anchor="end" font-family="{SANS}" font-size="13.5" fill="{t['text_muted']}">{html.escape(meta)}</text>
</svg>
"""


def build_architecture_svg(t: dict) -> str:
    """Studio-lit 3D Isometric System Architecture inside a recessed obsidian/travertine stage."""
    w, h = 1200, 424
    s1_base = studio_prism(210, 290, 58, 27, 16, "slate", t)
    s1_mid = studio_prism(210, 263, 58, 27, 16, "slate", t)
    s1_top = studio_prism(210, 236, 58, 27, 16, "accent", t)

    s2_plinth = studio_prism(600, 296, 72, 33, 15, "slate", t)
    s2_core = studio_prism(600, 277, 40, 19, 48, "accent", t)
    s2_cap = studio_prism(600, 222, 48, 22, 13, "brass", t)

    s3_p1 = studio_prism(990, 292, 62, 28, 11, "slate", t)
    s3_p2 = studio_prism(990, 263, 54, 25, 11, "slate", t)
    s3_p3 = studio_prism(990, 234, 44, 20, 11, "brass", t)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="How I build: From database schema to deployed product across Data and Domain, API and Automation, and Product Interface.">
  <style>
    @keyframes floatA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-7px); }} }}
    @keyframes floatB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-11px); }} }}
    @keyframes floatC {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes flowDash {{ from {{ stroke-dashoffset: 64; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes revDash {{ from {{ stroke-dashoffset: 0; }} to {{ stroke-dashoffset: 64; }} }}
    @keyframes pktFwd {{
      0% {{ transform: translateX(0px); opacity: 0; }}
      14% {{ opacity: 1; }}
      86% {{ opacity: 1; }}
      100% {{ transform: translateX(188px); opacity: 0; }}
    }}
    @keyframes pktBack {{
      0% {{ transform: translateX(188px); opacity: 0; }}
      14% {{ opacity: 0.9; }}
      86% {{ opacity: 0.9; }}
      100% {{ transform: translateX(0px); opacity: 0; }}
    }}
    @keyframes orbitRing {{
      0%, 100% {{ stroke-dashoffset: 0; opacity: 0.65; }}
      50% {{ stroke-dashoffset: 64; opacity: 1; }}
    }}
    .f-a {{ animation: floatA 4.8s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .f-b {{ animation: floatB 5.4s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .f-c {{ animation: floatC 5.0s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .f-b2 {{ animation: floatA 5.4s cubic-bezier(0.32, 0.72, 0, 1) 0.55s infinite; }}
    .f-c2 {{ animation: floatB 5.0s cubic-bezier(0.32, 0.72, 0, 1) 0.75s infinite; }}
    .conduit {{ stroke-dasharray: 6 10; animation: flowDash 2.4s linear infinite; }}
    .conduit-r {{ stroke-dasharray: 4 12; animation: revDash 3.2s linear infinite; }}
    .pkt1 {{ animation: pktFwd 2.6s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .pkt2 {{ animation: pktFwd 2.6s cubic-bezier(0.32, 0.72, 0, 1) 1.3s infinite; }}
    .pkt3 {{ animation: pktBack 3.4s cubic-bezier(0.32, 0.72, 0, 1) 0.5s infinite; }}
    .pkt4 {{ animation: pktBack 3.4s cubic-bezier(0.32, 0.72, 0, 1) 2.1s infinite; }}
    .ring {{ animation: orbitRing 7.4s linear infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .f-a, .f-b, .f-c, .f-b2, .f-c2, .conduit, .conduit-r, .pkt1, .pkt2, .pkt3, .pkt4, .ring {{ animation: none !important; }}
    }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t, surface=t['surface_deep'])}

  <!-- Clean editorial lead without eyebrow bloat -->
  <text x="48" y="64" font-family="{SANS}" font-size="25" font-weight="700" letter-spacing="-0.5" fill="{t['text_primary']}">From database schema to deployed product.</text>
  <text x="48" y="96" font-family="{SANS}" font-size="16" fill="{t['text_secondary']}">Information Technology student and backend-focused full-stack developer in Depok, Indonesia. Turning manual</text>
  <text x="48" y="120" font-family="{SANS}" font-size="16" fill="{t['text_secondary']}">processes and scattered operational data into dependable APIs, workflows, and clear web interfaces.</text>
  <line x1="48" y1="146" x2="{w-48}" y2="146" stroke="{t['border']}" stroke-width="1"/>

  <!-- Soft Gaussian-blurred tinted studio contact shadows -->
  <ellipse cx="210" cy="316" rx="74" ry="20" fill="{t['shadow']}" opacity="0.58" filter="url(#sblur)"/>
  <ellipse cx="600" cy="322" rx="86" ry="24" fill="{t['shadow']}" opacity="0.62" filter="url(#sblur)"/>
  <ellipse cx="990" cy="316" rx="74" ry="20" fill="{t['shadow']}" opacity="0.58" filter="url(#sblur)"/>

  <!-- Bidirectional studio glass conduits -->
  <g fill="none">
    <line x1="306" y1="262" x2="494" y2="262" stroke="{t['border']}" stroke-width="4" stroke-linecap="round"/>
    <line x1="306" y1="262" x2="494" y2="262" stroke="{t['accent']}" stroke-width="1.6" class="conduit"/>
    <line x1="306" y1="278" x2="494" y2="278" stroke="{t['border']}" stroke-width="1.4" class="conduit-r"/>

    <line x1="706" y1="262" x2="894" y2="262" stroke="{t['border']}" stroke-width="4" stroke-linecap="round"/>
    <line x1="706" y1="262" x2="894" y2="262" stroke="{t['accent']}" stroke-width="1.6" class="conduit"/>
    <line x1="706" y1="278" x2="894" y2="278" stroke="{t['border']}" stroke-width="1.4" class="conduit-r"/>
  </g>
  <g class="pkt1"><polygon points="306,256 318,262 306,268 294,262" fill="{t['accent']}"/></g>
  <g class="pkt2"><polygon points="706,256 718,262 706,268 694,262" fill="{t['accent']}"/></g>
  <g class="pkt3"><polygon points="306,274 314,278 306,282 298,278" fill="{t['brass']}"/></g>
  <g class="pkt4"><polygon points="706,274 714,278 706,282 698,278" fill="{t['brass']}"/></g>

  <g>{s1_base}<g class="f-a">{s1_mid}</g><g class="f-b">{s1_top}</g></g>
  <g>
    {s2_plinth}
    <ellipse cx="600" cy="260" rx="88" ry="34" fill="none" stroke="{t['brass']}" stroke-width="1.6" stroke-dasharray="10 6" class="ring"/>
    <g class="f-a">{s2_core}</g>
    <g class="f-b2">{s2_cap}</g>
  </g>
  <g>{s3_p1}<g class="f-c">{s3_p2}</g><g class="f-c2">{s3_p3}</g></g>

  <g text-anchor="middle" font-family="{SANS}">
    <text x="210" y="362" font-size="19.5" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">Data &amp; Domain</text>
    <text x="210" y="388" font-size="14.5" fill="{t['text_secondary']}">MySQL · Supabase · Schema Design</text>

    <text x="600" y="362" font-size="19.5" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">API &amp; Automation</text>
    <text x="600" y="388" font-size="14.5" fill="{t['text_secondary']}">Laravel · PHP · REST API · Workflows</text>

    <text x="990" y="362" font-size="19.5" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">Product Interface</text>
    <text x="990" y="388" font-size="14.5" fill="{t['text_secondary']}">TypeScript · Next.js · Tailwind CSS</text>
  </g>
</svg>
"""


def build_flagship_maus_svg(t: dict) -> str:
    """Machined Double-Bezel Flagship Showcase for verified LIVE Mau's Kitchen (1200x284)."""
    w, h = 1200, 284
    plane_catalog = studio_prism(836, 176, 56, 25, 14, "slate", t)
    plane_queue = studio_prism(962, 156, 60, 27, 16, "accent", t)
    plane_dispatch = studio_prism(1084, 188, 56, 25, 14, "brass", t)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Flagship live product: Mau's Kitchen. Menu discovery, ordering, and daily operations for an active kitchen at maukitchen.my.id.">
  <style>
    @keyframes liftA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes liftB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes orderFlow1 {{
      0% {{ transform: translate(0px, 0px); opacity: 0; }}
      15% {{ opacity: 1; }}
      85% {{ opacity: 1; }}
      100% {{ transform: translate(126px, -20px); opacity: 0; }}
    }}
    @keyframes orderFlow2 {{
      0% {{ transform: translate(0px, 0px); opacity: 0; }}
      15% {{ opacity: 1; }}
      85% {{ opacity: 1; }}
      100% {{ transform: translate(122px, 32px); opacity: 0; }}
    }}
    @keyframes railDash {{ from {{ stroke-dashoffset: 36; }} to {{ stroke-dashoffset: 0; }} }}
    .la {{ animation: liftA 4.8s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .lb {{ animation: liftB 4.8s cubic-bezier(0.32, 0.72, 0, 1) 0.55s infinite; }}
    .lc {{ animation: liftA 4.8s cubic-bezier(0.32, 0.72, 0, 1) 1.1s infinite; }}
    .of1 {{ animation: orderFlow1 3.0s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .of2 {{ animation: orderFlow2 3.0s cubic-bezier(0.32, 0.72, 0, 1) 1.5s infinite; }}
    .rail {{ stroke-dasharray: 5 7; animation: railDash 2.2s linear infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .la, .lb, .lc, .of1, .of2, .rail {{ animation: none !important; }}
    }}
  </style>
{shared_3d_defs(t)}
  {double_bezel_frame(w, h, t, surface=t['surface_warm'], spot='spot-warm', grain=True)}

  <!-- Single functional live status marker (verified HTTP 200) -->
  <rect x="46" y="38" width="144" height="26" rx="6" fill="{t['live_bg']}" stroke="{t['live']}" stroke-width="1"/>
  <text x="118" y="55" text-anchor="middle" font-family="{MONO}" font-size="11.5" font-weight="700" fill="{t['live']}">LIVE PRODUCTION</text>
  <text x="206" y="55" font-family="{MONO}" font-size="13" fill="{t['text_muted']}">maukitchen.my.id</text>

  <text x="46" y="110" font-family="{SANS}" font-size="38" font-weight="700" letter-spacing="-0.8" fill="{t['text_primary']}">Mau's Kitchen</text>
  <rect x="46" y="126" width="46" height="3" fill="{t['accent']}"/>

  <text x="46" y="162" font-family="{SANS}" font-size="16.5" fill="{t['text_secondary']}">Customer menu discovery, structured ordering, and daily kitchen</text>
  <text x="46" y="186" font-family="{SANS}" font-size="16.5" fill="{t['text_secondary']}">admin operations running in production for an active food business.</text>

  <g font-family="{MONO}" font-size="12.5" fill="{t['text_primary']}">
    <rect x="46" y="214" width="102" height="28" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="97" y="233" text-anchor="middle">TypeScript</text>
    <rect x="158" y="214" width="132" height="28" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="224" y="233" text-anchor="middle">Operations UI</text>
    <rect x="300" y="214" width="116" height="28" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="358" y="233" text-anchor="middle">Order Flow</text>
  </g>

  <line x1="712" y1="36" x2="712" y2="{h-36}" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 5"/>

  <ellipse cx="836" cy="204" rx="60" ry="17" fill="{t['shadow']}" opacity="0.56" filter="url(#sblur)"/>
  <ellipse cx="962" cy="192" rx="66" ry="19" fill="{t['shadow']}" opacity="0.60" filter="url(#sblur)"/>
  <ellipse cx="1084" cy="216" rx="60" ry="17" fill="{t['shadow']}" opacity="0.56" filter="url(#sblur)"/>

  <line x1="836" y1="164" x2="962" y2="144" stroke="{t['accent']}" stroke-width="1.8" class="rail"/>
  <line x1="962" y1="144" x2="1084" y2="176" stroke="{t['brass']}" stroke-width="1.8" class="rail"/>

  <g class="la">{plane_catalog}</g>
  <g class="lb">{plane_queue}</g>
  <g class="lc">{plane_dispatch}</g>

  <g class="of1">{studio_prism(836, 146, 14, 6.5, 11, "brass", t)}</g>
  <g class="of2">{studio_prism(962, 126, 14, 6.5, 11, "accent", t)}</g>

  <g text-anchor="middle" font-family="{MONO}" font-size="12.5" font-weight="600" fill="{t['text_secondary']}">
    <text x="836" y="246">MENU</text>
    <text x="962" y="246">QUEUE</text>
    <text x="1084" y="246">SERVED</text>
  </g>
</svg>
"""


def build_skill_path_svg(t: dict) -> str:
    """Asymmetric Wide Featured Card (684x296 -> 57% track, matches 498x296 at 41.5% to the sub-pixel)."""
    w, h = 684, 296
    steps = [
        (466, 232, 24, "slate"),
        (500, 220, 46, "slate"),
        (534, 208, 70, "brass"),
        (568, 196, 94, "slate"),
        (602, 184, 120, "accent"),
    ]
    prisms = [studio_prism(cx, by, 23, 11, ht, tone, t) for cx, by, ht, tone in steps]
    beacon = studio_prism(466, 200, 13, 6.2, 13, "accent", t)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Skill Path AI: highest-starred repository (3 stars), turning an existing profile into a practical skill roadmap and career direction.">
  <style>
    @keyframes climb {{
      0%, 10% {{ transform: translate(0px, 0px); }}
      26%, 32% {{ transform: translate(34px, -34px); }}
      48%, 54% {{ transform: translate(68px, -70px); }}
      70%, 76% {{ transform: translate(102px, -106px); }}
      90%, 100% {{ transform: translate(136px, -144px); }}
    }}
    @keyframes towerFloat {{
      0%, 100% {{ transform: translateY(0px); }}
      50% {{ transform: translateY(-4px); }}
    }}
    .beacon {{ animation: climb 5.4s cubic-bezier(0.32, 0.72, 0, 1) infinite alternate; }}
    .tfloat {{ animation: towerFloat 6s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .beacon {{ animation: none !important; transform: translate(136px, -144px); }}
      .tfloat {{ animation: none !important; }}
    }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t, surface=t['surface'], spot='spot-brass')}

  <text x="36" y="72" font-family="{SANS}" font-size="32" font-weight="700" letter-spacing="-0.7" fill="{t['text_primary']}">Skill Path AI</text>
  <text x="36" y="100" font-family="{MONO}" font-size="12.5" fill="{t['accent']}">3 stars on GitHub · TypeScript</text>

  <text x="36" y="142" font-family="{SANS}" font-size="16" fill="{t['text_secondary']}">Turns an existing developer profile into</text>
  <text x="36" y="166" font-family="{SANS}" font-size="16" fill="{t['text_secondary']}">a structured skill roadmap, portfolio guide,</text>
  <text x="36" y="190" font-family="{SANS}" font-size="16" fill="{t['text_secondary']}">and clear career direction.</text>

  <g font-family="{MONO}" font-size="12" fill="{t['text_primary']}">
    <rect x="36" y="216" width="102" height="26" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="87" y="233" text-anchor="middle">TypeScript</text>
    <rect x="148" y="216" width="112" height="26" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="204" y="233" text-anchor="middle">Career Engine</text>
  </g>
  <text x="36" y="268" font-family="{SANS}" font-size="13.5" font-weight="700" fill="{t['accent']}">Inspect repository</text>

  <ellipse cx="536" cy="242" rx="108" ry="24" fill="{t['shadow']}" opacity="0.58" filter="url(#sblur)"/>
  <g class="tfloat">{''.join(prisms)}</g>
  <g class="beacon">{beacon}</g>
</svg>
"""


def build_solar_ar_svg(t: dict) -> str:
    """Asymmetric Sculptural Companion Card (498x296 -> 41.5% track, exact height lock with Skill Path AI)."""
    w, h = 498, 296
    cx, cy = 376, 150
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Solar System AR: interactive WebAR learning experience combining product UI and 3D augmented reality with A-Frame and AR.js.">
  <style>
    @keyframes spinA {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes spinB {{ from {{ transform: rotate(360deg); }} to {{ transform: rotate(0deg); }} }}
    @keyframes sunPulse {{ 0%, 100% {{ opacity: 0.20; }} 50% {{ opacity: 0.42; }} }}
    .orb1 {{ animation: spinA 6.4s linear infinite; }}
    .orb2 {{ animation: spinA 11s linear infinite; }}
    .orb3 {{ animation: spinB 16s linear infinite; }}
    .halo {{ animation: sunPulse 4.8s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .orb1, .orb2, .orb3, .halo {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  <defs>
    <radialGradient id="sunGrad" cx="35%" cy="32%" r="65%">
      <stop offset="0%" stop-color="{t['brass_hi']}"/>
      <stop offset="55%" stop-color="{t['accent']}"/>
      <stop offset="100%" stop-color="{t['accent_lo']}"/>
    </radialGradient>
  </defs>
  {quiet_panel_frame(w, h, t, surface=t['surface_deep'], spot='spot-warm')}

  <text x="32" y="72" font-family="{SANS}" font-size="30" font-weight="700" letter-spacing="-0.6" fill="{t['text_primary']}">Solar System AR</text>
  <text x="32" y="100" font-family="{MONO}" font-size="12.5" fill="{t['brass']}">WebAR · A-Frame · AR.js</text>

  <text x="32" y="142" font-family="{SANS}" font-size="15.5" fill="{t['text_secondary']}">Browser learning tool</text>
  <text x="32" y="166" font-family="{SANS}" font-size="15.5" fill="{t['text_secondary']}">uniting product UI with</text>
  <text x="32" y="190" font-family="{SANS}" font-size="15.5" fill="{t['text_secondary']}">3D augmented reality.</text>

  <g font-family="{MONO}" font-size="12" fill="{t['text_primary']}">
    <rect x="32" y="216" width="102" height="26" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="83" y="233" text-anchor="middle">TypeScript</text>
  </g>
  <text x="32" y="268" font-family="{SANS}" font-size="13.5" font-weight="700" fill="{t['accent']}">Inspect repository</text>

  <ellipse cx="{cx}" cy="238" rx="76" ry="17" fill="{t['shadow']}" opacity="0.52" filter="url(#sblur)"/>

  <g transform="translate({cx},{cy}) rotate(-18) scale(1, 0.44)">
    <circle cx="0" cy="0" r="96" fill="none" stroke="{t['border_strong']}" stroke-width="1.5" stroke-dasharray="6 6"/>
    <g class="orb3">
      <circle cx="96" cy="0" r="9.5" fill="{t['brass']}"/>
      <circle cx="93" cy="-3" r="3" fill="{t['brass_hi']}"/>
    </g>
  </g>
  <g transform="translate({cx},{cy}) rotate(12) scale(1, 0.46)">
    <circle cx="0" cy="0" r="68" fill="none" stroke="{t['border_strong']}" stroke-width="1.4"/>
    <g class="orb2">
      <circle cx="-68" cy="0" r="10.5" fill="{t['accent']}"/>
      <circle cx="-71" cy="-3" r="3.5" fill="{t['accent_hi']}"/>
    </g>
  </g>

  <circle cx="{cx}" cy="{cy}" r="32" fill="{t['accent']}" class="halo" filter="url(#sblur)"/>
  <circle cx="{cx}" cy="{cy}" r="22" fill="url(#sunGrad)"/>

  <g transform="translate({cx},{cy}) rotate(-8) scale(1, 0.42)">
    <circle cx="0" cy="0" r="44" fill="none" stroke="{t['accent']}" stroke-width="1.4" opacity="0.85"/>
    <g class="orb1"><circle cx="44" cy="0" r="7.5" fill="{t['text_primary']}"/></g>
  </g>
</svg>
"""


def build_compact_press_svg(t: dict) -> str:
    w, h = 380, 232
    s1 = studio_prism(310, 108, 34, 15, 7, "slate", t)
    s2 = studio_prism(310, 88, 34, 15, 7, "brass", t)
    s3 = studio_prism(310, 68, 34, 15, 7, "accent", t)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Press Release Generator: TypeScript tool converting structured 5W+1H field notes into consistent press release drafts.">
  <style>
    @keyframes sheetA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-7px); }} }}
    @keyframes sheetB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-12px); }} }}
    .sa {{ animation: sheetA 4.6s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .sb {{ animation: sheetB 4.6s cubic-bezier(0.32, 0.72, 0, 1) 0.35s infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .sa, .sb {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t)}
  <text x="26" y="54" font-family="{SANS}" font-size="22" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">Press Release</text>
  <text x="26" y="80" font-family="{SANS}" font-size="22" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">Generator</text>
  <text x="26" y="118" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Turns structured 5W+1H field notes</text>
  <text x="26" y="140" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">into consistent press release drafts.</text>
  <rect x="26" y="164" width="96" height="24" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
  <text x="74" y="180" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="{t['text_primary']}">TypeScript</text>
  <text x="26" y="210" font-family="{SANS}" font-size="13" font-weight="700" fill="{t['accent']}">Inspect repository</text>

  <ellipse cx="310" cy="122" rx="38" ry="11" fill="{t['shadow']}" opacity="0.52" filter="url(#sblur)"/>
  {s1}<g class="sa">{s2}</g><g class="sb">{s3}</g>
</svg>
"""


def build_compact_fish_svg(t: dict) -> str:
    w, h = 380, 232
    crate = studio_prism(310, 108, 30, 14, 30, "slate", t)
    lid = studio_prism(310, 74, 32, 15, 9, "accent", t)
    tag_cube = studio_prism(310, 56, 13, 6, 10, "brass", t)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Fresh Fish E-Commerce: PHP, Laravel, Blade, and MySQL storefront and order transaction workflow.">
  <style>
    @keyframes lidLift {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes tokenRise {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-12px); }} }}
    .ll {{ animation: lidLift 4.8s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .tr {{ animation: tokenRise 4.8s cubic-bezier(0.32, 0.72, 0, 1) 0.3s infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .ll, .tr {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t)}
  <text x="26" y="54" font-family="{SANS}" font-size="22" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">Fresh Fish</text>
  <text x="26" y="80" font-family="{SANS}" font-size="22" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">E-Commerce</text>
  <text x="26" y="118" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Online storefront and order workflow</text>
  <text x="26" y="140" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">built with Laravel, Blade, and MySQL.</text>
  <g font-family="{MONO}" font-size="11.5" fill="{t['text_primary']}">
    <rect x="26" y="164" width="76" height="24" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="64" y="180" text-anchor="middle">Laravel</text>
    <rect x="110" y="164" width="66" height="24" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="143" y="180" text-anchor="middle">MySQL</text>
    <rect x="184" y="164" width="64" height="24" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="216" y="180" text-anchor="middle">Blade</text>
  </g>
  <text x="26" y="210" font-family="{SANS}" font-size="13" font-weight="700" fill="{t['accent']}">Inspect repository</text>

  <ellipse cx="310" cy="122" rx="38" ry="11" fill="{t['shadow']}" opacity="0.52" filter="url(#sblur)"/>
  {crate}<g class="ll">{lid}</g><g class="tr">{tag_cube}</g>
</svg>
"""


def build_compact_hmti_svg(t: dict) -> str:
    w, h = 380, 232
    hub = studio_prism(310, 92, 22, 10, 26, "accent", t)
    n1 = studio_prism(270, 108, 14, 6.5, 14, "slate", t)
    n2 = studio_prism(348, 108, 14, 6.5, 14, "brass", t)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="HMTI Margonda: TypeScript public organization website for the Informatics Student Association at UBSI Margonda.">
  <style>
    @keyframes hubFloat {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-7px); }} }}
    @keyframes linkPulse {{ from {{ stroke-dashoffset: 24; }} to {{ stroke-dashoffset: 0; }} }}
    .hf {{ animation: hubFloat 4.6s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .lp {{ stroke-dasharray: 4 5; animation: linkPulse 2s linear infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .hf, .lp {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t)}
  <text x="26" y="54" font-family="{SANS}" font-size="22" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">HMTI</text>
  <text x="26" y="80" font-family="{SANS}" font-size="22" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">Margonda</text>
  <text x="26" y="118" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Public website for the Informatics</text>
  <text x="26" y="140" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Student Association, UBSI Margonda.</text>
  <rect x="26" y="164" width="96" height="24" rx="6" fill="{t['raised']}" stroke="{t['border']}"/>
  <text x="74" y="180" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="{t['text_primary']}">TypeScript</text>
  <text x="26" y="210" font-family="{SANS}" font-size="13" font-weight="700" fill="{t['accent']}">Inspect repository</text>

  <ellipse cx="310" cy="122" rx="50" ry="12" fill="{t['shadow']}" opacity="0.48" filter="url(#sblur)"/>
  <line x1="270" y1="102" x2="310" y2="86" stroke="{t['accent']}" stroke-width="1.6" class="lp"/>
  <line x1="348" y1="102" x2="310" y2="86" stroke="{t['brass']}" stroke-width="1.6" class="lp"/>
  {n1}{n2}<g class="hf">{hub}</g>
</svg>
"""


def build_stack_monument_svg(t: dict) -> str:
    w, h = 1200, 356
    max_val = max(c for _, _, c, _ in ORIGINAL_LANG_COUNTS)
    bar_elems: list[str] = []

    start_x = 96
    step_x = 76
    base_y = 258

    for idx, (short, full, count, tone) in enumerate(ORIGINAL_LANG_COUNTS):
        cx = start_x + idx * step_x
        ht = max(24.0, (count / max_val) * 144.0)
        delay = f"{idx * 0.24:.2f}s"
        prism_svg = studio_prism(cx, base_y, 22, 10, ht, tone, t)
        bar_elems.append(
            f'<g class="bar-col" style="animation-delay:{delay}">'
            f'<ellipse cx="{cx}" cy="{base_y + 18}" rx="26" ry="8" fill="{t["shadow"]}" opacity="0.52" filter="url(#sblur)"/>'
            f"{prism_svg}"
            f'<text x="{cx}" y="{base_y - ht - 18:.1f}" text-anchor="middle" font-family="{MONO}" font-size="13.5" font-weight="700" fill="{t["text_primary"]}">{count}</text>'
            f'<text x="{cx}" y="{base_y + 40}" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t["text_secondary"]}">{short}</text>'
            f"</g>"
        )

    stack_rows = [
        ("Backend systems", "Laravel · PHP · REST API · MySQL · API testing"),
        ("Product interface", "TypeScript · JavaScript · Next.js · Tailwind CSS"),
        ("Workflow & ops", "Git · GitHub Actions · Postman · Figma · Deployment"),
        ("Extending next", "Supabase · Realtime data · Automated testing · System design"),
    ]
    rows_svg: list[str] = []
    for idx, (label, tools) in enumerate(stack_rows):
        y = 104 + idx * 58
        delay = f"{idx * 0.7:.1f}s"
        line_svg = (
            f'<line x1="680" y1="{y + 32}" x2="1152" y2="{y + 32}" stroke="{t["border"]}" stroke-width="1"/>'
            f'<rect x="680" y="{y + 31}" width="54" height="2" fill="{t["accent"]}" class="row-scan" style="animation-delay:{delay}"/>'
            if idx < len(stack_rows) - 1
            else ""
        )
        rows_svg.append(
            f'<text x="680" y="{y}" font-family="{SANS}" font-size="17" font-weight="700" letter-spacing="-0.2" fill="{t["text_primary"]}">{html.escape(label)}</text>'
            f'<text x="680" y="{y + 22}" font-family="{SANS}" font-size="14.5" fill="{t["text_secondary"]}">{html.escape(tools)}</text>'
            f"{line_svg}"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Repository language distribution and working stack: 20 original public repositories (22 total). TypeScript 9, JavaScript 4, Python 2, CSS 2, PHP 1, Blade 1, HTML 1.">
  <style>
    @keyframes barBreath {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes datumSweep {{
      0% {{ transform: translateX(0px); opacity: 0.25; }}
      50% {{ transform: translateX(460px); opacity: 0.95; }}
      100% {{ transform: translateX(0px); opacity: 0.25; }}
    }}
    @keyframes rowGlide {{
      0% {{ transform: translateX(0px); opacity: 0.2; }}
      50% {{ transform: translateX(418px); opacity: 0.9; }}
      100% {{ transform: translateX(0px); opacity: 0.2; }}
    }}
    .bar-col {{ animation: barBreath 5.0s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .datum {{ animation: datumSweep 7.6s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .row-scan {{ animation: rowGlide 7.0s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .bar-col, .datum, .row-scan {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t, surface=t['surface_deep'])}

  <text x="48" y="46" font-family="{SANS}" font-size="16" font-weight="700" fill="{t['text_primary']}">Language distribution</text>
  <text x="614" y="46" text-anchor="end" font-family="{MONO}" font-size="11.5" fill="{t['text_muted']}">20 original repos (22 public)</text>
  <line x1="48" y1="60" x2="614" y2="60" stroke="{t['border']}" stroke-width="1"/>

  <line x1="58" y1="268" x2="594" y2="268" stroke="{t['border']}" stroke-width="1.2" stroke-dasharray="3 4"/>
  <rect x="58" y="267" width="76" height="2.4" fill="{t['accent']}" class="datum"/>
  {''.join(bar_elems)}

  <text x="48" y="330" font-family="{MONO}" font-size="11.5" fill="{t['text_muted']}">Source: github.com/Sutannn13 original public repositories · Nov 2026</text>

  <line x1="646" y1="30" x2="646" y2="{h-30}" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 5"/>

  <text x="680" y="46" font-family="{SANS}" font-size="16" font-weight="700" fill="{t['text_primary']}">Working stack</text>
  <text x="1152" y="46" text-anchor="end" font-family="{MONO}" font-size="11.5" fill="{t['accent']}">Daily tools</text>
  <line x1="680" y1="60" x2="1152" y2="60" stroke="{t['border']}" stroke-width="1"/>

  {''.join(rows_svg)}
</svg>
"""


def build_track_record_svg(t: dict) -> str:
    """Clean editorial 2x2 credential ledger with studio-lit 3D isometric emblems (zero noisy eyebrows)."""
    w, h = 1200, 304

    e1 = (
        studio_prism(72, 110, 15, 7, 16, "slate", t)
        + studio_prism(96, 104, 15, 7, 30, "accent", t)
        + studio_prism(120, 114, 15, 7, 12, "brass", t)
    )
    e2 = (
        studio_prism(684, 112, 26, 12, 10, "slate", t)
        + f'<g class="em-float2">{studio_prism(684, 92, 17, 8, 16, "brass", t)}</g>'
    )
    e3 = (
        studio_prism(96, 254, 28, 12, 7, "slate", t)
        + f'<g class="em-float1">{studio_prism(96, 238, 28, 12, 7, "slate", t)}</g>'
        + f'<g class="em-float2">{studio_prism(96, 222, 28, 12, 7, "accent", t)}</g>'
    )
    e4 = (
        f'<line x1="664" y1="244" x2="704" y2="226" stroke="{t["accent"]}" stroke-width="1.6" class="net-dash"/>'
        f'<line x1="684" y1="256" x2="704" y2="226" stroke="{t["brass"]}" stroke-width="1.6" class="net-dash"/>'
        + studio_prism(664, 250, 13, 6, 12, "slate", t)
        + studio_prism(684, 262, 13, 6, 12, "brass", t)
        + f'<g class="em-float1">{studio_prism(704, 234, 14, 6.5, 16, "accent", t)}</g>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Track record: 2nd Place UBSI West Java IT Bootcamp (Trash Point), Registered HKI Copyright Inventor, SINTA 2 Research Contributor in JITK (SALI App), MikroTik MTCNA and Cisco Networking.">
  <style>
    @keyframes emA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-5px); }} }}
    @keyframes emB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-9px); }} }}
    @keyframes netFlow {{ from {{ stroke-dashoffset: 24; }} to {{ stroke-dashoffset: 0; }} }}
    .em-float1 {{ animation: emA 4.8s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .em-float2 {{ animation: emB 5.2s cubic-bezier(0.32, 0.72, 0, 1) 0.4s infinite; }}
    .net-dash {{ stroke-dasharray: 4 5; animation: netFlow 2.2s linear infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .em-float1, .em-float2, .net-dash {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  {quiet_panel_frame(w, h, t)}

  <line x1="600" y1="28" x2="600" y2="{h-28}" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 5"/>
  <line x1="36" y1="152" x2="{w-36}" y2="152" stroke="{t['border']}" stroke-width="1"/>

  <g class="em-float1">{e1}</g>
  <text x="158" y="70" font-family="{SANS}" font-size="20" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">2nd Place, UBSI West Java IT Bootcamp</text>
  <text x="158" y="98" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Built the Trash Point web application from data model</text>
  <text x="158" y="120" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">to deployed competition demo.</text>

  {e2}
  <text x="742" y="70" font-family="{SANS}" font-size="20" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">Registered HKI Copyright Inventor</text>
  <text x="742" y="98" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Officially recorded intellectual property registration</text>
  <text x="742" y="120" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">for the Trash Point software application.</text>

  {e3}
  <text x="158" y="212" font-family="{SANS}" font-size="20" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">SINTA 2 Research Contributor</text>
  <text x="158" y="240" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Co-authored the SALI App research publication in the</text>
  <text x="158" y="262" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">nationally accredited JITK journal.</text>

  {e4}
  <text x="742" y="212" font-family="{SANS}" font-size="20" font-weight="700" letter-spacing="-0.3" fill="{t['text_primary']}">MikroTik MTCNA &amp; Cisco Networking</text>
  <text x="742" y="240" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Certified in MikroTik network administration and</text>
  <text x="742" y="262" font-family="{SANS}" font-size="14.5" fill="{t['text_secondary']}">Cisco Networking fundamentals.</text>
</svg>
"""


def build_footer_svg(t: dict) -> str:
    """Machined Double-Bezel Atmospheric Closing Horizon Banner (1200x220)."""
    w, h = 1200, 220
    waves = []
    for i in range(6):
        y = 142 + i * 13
        amp = 6 + i * 2.2
        op = 0.24 + i * 0.13
        stroke_c = t["accent"] if i == 2 else (t["brass"] if i == 4 else t["border_strong"])
        sw = 1.9 if i == 2 else 1.1
        pts = []
        for step in range(0, 14):
            x = -40 + step * 100
            dy = math.sin((step + i * 0.85) * 0.72) * amp
            pts.append((x, y + dy))
        d = f"M{pts[0][0]},{pts[0][1]:.1f}"
        for j in range(1, len(pts)):
            mx = (pts[j - 1][0] + pts[j][0]) / 2
            my = (pts[j - 1][1] + pts[j][1]) / 2
            d += f" Q{pts[j - 1][0]},{pts[j - 1][1]:.1f} {mx:.1f},{my:.1f}"
        d += f" T{pts[-1][0]},{pts[-1][1]:.1f}"
        cls = "wave-a" if i % 2 == 0 else "wave-b"
        waves.append(f'<path d="{d}" fill="none" stroke="{stroke_c}" stroke-width="{sw}" opacity="{op:.2f}" class="{cls}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Closing invitation: Observe the problem, Design the flow, Ship the system. Open for junior roles, internships, and product collaborations.">
  <style>
    @keyframes driftA {{ 0%, 100% {{ transform: translateX(0px); }} 50% {{ transform: translateX(-34px); }} }}
    @keyframes driftB {{ 0%, 100% {{ transform: translateX(0px); }} 50% {{ transform: translateX(34px); }} }}
    .wave-a {{ animation: driftA 8.5s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    .wave-b {{ animation: driftB 10.5s cubic-bezier(0.32, 0.72, 0, 1) infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .wave-a, .wave-b {{ animation: none !important; }} }}
  </style>
{shared_3d_defs(t)}
  <defs>
    <clipPath id="fc"><rect x="6" y="6" width="{w-12}" height="{h-12}" rx="10"/></clipPath>
    <radialGradient id="h-glow" cx="50%" cy="100%" r="55%">
      <stop offset="0%" stop-color="{t['accent']}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{t['accent']}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  {double_bezel_frame(w, h, t, surface=t['surface_warm'], grain=True)}
  <g clip-path="url(#fc)">
    <rect x="6" y="6" width="{w-12}" height="{h-12}" fill="url(#h-glow)"/>
    {''.join(waves)}
  </g>
  <text x="600" y="64" text-anchor="middle" font-family="{SERIF}" font-size="30" font-weight="700" letter-spacing="-0.4" fill="{t['text_primary']}">Observe the problem · Design the flow · Ship the system</text>
  <text x="600" y="98" text-anchor="middle" font-family="{SANS}" font-size="16" fill="{t['text_secondary']}">Open to junior backend or full-stack roles, internships, and focused product builds.</text>
  <text x="600" y="126" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t['text_muted']}">Sutan Arlie Johan · Depok, Indonesia · sutanarliejohan@gmail.com</text>
</svg>
"""


def build_all() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for mode, theme in THEMES.items():
        outputs: dict[str, str] = {
            **build_action_tiles(theme),
            "btn-maus-live": build_cta_bar(theme, "Open maukitchen.my.id", "LIVE SITE", primary=True),
            "btn-maus-source": build_cta_bar(theme, "Inspect Mau's Kitchen source", "GITHUB REPO", primary=False),
            "btn-contact-email": build_cta_bar(theme, "Start a conversation", "EMAIL DIRECT", primary=True),
            "btn-contact-linkedin": build_cta_bar(theme, "Connect on LinkedIn", "LINKEDIN", primary=False),
            "section-work": build_section_strip(theme, "02", "Selected work", "6 verified builds · 1 live production"),
            "section-activity": build_section_strip(theme, "03", "Activity & stack", "Daily graph · 20 original repos"),
            "section-record": build_section_strip(theme, "04", "Track record", "Bootcamp · HKI · SINTA 2 · Certs"),
            "architecture": build_architecture_svg(theme),
            "project-maus-kitchen": build_flagship_maus_svg(theme),
            "project-skill-path": build_skill_path_svg(theme),
            "project-solar-ar": build_solar_ar_svg(theme),
            "project-press-release": build_compact_press_svg(theme),
            "project-fresh-fish": build_compact_fish_svg(theme),
            "project-hmti": build_compact_hmti_svg(theme),
            "stack-monument": build_stack_monument_svg(theme),
            "track-record": build_track_record_svg(theme),
            "footer": build_footer_svg(theme),
        }
        for name, svg_str in outputs.items():
            out = ASSETS / f"{name}-{mode}.svg"
            out.write_text(svg_str, encoding="utf-8")
    print(f"Generated {len(outputs) * 2} dual-theme studio-lit SVGs in {ASSETS}")


if __name__ == "__main__":
    build_all()
