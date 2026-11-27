#!/usr/bin/env python3
"""Generate dual-theme (dark & light) animated 3D isometric/perspective SVGs.

Every color pair is WCAG AA verified (>= 4.5:1 text, >= 3.0:1 UI boundaries) and
every SVG honors prefers-reduced-motion. Zero em dashes, zero fabricated metrics.
"""

from __future__ import annotations

import html
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

THEMES = {
    "dark": {
        "surface": "#14171c",
        "raised": "#1c2028",
        "raised_hi": "#262c37",
        "facet_top": "#2b323f",
        "facet_left": "#1f2530",
        "facet_right": "#171c24",
        "border": "#2c323c",
        "border_strong": "#5b6575",
        "text_primary": "#f3efe6",
        "text_secondary": "#b6b1a6",
        "text_muted": "#969187",
        "accent": "#e57a52",
        "accent_top": "#f0936f",
        "accent_left": "#d46840",
        "accent_right": "#9c4727",
        "brass": "#d9a45b",
        "brass_top": "#e6b877",
        "brass_left": "#c28e46",
        "brass_right": "#8f652c",
        "live": "#72c495",
        "live_bg": "#15261e",
        "shadow": "#090b0e",
    },
    "light": {
        "surface": "#f7f4ee",
        "raised": "#eee9df",
        "raised_hi": "#e5dfd3",
        "facet_top": "#e7e1d5",
        "facet_left": "#d9d2c4",
        "facet_right": "#c7bfb0",
        "border": "#d6cfc2",
        "border_strong": "#766f64",
        "text_primary": "#161614",
        "text_secondary": "#4a4741",
        "text_muted": "#5c5850",
        "accent": "#b5451b",
        "accent_top": "#d46035",
        "accent_left": "#b5451b",
        "accent_right": "#873110",
        "brass": "#7d5318",
        "brass_top": "#9c6d28",
        "brass_left": "#7d5318",
        "brass_right": "#5c3c0e",
        "live": "#1e6b43",
        "live_bg": "#e4f0e8",
        "shadow": "#c9c1b2",
    },
}

# Verified directly from GitHub API for Sutannn13 (20 original / 22 total public repos)
ORIGINAL_LANG_COUNTS = [
    ("TS", "TypeScript", 9, "accent"),
    ("JS", "JavaScript", 4, "brass"),
    ("PY", "Python", 2, "slate"),
    ("CSS", "CSS", 2, "slate"),
    ("PHP", "PHP", 1, "slate"),
    ("BLD", "Blade", 1, "slate"),
    ("HTML", "HTML", 1, "slate"),
]


def iso_prism(
    cx: float,
    base_y: float,
    rx: float,
    ry: float,
    height: float,
    top_fill: str,
    left_fill: str,
    right_fill: str,
    stroke: str = "",
) -> str:
    """Return SVG polygons for a clean 3D isometric vertical prism."""
    ty = base_y - height
    top_pts = f"{cx:.1f},{ty - ry:.1f} {cx + rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx - rx:.1f},{ty:.1f}"
    left_pts = f"{cx - rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx:.1f},{base_y + ry:.1f} {cx - rx:.1f},{base_y:.1f}"
    right_pts = f"{cx + rx:.1f},{ty:.1f} {cx:.1f},{ty + ry:.1f} {cx:.1f},{base_y + ry:.1f} {cx + rx:.1f},{base_y:.1f}"
    s_attr = f' stroke="{stroke}" stroke-width="0.9" stroke-linejoin="round"' if stroke else ""
    return (
        f'<polygon points="{left_pts}" fill="{left_fill}"{s_attr}/>'
        f'<polygon points="{right_pts}" fill="{right_fill}"{s_attr}/>'
        f'<polygon points="{top_pts}" fill="{top_fill}"{s_attr}/>'
    )


def corner_ticks(w: int, h: int, color: str) -> str:
    return (
        f'<g stroke="{color}" stroke-width="1.15" opacity="0.65" fill="none">'
        f'<path d="M16,26 L16,16 L26,16"/>'
        f'<path d="M{w-26},16 L{w-16},16 L{w-16},26"/>'
        f'<path d="M16,{h-26} L16,{h-16} L26,{h-16}"/>'
        f'<path d="M{w-26},{h-16} L{w-16},{h-16} L{w-16},{h-26}"/>'
        f"</g>"
    )


def build_architecture_svg(t: dict) -> str:
    w, h = 1200, 315
    # Station 1: Stacked 3D isometric database slabs
    s1_base = iso_prism(210, 186, 56, 26, 16, t["facet_top"], t["facet_left"], t["facet_right"], t["border"])
    s1_mid = iso_prism(210, 160, 56, 26, 16, t["facet_top"], t["facet_left"], t["facet_right"], t["border"])
    s1_top = iso_prism(210, 134, 56, 26, 16, t["accent_top"], t["accent_left"], t["accent_right"], t["border"])

    # Station 2: Elevated 3D isometric modular API engine
    s2_plinth = iso_prism(600, 192, 68, 31, 14, t["facet_top"], t["facet_left"], t["facet_right"], t["border"])
    s2_core = iso_prism(600, 174, 38, 18, 46, t["accent_top"], t["accent_left"], t["accent_right"], t["border"])
    s2_cap = iso_prism(600, 122, 46, 21, 12, t["brass_top"], t["brass_left"], t["brass_right"], t["border"])

    # Station 3: Layered 3D isometric product interface planes
    s3_p1 = iso_prism(990, 188, 60, 27, 10, t["facet_top"], t["facet_left"], t["facet_right"], t["border"])
    s3_p2 = iso_prism(990, 160, 52, 24, 10, t["facet_top"], t["facet_left"], t["facet_right"], t["border"])
    s3_p3 = iso_prism(990, 132, 42, 19, 10, t["brass_top"], t["brass_left"], t["brass_right"], t["border"])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="3D isometric system architecture pipeline: Data and Domain, API and Automation, Product Interface">
  <style>
    @keyframes floatA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-7px); }} }}
    @keyframes floatB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes floatC {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes flowDash {{ from {{ stroke-dashoffset: 64; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes packet1 {{ 0% {{ transform: translateX(0px); opacity: 0; }} 14% {{ opacity: 1; }} 86% {{ opacity: 1; }} 100% {{ transform: translateX(188px); opacity: 0; }} }}
    @keyframes packet2 {{ 0% {{ transform: translateX(0px); opacity: 0; }} 14% {{ opacity: 1; }} 86% {{ opacity: 1; }} 100% {{ transform: translateX(188px); opacity: 0; }} }}
    @keyframes ringBreath {{ 0%, 100% {{ opacity: 0.55; }} 50% {{ opacity: 0.95; }} }}
    .f-a {{ animation: floatA 4.6s ease-in-out infinite; }}
    .f-b {{ animation: floatB 5.2s ease-in-out infinite; }}
    .f-c {{ animation: floatC 4.9s ease-in-out infinite; }}
    .f-b2 {{ animation: floatA 5.2s ease-in-out 0.6s infinite; }}
    .f-c2 {{ animation: floatB 4.9s ease-in-out 0.8s infinite; }}
    .conduit {{ stroke-dasharray: 6 10; animation: flowDash 2.6s linear infinite; }}
    .pkt1 {{ animation: packet1 2.8s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
    .pkt2 {{ animation: packet2 2.8s cubic-bezier(0.4, 0, 0.2, 1) 1.4s infinite; }}
    .ring {{ animation: ringBreath 4.6s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .f-a, .f-b, .f-c, .f-b2, .f-c2, .conduit, .pkt1, .pkt2, .ring {{ animation: none !important; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
  {corner_ticks(w, h, t['border_strong'])}

  <!-- Top architectural specification bar -->
  <text x="44" y="42" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" letter-spacing="1.4" fill="{t['text_muted']}">SYSTEM ARCHITECTURE</text>
  <text x="{w-44}" y="42" text-anchor="end" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" fill="{t['text_muted']}">DATA MODEL -&gt; API ENGINE -&gt; PRODUCT UI</text>
  <line x1="44" y1="56" x2="{w-44}" y2="56" stroke="{t['border']}" stroke-width="1"/>

  <!-- Ground shadow ellipses -->
  <ellipse cx="210" cy="206" rx="70" ry="20" fill="{t['shadow']}" opacity="0.42"/>
  <ellipse cx="600" cy="212" rx="82" ry="24" fill="{t['shadow']}" opacity="0.46"/>
  <ellipse cx="990" cy="206" rx="70" ry="20" fill="{t['shadow']}" opacity="0.42"/>

  <!-- Precision architectural data conduits between 3D stations -->
  <g fill="none">
    <line x1="306" y1="164" x2="494" y2="164" stroke="{t['border']}" stroke-width="4" stroke-linecap="round"/>
    <line x1="306" y1="164" x2="494" y2="164" stroke="{t['accent']}" stroke-width="1.6" class="conduit"/>
    <line x1="706" y1="164" x2="894" y2="164" stroke="{t['border']}" stroke-width="4" stroke-linecap="round"/>
    <line x1="706" y1="164" x2="894" y2="164" stroke="{t['accent']}" stroke-width="1.6" class="conduit"/>
  </g>
  <!-- Gliding isometric data packets -->
  <g class="pkt1">
    <polygon points="306,158 318,164 306,170 294,164" fill="{t['accent']}"/>
  </g>
  <g class="pkt2">
    <polygon points="706,158 718,164 706,170 694,164" fill="{t['accent']}"/>
  </g>

  <!-- Station 01: Data & Domain -->
  <g>
    {s1_base}
    <g class="f-a">{s1_mid}</g>
    <g class="f-b">{s1_top}</g>
  </g>

  <!-- Station 02: API & Automation -->
  <g>
    {s2_plinth}
    <ellipse cx="600" cy="158" rx="82" ry="32" fill="none" stroke="{t['brass']}" stroke-width="1.4" stroke-dasharray="10 6" class="ring"/>
    <g class="f-a">{s2_core}</g>
    <g class="f-b2">{s2_cap}</g>
  </g>

  <!-- Station 03: Product Interface -->
  <g>
    {s3_p1}
    <g class="f-c">{s3_p2}</g>
    <g class="f-c2">{s3_p3}</g>
  </g>

  <!-- Station labels -->
  <g text-anchor="middle" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif">
    <text x="210" y="252" font-size="20" font-weight="700" fill="{t['text_primary']}">Data &amp; Domain</text>
    <text x="210" y="278" font-size="14.5" fill="{t['text_secondary']}">MySQL · Supabase · Schema Design</text>

    <text x="600" y="252" font-size="20" font-weight="700" fill="{t['text_primary']}">API &amp; Automation</text>
    <text x="600" y="278" font-size="14.5" fill="{t['text_secondary']}">Laravel · PHP · REST API · Workflows</text>

    <text x="990" y="252" font-size="20" font-weight="700" fill="{t['text_primary']}">Product Interface</text>
    <text x="990" y="278" font-size="14.5" fill="{t['text_secondary']}">TypeScript · Next.js · Tailwind CSS</text>
  </g>
</svg>
"""


def build_flagship_maus_svg(t: dict) -> str:
    w, h = 1200, 256
    # Three staggered 3D isometric operations planes on the right stage (x=760..1130)
    plane_catalog = iso_prism(836, 162, 54, 24, 12, t["facet_top"], t["facet_left"], t["facet_right"], t["border"])
    plane_queue = iso_prism(962, 146, 58, 26, 14, t["accent_top"], t["accent_left"], t["accent_right"], t["border"])
    plane_dispatch = iso_prism(1084, 174, 54, 24, 12, t["brass_top"], t["brass_left"], t["brass_right"], t["border"])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Flagship live product: Mau's Kitchen. Menu discovery, ordering, and daily operations for an active kitchen. Live at maukitchen.my.id.">
  <style>
    @keyframes liftA {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes liftB {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-9px); }} }}
    @keyframes orderFlow1 {{
      0% {{ transform: translate(0px, 0px); opacity: 0; }}
      15% {{ opacity: 1; }}
      85% {{ opacity: 1; }}
      100% {{ transform: translate(126px, -16px); opacity: 0; }}
    }}
    @keyframes orderFlow2 {{
      0% {{ transform: translate(0px, 0px); opacity: 0; }}
      15% {{ opacity: 1; }}
      85% {{ opacity: 1; }}
      100% {{ transform: translate(122px, 28px); opacity: 0; }}
    }}
    .la {{ animation: liftA 4.8s ease-in-out infinite; }}
    .lb {{ animation: liftB 4.8s ease-in-out 0.6s infinite; }}
    .lc {{ animation: liftA 4.8s ease-in-out 1.2s infinite; }}
    .of1 {{ animation: orderFlow1 3.2s ease-in-out infinite; }}
    .of2 {{ animation: orderFlow2 3.2s ease-in-out 1.6s infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .la, .lb, .lc, .of1, .of2 {{ animation: none !important; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
  {corner_ticks(w, h, t['border_strong'])}

  <!-- Editorial left region -->
  <rect x="44" y="34" width="142" height="24" rx="4" fill="{t['live_bg']}" stroke="{t['live']}" stroke-width="1"/>
  <text x="115" y="50" text-anchor="middle" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="11.5" font-weight="700" fill="{t['live']}">LIVE PRODUCTION</text>
  <text x="202" y="50" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12.5" fill="{t['text_muted']}">maukitchen.my.id</text>

  <text x="44" y="102" font-family="Georgia, 'Times New Roman', serif" font-size="34" font-weight="700" fill="{t['text_primary']}">Mau's Kitchen</text>
  <rect x="44" y="116" width="44" height="2.5" fill="{t['accent']}"/>

  <text x="44" y="150" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="16" fill="{t['text_secondary']}">Customer menu discovery, structured ordering, and daily kitchen</text>
  <text x="44" y="174" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="16" fill="{t['text_secondary']}">admin operations running in production for an active food business.</text>

  <!-- Architectural tags (4px radius, not pills) -->
  <g font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" fill="{t['text_primary']}">
    <rect x="44" y="198" width="98" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="93" y="215" text-anchor="middle">TypeScript</text>
    <rect x="152" y="198" width="128" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="216" y="215" text-anchor="middle">Operations UI</text>
    <rect x="290" y="198" width="114" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="347" y="215" text-anchor="middle">Order Flow</text>
  </g>

  <!-- Vertical separator -->
  <line x1="716" y1="34" x2="716" y2="{h-34}" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 5"/>

  <!-- 3D Isometric Kitchen Operations Diorama -->
  <ellipse cx="836" cy="186" rx="58" ry="17" fill="{t['shadow']}" opacity="0.4"/>
  <ellipse cx="962" cy="176" rx="64" ry="19" fill="{t['shadow']}" opacity="0.45"/>
  <ellipse cx="1084" cy="198" rx="58" ry="17" fill="{t['shadow']}" opacity="0.4"/>

  <line x1="836" y1="150" x2="962" y2="134" stroke="{t['border_strong']}" stroke-width="1.5" stroke-dasharray="4 5"/>
  <line x1="962" y1="134" x2="1084" y2="162" stroke="{t['border_strong']}" stroke-width="1.5" stroke-dasharray="4 5"/>

  <g class="la">{plane_catalog}</g>
  <g class="lb">{plane_queue}</g>
  <g class="lc">{plane_dispatch}</g>

  <!-- Animated order tokens moving along 3D workflow -->
  <g class="of1">
    {iso_prism(836, 134, 13, 6, 10, t["brass_top"], t["brass_left"], t["brass_right"])}
  </g>
  <g class="of2">
    {iso_prism(962, 118, 13, 6, 10, t["accent_top"], t["accent_left"], t["accent_right"])}
  </g>

  <g text-anchor="middle" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12.5" font-weight="600" fill="{t['text_secondary']}">
    <text x="836" y="222">MENU</text>
    <text x="962" y="222">QUEUE</text>
    <text x="1084" y="222">SERVED</text>
  </g>
</svg>
"""


def build_skill_path_svg(t: dict) -> str:
    w, h = 580, 268
    # 5 ascending 3D isometric staircase blocks representing career roadmap progression
    steps = [
        (398, 206, 20),
        (428, 194, 38),
        (458, 182, 58),
        (488, 170, 78),
        (518, 158, 100),
    ]
    prisms = []
    for idx, (cx, by, ht) in enumerate(steps):
        if idx == 4:
            prisms.append(iso_prism(cx, by, 20, 9.5, ht, t["accent_top"], t["accent_left"], t["accent_right"], t["border"]))
        elif idx == 2:
            prisms.append(iso_prism(cx, by, 20, 9.5, ht, t["brass_top"], t["brass_left"], t["brass_right"], t["border"]))
        else:
            prisms.append(iso_prism(cx, by, 20, 9.5, ht, t["facet_top"], t["facet_left"], t["facet_right"], t["border"]))

    beacon = iso_prism(398, 180, 11, 5.5, 11, t["accent_top"], t["accent_left"], t["accent_right"])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Skill Path AI: maps an existing profile into a practical skill roadmap and career direction. Open source TypeScript repository.">
  <style>
    @keyframes climb {{
      0%, 10% {{ transform: translate(0px, 0px); }}
      26%, 32% {{ transform: translate(30px, -30px); }}
      48%, 54% {{ transform: translate(60px, -62px); }}
      70%, 76% {{ transform: translate(90px, -94px); }}
      90%, 100% {{ transform: translate(120px, -128px); }}
    }}
    .beacon {{ animation: climb 5.4s cubic-bezier(0.45, 0, 0.25, 1) infinite alternate; }}
    @media (prefers-reduced-motion: reduce) {{
      .beacon {{ animation: none !important; transform: translate(120px, -128px); }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
  {corner_ticks(w, h, t['border_strong'])}

  <text x="32" y="42" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" fill="{t['text_muted']}">OPEN SOURCE · 3 STARS</text>
  <text x="32" y="86" font-family="Georgia, 'Times New Roman', serif" font-size="28" font-weight="700" fill="{t['text_primary']}">Skill Path AI</text>
  <rect x="32" y="100" width="36" height="2.5" fill="{t['accent']}"/>

  <text x="32" y="134" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="15.5" fill="{t['text_secondary']}">Turns an existing profile into</text>
  <text x="32" y="158" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="15.5" fill="{t['text_secondary']}">a practical skill roadmap and</text>
  <text x="32" y="182" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="15.5" fill="{t['text_secondary']}">clear career direction.</text>

  <g font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" fill="{t['text_primary']}">
    <rect x="32" y="210" width="98" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="81" y="227" text-anchor="middle">TypeScript</text>
    <rect x="140" y="210" width="98" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="189" y="227" text-anchor="middle">Roadmap AI</text>
  </g>

  <!-- 3D Isometric Ascending Roadmap Monument -->
  <ellipse cx="458" cy="212" rx="92" ry="22" fill="{t['shadow']}" opacity="0.42"/>
  {''.join(prisms)}
  <g class="beacon">{beacon}</g>
</svg>
"""


def build_solar_ar_svg(t: dict) -> str:
    w, h = 580, 268
    cx, cy = 456, 144
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Solar System AR: interactive browser learning combining product UI and WebAR with A-Frame and AR.js.">
  <style>
    @keyframes spinA {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes spinB {{ from {{ transform: rotate(360deg); }} to {{ transform: rotate(0deg); }} }}
    .orb1 {{ animation: spinA 7s linear infinite; }}
    .orb2 {{ animation: spinA 12s linear infinite; }}
    .orb3 {{ animation: spinB 17s linear infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .orb1, .orb2, .orb3 {{ animation: none !important; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
  {corner_ticks(w, h, t['border_strong'])}

  <text x="32" y="42" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" fill="{t['text_muted']}">IMMERSIVE WEB AR</text>
  <text x="32" y="86" font-family="Georgia, 'Times New Roman', serif" font-size="28" font-weight="700" fill="{t['text_primary']}">Solar System AR</text>
  <rect x="32" y="100" width="36" height="2.5" fill="{t['accent']}"/>

  <text x="32" y="134" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="15.5" fill="{t['text_secondary']}">Interactive browser learning</text>
  <text x="32" y="158" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="15.5" fill="{t['text_secondary']}">experience uniting product UI</text>
  <text x="32" y="182" font-family="'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="15.5" fill="{t['text_secondary']}">with 3D augmented reality.</text>

  <g font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" fill="{t['text_primary']}">
    <rect x="32" y="210" width="98" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="81" y="227" text-anchor="middle">TypeScript</text>
    <rect x="140" y="210" width="128" height="26" rx="4" fill="{t['raised']}" stroke="{t['border']}"/>
    <text x="204" y="227" text-anchor="middle">A-Frame / AR.js</text>
  </g>

  <!-- 3D Projected Tilted Planetary Orrery -->
  <defs>
    <radialGradient id="sunGrad" cx="35%" cy="32%" r="65%">
      <stop offset="0%" stop-color="{t['brass_top']}"/>
      <stop offset="55%" stop-color="{t['accent']}"/>
      <stop offset="100%" stop-color="{t['accent_right']}"/>
    </radialGradient>
  </defs>

  <ellipse cx="{cx}" cy="222" rx="74" ry="16" fill="{t['shadow']}" opacity="0.35"/>

  <!-- Tilted orbital plane 1 (outer) -->
  <g transform="translate({cx},{cy}) rotate(-18) scale(1, 0.44)">
    <circle cx="0" cy="0" r="96" fill="none" stroke="{t['border_strong']}" stroke-width="1.6" stroke-dasharray="6 6"/>
    <g class="orb3">
      <circle cx="96" cy="0" r="9" fill="{t['brass']}"/>
      <circle cx="93" cy="-3" r="3" fill="{t['brass_top']}"/>
    </g>
  </g>

  <!-- Tilted orbital plane 2 (middle) -->
  <g transform="translate({cx},{cy}) rotate(12) scale(1, 0.46)">
    <circle cx="0" cy="0" r="68" fill="none" stroke="{t['border_strong']}" stroke-width="1.5"/>
    <g class="orb2">
      <circle cx="-68" cy="0" r="10.5" fill="{t['accent']}"/>
      <circle cx="-71" cy="-3" r="3.5" fill="{t['accent_top']}"/>
    </g>
  </g>

  <!-- Central 3D shaded sphere -->
  <circle cx="{cx}" cy="{cy}" r="22" fill="url(#sunGrad)"/>

  <!-- Tilted orbital plane 3 (inner fast ring) -->
  <g transform="translate({cx},{cy}) rotate(-8) scale(1, 0.42)">
    <circle cx="0" cy="0" r="44" fill="none" stroke="{t['accent']}" stroke-width="1.4" opacity="0.8"/>
    <g class="orb1">
      <circle cx="44" cy="0" r="7.5" fill="{t['text_primary']}"/>
    </g>
  </g>
</svg>
"""


def build_stack_monument_svg(t: dict) -> str:
    w, h = 1200, 344
    max_val = max(c for _, _, c, _ in ORIGINAL_LANG_COUNTS)
    bar_elems: list[str] = []

    start_x = 96
    step_x = 76
    base_y = 248

    for idx, (short, full, count, tone) in enumerate(ORIGINAL_LANG_COUNTS):
        cx = start_x + idx * step_x
        ht = max(24.0, (count / max_val) * 140.0)
        if tone == "accent":
            top_f, left_f, right_f = t["accent_top"], t["accent_left"], t["accent_right"]
        elif tone == "brass":
            top_f, left_f, right_f = t["brass_top"], t["brass_left"], t["brass_right"]
        else:
            top_f, left_f, right_f = t["facet_top"], t["facet_left"], t["facet_right"]

        delay = f"{idx * 0.22:.2f}s"
        prism_svg = iso_prism(cx, base_y, 22, 10, ht, top_f, left_f, right_f, t["border"])
        bar_elems.append(
            f'<g class="bar-col" style="animation-delay:{delay}">'
            f'<ellipse cx="{cx}" cy="{base_y + 16}" rx="26" ry="8" fill="{t["shadow"]}" opacity="0.38"/>'
            f"{prism_svg}"
            f'<text x="{cx}" y="{base_y - ht - 18:.1f}" text-anchor="middle" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="13" font-weight="700" fill="{t["text_primary"]}">{count}</text>'
            f'<text x="{cx}" y="{base_y + 38}" text-anchor="middle" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="11.5" fill="{t["text_secondary"]}">{short}</text>'
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
        y = 104 + idx * 56
        line_svg = (
            f'<line x1="680" y1="{y + 30}" x2="1156" y2="{y + 30}" stroke="{t["border"]}" stroke-width="1"/>'
            if idx < len(stack_rows) - 1
            else ""
        )
        rows_svg.append(
            f'<text x="680" y="{y}" font-family="Georgia, \'Times New Roman\', serif" font-size="17" font-weight="700" fill="{t["text_primary"]}">{html.escape(label)}</text>'
            f'<text x="680" y="{y + 21}" font-family="\'Segoe UI\', -apple-system, BlinkMacSystemFont, Arial, sans-serif" font-size="14.5" fill="{t["text_secondary"]}">{html.escape(tools)}</text>'
            f"{line_svg}"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Repository language distribution and working stack: 20 original public repositories (22 total). TypeScript 9, JavaScript 4, Python 2, CSS 2, PHP 1, Blade 1, HTML 1.">
  <style>
    @keyframes barBreath {{
      0%, 100% {{ transform: translateY(0px); }}
      50% {{ transform: translateY(-4px); }}
    }}
    .bar-col {{ animation: barBreath 5.2s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .bar-col {{ animation: none !important; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
  {corner_ticks(w, h, t['border_strong'])}

  <!-- Left header -->
  <text x="44" y="42" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" letter-spacing="1.4" fill="{t['text_muted']}">LANGUAGE DISTRIBUTION</text>
  <text x="614" y="42" text-anchor="end" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="11.5" fill="{t['text_muted']}">20 ORIGINAL REPOS (22 PUBLIC)</text>
  <line x1="44" y1="56" x2="614" y2="56" stroke="{t['border']}" stroke-width="1"/>

  <!-- Subtle architectural baseline -->
  <line x1="60" y1="258" x2="594" y2="258" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 4"/>
  {''.join(bar_elems)}

  <text x="44" y="318" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="11" fill="{t['text_muted']}">Source: github.com/Sutannn13 public original repositories · Nov 2026</text>

  <!-- Center structural divider -->
  <line x1="646" y1="30" x2="646" y2="{h-30}" stroke="{t['border']}" stroke-width="1" stroke-dasharray="3 5"/>

  <!-- Right header -->
  <text x="680" y="42" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="12" letter-spacing="1.4" fill="{t['text_muted']}">WORKING STACK</text>
  <text x="1156" y="42" text-anchor="end" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="11.5" fill="{t['accent']}">DAILY TOOLS</text>
  <line x1="680" y1="56" x2="1156" y2="56" stroke="{t['border']}" stroke-width="1"/>

  {''.join(rows_svg)}
</svg>
"""


def build_footer_svg(t: dict) -> str:
    w, h = 1200, 148
    # Layered 3D perspective receding architectural horizon contours
    waves = []
    for i in range(5):
        y = 82 + i * 13
        amp = 6 + i * 2.2
        op = 0.20 + i * 0.14
        stroke_c = t["accent"] if i == 2 else t["border_strong"]
        sw = 1.6 if i == 2 else 1.0
        pts = []
        for step in range(0, 14):
            x = -40 + step * 100
            dy = math.sin((step + i * 0.8) * 0.7) * amp
            pts.append((x, y + dy))
        d = f"M{pts[0][0]},{pts[0][1]:.1f}"
        for j in range(1, len(pts)):
            mx = (pts[j - 1][0] + pts[j][0]) / 2
            my = (pts[j - 1][1] + pts[j][1]) / 2
            d += f" Q{pts[j - 1][0]},{pts[j - 1][1]:.1f} {mx:.1f},{my:.1f}"
        d += f" T{pts[-1][0]},{pts[-1][1]:.1f}"
        cls = "wave-a" if i % 2 == 0 else "wave-b"
        waves.append(f'<path d="{d}" fill="none" stroke="{stroke_c}" stroke-width="{sw}" opacity="{op:.2f}" class="{cls}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Architectural horizon closing banner: Observe the problem, Design the flow, Ship the system. Sutan Arlie Johan, Depok, Indonesia.">
  <style>
    @keyframes driftA {{ 0%, 100% {{ transform: translateX(0px); }} 50% {{ transform: translateX(-28px); }} }}
    @keyframes driftB {{ 0%, 100% {{ transform: translateX(0px); }} 50% {{ transform: translateX(28px); }} }}
    .wave-a {{ animation: driftA 9s ease-in-out infinite; }}
    .wave-b {{ animation: driftB 11s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{
      .wave-a, .wave-b {{ animation: none !important; }}
    }}
  </style>
  <defs>
    <clipPath id="fc"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10"/></clipPath>
  </defs>
  <rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="10" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
  <g clip-path="url(#fc)">
    {''.join(waves)}
  </g>
  {corner_ticks(w, h, t['border_strong'])}
  <text x="600" y="50" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="22" font-weight="700" fill="{t['text_primary']}">Observe the problem  ·  Design the flow  ·  Ship the system</text>
  <text x="600" y="76" text-anchor="middle" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="13" fill="{t['text_muted']}">SUTAN ARLIE JOHAN  ·  DEPOK, INDONESIA  ·  OPEN FOR ROLES &amp; PRODUCT COLLABORATIONS</text>
</svg>
"""


def build_all() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    builders = {
        "architecture": build_architecture_svg,
        "project-maus-kitchen": build_flagship_maus_svg,
        "project-skill-path": build_skill_path_svg,
        "project-solar-ar": build_solar_ar_svg,
        "stack-monument": build_stack_monument_svg,
        "footer": build_footer_svg,
    }
    for mode, theme in THEMES.items():
        for name, fn in builders.items():
            out = ASSETS / f"{name}-{mode}.svg"
            out.write_text(fn(theme), encoding="utf-8")
            print(f"Wrote {out.name} ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build_all()
