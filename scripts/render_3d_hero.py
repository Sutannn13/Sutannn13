#!/usr/bin/env python3
"""Render true 3D PBR raymarched hero banners (dark & light) as seamless-loop APNGs.

Uses headless Chromium WebGL2 via Playwright with 2x2 supersampled SDF raymarching,
soft penumbra shadows, multi-tap ambient occlusion, Cook-Torrance specular shading,
and delta-bounding-box APNG compression so static typography stays crisp and compact.
"""

from __future__ import annotations

import io
import json
import struct
import zlib
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

WIDTH = 1200
HEIGHT = 380
FRAMES = 44          # 44 frames @ ~18.2 fps = 2.42s seamless 90-deg symmetric architectural loop
DURATION_MS = 55     # 55ms per frame (silky slow cadence + compact APNG)

THEMES = {
    "dark": {
        "out": ASSETS / "hero-dark.png",
        "surface": "#14171c",
        "surface_rgb": (0.0784, 0.0902, 0.1100),
        "border": "#2c323c",
        "tick": "#5b6575",
        "text_primary": "#f3efe6",
        "text_secondary": "#b6b1a6",
        "text_muted": "#969187",
        "accent": "#e57a52",
        "accent_rgb": (0.898, 0.478, 0.322),
        "brass_rgb": (0.851, 0.643, 0.357),
        "slab_rgb": (0.155, 0.178, 0.215),
        "plinth_rgb": (0.098, 0.112, 0.136),
        "is_light": 0.0,
    },
    "light": {
        "out": ASSETS / "hero-light.png",
        "surface": "#f7f4ee",
        "surface_rgb": (0.9686, 0.9569, 0.9333),
        "border": "#d6cfc2",
        "tick": "#766f64",
        "text_primary": "#161614",
        "text_secondary": "#4a4741",
        "text_muted": "#5c5850",
        "accent": "#b5451b",
        "accent_rgb": (0.710, 0.271, 0.106),
        "brass_rgb": (0.240, 0.220, 0.195),
        "slab_rgb": (0.855, 0.825, 0.775),
        "plinth_rgb": (0.915, 0.894, 0.858),
        "is_light": 1.0,
    },
}

FRAG_SHADER = r"""#version 300 es
precision highp float;

out vec4 fragColor;

uniform vec2 u_res;
uniform float u_time;
uniform vec3 u_bg;
uniform vec3 u_slab;
uniform vec3 u_accent;
uniform vec3 u_brass;
uniform vec3 u_plinth;
uniform float u_light;

const float PI = 3.14159265359;
const float TAU = 6.28318530718;

mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

// Returns vec2(distance, materialId)
// 1 = architectural monolith slab
// 2 = kiln terracotta inner core & inner gimbal ring
// 3 = brushed brass / graphite outer gimbal ring
// 4 = telemetry orbital nodes
// 5 = matte floor plinth
vec2 opU(vec2 a, vec2 b) { return (a.x < b.x) ? a : b; }

vec2 mapScene(vec3 p) {
    float phase = u_time * TAU;

    // Gentle sculptural levitation (100% periodic)
    float hover = 0.055 * sin(phase);

    // 90-degree 4-fold symmetric rotation so chamfered square slabs loop seamlessly
    // with calm, unhurried architectural speed.
    float coreYaw = 0.62 + u_time * (PI * 0.5);
    float corePitch = 0.045 * sin(phase);

    vec3 pc = p - vec3(0.0, 0.16 + hover, 0.0);
    pc.yz *= rot(corePitch);
    pc.xz *= rot(coreYaw);

    // Three interlocking chamfered architectural slabs: Data / API / Product
    float gap = 0.03 * sin(phase);
    vec3 pTop = pc - vec3(0.0, 0.44 + gap, 0.0);
    vec3 pMid = pc;
    vec3 pBot = pc - vec3(0.0, -0.44 - gap, 0.0);

    // Subtle counter-twist on top and bottom slabs for kinetic articulation
    pTop.xz *= rot(0.14 * sin(phase));
    pBot.xz *= rot(-0.14 * sin(phase));

    float dTop = sdRoundBox(pTop, vec3(0.46, 0.125, 0.46), 0.042);
    float dMid = sdRoundBox(pMid, vec3(0.54, 0.155, 0.54), 0.048);
    float dBot = sdRoundBox(pBot, vec3(0.48, 0.125, 0.48), 0.042);

    // Precision architectural notch carved into middle slab
    float dNotch = sdRoundBox(pMid, vec3(0.62, 0.042, 0.62), 0.012);
    float dSlabs = min(dTop, min(max(dMid, -dNotch), dBot));

    // Inner glowing/anodized terracotta architectural spine connecting all 3 slabs
    float dSpine = sdRoundBox(pc, vec3(0.32, 0.50, 0.32), 0.035);

    vec2 res = vec2(dSlabs, 1.0);
    res = opU(res, vec2(dSpine, 2.0));

    // Outer machined orbital gimbal ring (brushed brass / anodized graphite)
    vec3 po = p - vec3(0.0, 0.16 + hover * 0.5, 0.0);
    po.xy *= rot(0.38 + 0.10 * sin(phase));
    po.yz *= rot(0.34 + 0.10 * cos(phase));
    float dOuterRing = sdTorus(po, vec2(1.20, 0.030));
    res = opU(res, vec2(dOuterRing, 3.0));

    // Three orbital telemetry nodes spaced 120 deg apart; advancing by 120 deg loops seamlessly
    float nodeBase = u_time * (TAU / 3.0);
    float dNodes = 1e5;
    for (int i = 0; i < 3; i++) {
        float a = nodeBase + float(i) * (TAU / 3.0);
        vec3 np = vec3(cos(a) * 1.20, 0.0, sin(a) * 1.20);
        dNodes = min(dNodes, length(po - np) - 0.072);
    }
    res = opU(res, vec2(dNodes, 4.0));

    // Inner counter-tilted kiln terracotta gimbal ring
    vec3 pi = p - vec3(0.0, 0.16 + hover * 0.7, 0.0);
    pi.xy *= rot(-0.56 - 0.12 * cos(phase));
    pi.yz *= rot(-0.28 + 0.12 * sin(phase));
    float dInnerRing = sdTorus(pi, vec2(0.92, 0.022));
    res = opU(res, vec2(dInnerRing, 2.0));

    // Recessed architectural studio plinth plane for grounded soft shadows
    float dFloor = p.y + 1.08;
    float dDisc = sdCylinder(p - vec3(0.0, -1.11, 0.0), 0.04, 1.48);
    res = opU(res, vec2(min(dFloor, dDisc), 5.0));

    return res;
}

vec3 calcNormal(vec3 p) {
    const vec2 e = vec2(0.0012, -0.0012);
    return normalize(
        e.xyy * mapScene(p + e.xyy).x +
        e.yyx * mapScene(p + e.yyx).x +
        e.yxy * mapScene(p + e.yxy).x +
        e.xxx * mapScene(p + e.xxx).x
    );
}

float calcSoftShadow(vec3 ro, vec3 rd, float mint, float maxt, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 20; i++) {
        float h = mapScene(ro + rd * t).x;
        res = min(res, k * h / t);
        t += clamp(h, 0.025, 0.25);
        if (res < 0.004 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 4; i++) {
        float h = 0.025 + 0.11 * float(i) / 3.0;
        float d = mapScene(pos + h * nor).x;
        occ += (h - d) * sca;
        sca *= 0.78;
    }
    return clamp(1.0 - 2.3 * occ, 0.0, 1.0);
}

vec3 aces(vec3 x) {
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

vec3 renderPixel(vec2 uv) {
    // Camera positioned cleanly with generous gallery margin so rings & floor shadow never clip
    vec3 ro = vec3(0.0, 0.78, 4.58);
    vec3 ta = vec3(0.0, -0.02, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 2.02 * ww);

    // Localized studio vignette smoothly tapering to 0 before canvas edges (zero seam at x=638)
    float edgeFade = smoothstep(0.68, 0.12, length(uv * vec2(0.88, 1.12)));
    vec3 bgCol = u_bg;
    if (u_light < 0.5) {
        bgCol += vec3(0.026, 0.023, 0.020) * edgeFade;
    } else {
        bgCol -= vec3(0.024, 0.020, 0.015) * edgeFade;
    }

    // Fast analytic bounding-sphere rejection for background pixels
    vec3 oc = ro - vec3(0.0, -0.04, 0.0);
    float b = dot(oc, rd);
    float c = dot(oc, oc) - 1.92 * 1.92;
    float disc = b * b - c;
    if (disc < 0.0) {
        return bgCol;
    }
    float tStart = max(0.0, -b - sqrt(disc));
    float tMax = min(9.5, -b + sqrt(disc) + 1.5);

    float t = tStart;
    float mat = -1.0;
    for (int i = 0; i < 64; i++) {
        vec3 p = ro + rd * t;
        vec2 h = mapScene(p);
        if (h.x < 0.0016) {
            mat = h.y;
            break;
        }
        t += h.x;
        if (t > tMax) break;
    }

    if (mat < 0.0) {
        return bgCol;
    }

    vec3 pos = ro + rd * t;
    vec3 nor = calcNormal(pos);
    vec3 viewDir = -rd;

    // Studio 3-point lighting rig
    vec3 keyDir = normalize(vec3(-0.62, 0.85, 0.65));
    vec3 fillDir = normalize(vec3(0.75, 0.35, 0.45));
    vec3 rimDir = normalize(vec3(0.42, 0.55, -0.78));

    float keyDiff = max(dot(nor, keyDir), 0.0);
    float fillDiff = max(dot(nor, fillDir), 0.0);
    float rimDiff = max(dot(nor, rimDir), 0.0);

    float sh = calcSoftShadow(pos + nor * 0.006, keyDir, 0.02, 5.5, 10.0);
    float ao = calcAO(pos, nor);
    float fresnel = pow(clamp(1.0 - max(dot(nor, viewDir), 0.0), 0.0, 1.0), 3.6);

    // Ground plane / plinth: dissolve cleanly into backdrop so zero horizon box edge exists
    if (mat > 4.5) {
        float r2 = dot(pos.xz, pos.xz);
        float mask = exp(-r2 * 0.52);
        // Subtle shadow + ambient occlusion contact on studio floor
        float shadowFactor = mix(1.0, 0.55 + 0.45 * sh, mask);
        float aoFactor = mix(1.0, 0.72 + 0.28 * ao, mask);
        // Subtle architectural plinth rim ring
        float ringHint = smoothstep(0.03, 0.0, abs(length(pos.xz) - 1.44)) * 0.14;
        vec3 floorCol = bgCol * shadowFactor * aoFactor;
        if (u_light < 0.5) {
            floorCol += vec3(0.18, 0.19, 0.21) * ringHint;
        } else {
            floorCol -= vec3(0.12, 0.11, 0.10) * ringHint;
        }
        return mix(bgCol, floorCol, mask);
    }

    // Material properties
    vec3 albedo = u_slab;
    float specPower = 38.0;
    float specStrength = 0.45;
    float metallic = 0.25;
    vec3 emissive = vec3(0.0);

    if (mat < 1.5) {
        // Matte satin architectural slab (obsidian in dark, honed travertine in light)
        albedo = u_slab;
        specPower = (u_light < 0.5) ? 42.0 : 22.0;
        specStrength = (u_light < 0.5) ? 0.50 : 0.22;
        metallic = (u_light < 0.5) ? 0.35 : 0.06;
        // Subtle terracotta bounce near inner core gap
        float coreProx = exp(-abs(pos.y - 0.16) * 5.0) * exp(-length(pos.xz) * 1.4);
        emissive = u_accent * coreProx * ((u_light < 0.5) ? 0.22 : 0.09);
    } else if (mat < 2.5) {
        // Kiln terracotta ceramic/anodized core & inner gimbal ring
        albedo = u_accent;
        specPower = 54.0;
        specStrength = 0.55;
        metallic = 0.22;
        emissive = u_accent * ((u_light < 0.5) ? 0.14 : 0.04);
    } else if (mat < 3.5) {
        // Brushed architectural brass (dark) / dark machined bronze (light)
        albedo = u_brass;
        specPower = 88.0;
        specStrength = 0.95;
        metallic = 0.84;
    } else {
        // Orbital telemetry spheres (polished kiln terracotta)
        albedo = mix(u_accent, vec3(1.0, 0.85, 0.72), 0.22);
        specPower = 96.0;
        specStrength = 0.92;
        metallic = 0.55;
        emissive = u_accent * ((u_light < 0.5) ? 0.26 : 0.08);
    }

    vec3 keyH = normalize(keyDir + viewDir);
    vec3 rimH = normalize(rimDir + viewDir);
    float keySpec = pow(max(dot(nor, keyH), 0.0), specPower) * specStrength;
    float rimSpec = pow(max(dot(nor, rimH), 0.0), specPower * 0.5) * specStrength * 0.45;

    vec3 keyCol = (u_light < 0.5) ? vec3(1.06, 0.98, 0.88) : vec3(1.05, 1.02, 0.96);
    vec3 fillCol = (u_light < 0.5) ? vec3(0.42, 0.48, 0.58) : vec3(0.68, 0.72, 0.78);
    vec3 rimCol = (u_light < 0.5) ? vec3(0.95, 0.76, 0.62) : vec3(0.92, 0.88, 0.82);

    vec3 specTint = mix(vec3(1.0), albedo, metallic);
    vec3 amb = albedo * ((u_light < 0.5) ? vec3(0.24, 0.26, 0.30) : vec3(0.56, 0.55, 0.53));

    vec3 col = amb * ao;
    col += albedo * (1.0 - 0.55 * metallic) * keyCol * keyDiff * (0.28 + 0.72 * sh);
    col += albedo * (1.0 - 0.45 * metallic) * fillCol * fillDiff * 0.48 * ao;
    col += specTint * keyCol * keySpec * (0.35 + 0.65 * sh);
    col += specTint * rimCol * (rimSpec + fresnel * ((u_light < 0.5) ? 0.42 : 0.22)) * (0.4 + 0.6 * rimDiff);
    col += emissive;

    // Gentle filmic curve preserving exact brand palette fidelity
    col = mix(col, aces(col * 1.06), 0.55);
    return clamp(col, 0.0, 1.0);
}

void main() {
    // 2x rotated-grid supersampling for crisp anti-aliased bevels at high speed
    vec2 uv1 = (gl_FragCoord.xy + vec2(-0.25, -0.25) - 0.5 * u_res) / u_res.y;
    vec2 uv2 = (gl_FragCoord.xy + vec2( 0.25,  0.25) - 0.5 * u_res) / u_res.y;
    vec3 col = 0.5 * (renderPixel(uv1) + renderPixel(uv2));
    fragColor = vec4(col, 1.0);
}
"""

VERT_SHADER = r"""#version 300 es
in vec2 a_pos;
void main() {
    gl_Position = vec4(a_pos, 0.0, 1.0);
}
"""


def build_html(theme: dict) -> str:
    cfg = json.dumps({
        "bg": list(theme["surface_rgb"]),
        "slab": list(theme["slab_rgb"]),
        "accent": list(theme["accent_rgb"]),
        "brass": list(theme["brass_rgb"]),
        "plinth": list(theme["plinth_rgb"]),
        "isLight": theme["is_light"],
    })
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: {WIDTH}px;
    height: {HEIGHT}px;
    overflow: hidden;
    background: {theme["surface"]};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .card {{
    position: relative;
    width: {WIDTH}px;
    height: {HEIGHT}px;
    background: {theme["surface"]};
    border: 1.5px solid {theme["border"]};
    border-radius: 10px;
    overflow: hidden;
  }}
  #gl {{
    position: absolute;
    right: 2px;
    top: 2px;
    width: 560px;
    height: 376px;
    display: block;
  }}
  .content {{
    position: relative;
    z-index: 2;
    width: 650px;
    height: 100%;
    padding: 48px 0 44px 56px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .kicker {{
    font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace;
    font-size: 12.5px;
    letter-spacing: 1.4px;
    color: {theme["text_muted"]};
    text-transform: uppercase;
  }}
  .headline-block {{
    margin-top: -4px;
  }}
  h1 {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 50px;
    font-weight: 700;
    line-height: 1.08;
    letter-spacing: -0.4px;
    color: {theme["text_primary"]};
  }}
  .rule {{
    width: 56px;
    height: 3px;
    background: {theme["accent"]};
    margin: 18px 0 18px 0;
  }}
  .lead {{
    font-size: 18px;
    line-height: 1.5;
    color: {theme["text_secondary"]};
    max-width: 540px;
  }}
  .stack {{
    font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace;
    font-size: 13px;
    color: {theme["text_muted"]};
    letter-spacing: 0.3px;
  }}
  .stack strong {{
    color: {theme["accent"]};
    font-weight: 600;
  }}
  .overlay-svg {{
    position: absolute;
    inset: 0;
    width: {WIDTH}px;
    height: {HEIGHT}px;
    pointer-events: none;
    z-index: 3;
  }}
</style>
</head>
<body>
  <div class="card">
    <canvas id="gl" width="560" height="376"></canvas>
    <div class="content">
      <div class="kicker">DEPOK, INDONESIA &nbsp;·&nbsp; BACKEND &amp; FULL-STACK</div>
      <div class="headline-block">
        <h1>Sutan Arlie Johan</h1>
        <div class="rule"></div>
        <p class="lead">Turning operational bottlenecks and scattered data into clear backend systems and web products.</p>
      </div>
      <div class="stack"><strong>CORE</strong> &nbsp; Laravel &middot; TypeScript &middot; REST API &middot; MySQL &middot; Next.js &middot; Supabase</div>
    </div>
    <svg class="overlay-svg" viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg">
      <!-- Architectural registration ticks (identity motif) -->
      <g stroke="{theme["tick"]}" stroke-width="1.2" opacity="0.72" fill="none">
        <path d="M18,30 L18,18 L30,18"/>
        <path d="M1170,18 L1182,18 L1182,30"/>
        <path d="M18,350 L18,362 L30,362"/>
        <path d="M1170,362 L1182,362 L1182,350"/>
        <!-- Precision orbital reticle marks framing the 3D sculpture -->
        <line x1="918" y1="24" x2="918" y2="34"/>
        <line x1="918" y1="346" x2="918" y2="356"/>
        <line x1="654" y1="190" x2="664" y2="190"/>
        <line x1="1172" y1="190" x2="1182" y2="190"/>
      </g>
      <!-- Subtle vertical hairline separating editorial column from 3D studio stage -->
      <line x1="640" y1="42" x2="640" y2="338" stroke="{theme["border"]}" stroke-width="1" stroke-dasharray="3 5"/>
      <text x="1164" y="352" text-anchor="end" font-family="Cascadia Mono, Consolas, monospace" font-size="11" fill="{theme["text_muted"]}">SYS.MODEL / 01</text>
    </svg>
  </div>
<script>
const CFG = {cfg};
const VERT = {json.dumps(VERT_SHADER)};
const FRAG = {json.dumps(FRAG_SHADER)};

const canvas = document.getElementById('gl');
const gl = canvas.getContext('webgl2', {{ preserveDrawingBuffer: true, antialias: false }});
if (!gl) throw new Error('WebGL2 unavailable');

function compile(type, src) {{
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {{
    throw new Error(gl.getShaderInfoLog(s));
  }}
  return s;
}}

const prog = gl.createProgram();
gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
gl.linkProgram(prog);
if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {{
  throw new Error(gl.getProgramInfoLog(prog));
}}
gl.useProgram(prog);

const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'a_pos');
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

const uRes = gl.getUniformLocation(prog, 'u_res');
const uTime = gl.getUniformLocation(prog, 'u_time');
gl.uniform2f(uRes, canvas.width, canvas.height);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_bg'), CFG.bg);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_slab'), CFG.slab);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_accent'), CFG.accent);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_brass'), CFG.brass);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_plinth'), CFG.plinth);
gl.uniform1f(gl.getUniformLocation(prog, 'u_light'), CFG.isLight);

window.renderFrame = function(t) {{
  gl.viewport(0, 0, canvas.width, canvas.height);
  gl.uniform1f(uTime, t);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.finish();
}};
window.renderFrame(0.0);
</script>
</body>
</html>
"""


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _encode_rgb_idat(img: Image.Image) -> bytes:
    """Encode an RGB PIL Image into PNG scanlines + zlib data (Paeth/Sub filter via Pillow)."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    raw = buf.getvalue()
    # Extract concatenated IDAT payload from Pillow-compressed PNG
    pos = 8
    idat_parts: list[bytes] = []
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        cdata = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IDAT":
            idat_parts.append(cdata)
    return b"".join(idat_parts)


def save_delta_apng(frames: list[Image.Image], out_path: Path, duration_ms: int) -> None:
    """Write a true 24-bit APNG where frames 1..N store only the changed 3D bounding box.

    ponytail: computes one shared delta bounding box across frames (O(N) pixel diff)
    so the left editorial typography is stored once in frame 0 while the 3D stage loops
    at full 24-bit RGB without GIF dithering.
    """
    base = frames[0].convert("RGB")
    w, h = base.size

    # Find minimal bounding box covering every pixel that changes across the loop
    x0, y0, x1, y1 = w, h, 0, 0
    for f in frames[1:]:
        diff = ImageChops.difference(base, f.convert("RGB"))
        bbox = diff.getbbox()
        if bbox:
            x0 = min(x0, bbox[0])
            y0 = min(y0, bbox[1])
            x1 = max(x1, bbox[2])
            y1 = max(y1, bbox[3])
    if x1 <= x0 or y1 <= y0:
        x0, y0, x1, y1 = 0, 0, w, h

    dw, dh = x1 - x0, y1 - y0
    chunks: list[bytes] = [b"\x89PNG\r\n\x1a\n"]

    # IHDR: 8-bit truecolor RGB (color_type=2)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    chunks.append(_png_chunk(b"IHDR", ihdr))

    # acTL: num_frames, num_plays=0 (infinite seamless loop)
    chunks.append(_png_chunk(b"acTL", struct.pack(">II", len(frames), 0)))

    seq = 0
    # Frame 0: full canvas (also serves as crisp static PNG fallback)
    fc0 = struct.pack(">IIIIIHHBB", seq, w, h, 0, 0, duration_ms, 1000, 0, 0)
    seq += 1
    chunks.append(_png_chunk(b"fcTL", fc0))
    chunks.append(_png_chunk(b"IDAT", _encode_rgb_idat(base)))

    # Frames 1..N-1: cropped to exact changed 3D stage box (dispose=0, blend=0 overwrite)
    for f in frames[1:]:
        crop = f.convert("RGB").crop((x0, y0, x1, y1))
        fctl = struct.pack(">IIIIIHHBB", seq, dw, dh, x0, y0, duration_ms, 1000, 0, 0)
        seq += 1
        chunks.append(_png_chunk(b"fcTL", fctl))
        fdat_payload = struct.pack(">I", seq) + _encode_rgb_idat(crop)
        seq += 1
        chunks.append(_png_chunk(b"fdAT", fdat_payload))

    chunks.append(_png_chunk(b"IEND", b""))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"".join(chunks))
    kb = out_path.stat().st_size / 1024
    print(f"Wrote {out_path.name}: {len(frames)} frames, delta box=({x0},{y0},{x1},{y1}) [{dw}x{dh}], {kb:.1f} KB")


def render_all() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        for name, theme in THEMES.items():
            page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
            page.set_content(build_html(theme), wait_until="load")
            frames: list[Image.Image] = []
            # Capture full canvas for frame 0, then clip-screenshot only the 3D stage for frames 1..N-1
            page.evaluate("window.renderFrame(0.0)")
            base_img = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
            frames.append(base_img)
            stage_clip = {"x": 638, "y": 2, "width": 560, "height": 376}
            for i in range(1, FRAMES):
                t = i / FRAMES
                page.evaluate(f"window.renderFrame({t:.8f})")
                patch_bytes = page.screenshot(type="png", clip=stage_clip)
                patch = Image.open(io.BytesIO(patch_bytes)).convert("RGB")
                full = base_img.copy()
                full.paste(patch, (638, 2))
                frames.append(full)
                if (i + 1) % 12 == 0:
                    print(f"  [{name}] rendered {i + 1}/{FRAMES} frames", flush=True)
            page.close()
            save_delta_apng(frames, theme["out"], DURATION_MS)
        browser.close()


if __name__ == "__main__":
    render_all()
