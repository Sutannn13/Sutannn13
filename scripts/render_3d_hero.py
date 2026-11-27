#!/usr/bin/env python3
"""Render cinema-grade WebGL2 PBR raymarched 3D APNG showcases (dark & light).

Renders TWO true PBR 3D seamless-loop centerpieces:
1. Hero (1200x392): Machined architectural monolith astrolabe with studio softbox
   reflections, micro-milled brass gimbal ring, 4 orbiting chamfered satellite cubes,
   recessed terracotta diffuser slits, soft penumbra shadow, and subtle satin floor reflection.
2. Flagship Mau's Kitchen (1200x284): True 3D perspective operations diorama with 3
   beveled plinth stages (Menu -> Queue -> Served) and physically-shaded terracotta/brass
   order cubes arcing smoothly across the stages with live moving cast shadows.
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

HERO_W, HERO_H, HERO_FRAMES, HERO_MS = 1200, 392, 40, 55
MAUS_W, MAUS_H, MAUS_FRAMES, MAUS_MS = 1200, 284, 36, 60

THEMES = {
    "dark": {
        "shell": "#0f1217",
        "shell_border": "#252c37",
        "surface": "#151920",
        "surface_warm": "#18171a",
        "surface_rgb": (0.0824, 0.0980, 0.1255),
        "warm_rgb": (0.0941, 0.0902, 0.1020),
        "inner_border": "#2c3340",
        "rim_top": "rgba(255, 248, 236, 0.14)",
        "tick": "#5b6575",
        "text_primary": "#f3efe6",
        "text_secondary": "#b6b1a6",
        "text_muted": "#969187",
        "accent": "#e57a52",
        "accent_rgb": (0.915, 0.490, 0.325),
        "brass_rgb": (0.890, 0.680, 0.385),
        "slab_rgb": (0.160, 0.188, 0.232),
        "raised": "#1e232d",
        "live": "#72c495",
        "live_bg": "#14261d",
        "grain_opacity": "0.026",
        "is_light": 0.0,
    },
    "light": {
        "shell": "#ebe5da",
        "shell_border": "#d2cabd",
        "surface": "#f7f4ee",
        "surface_warm": "#f9f4ec",
        "surface_rgb": (0.9686, 0.9569, 0.9333),
        "warm_rgb": (0.9765, 0.9569, 0.9255),
        "inner_border": "#dcd5c8",
        "rim_top": "rgba(255, 255, 255, 0.90)",
        "tick": "#766f64",
        "text_primary": "#161614",
        "text_secondary": "#4a4741",
        "text_muted": "#5c5850",
        "accent": "#b5451b",
        "accent_rgb": (0.715, 0.275, 0.110),
        "brass_rgb": (0.235, 0.215, 0.190),
        "slab_rgb": (0.865, 0.835, 0.785),
        "raised": "#ece6db",
        "live": "#1e6b43",
        "live_bg": "#e3f0e8",
        "grain_opacity": "0.020",
        "is_light": 1.0,
    },
}

VERT_SHADER = r"""#version 300 es
in vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
"""

# ---------------------------------------------------------------------------
# SHADER 1: HERO ARCHITECTURAL ASTROLABE (softbox reflections + floor bounce)
# ---------------------------------------------------------------------------
HERO_FRAG_SHADER = r"""#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2 u_res;
uniform float u_time;
uniform vec3 u_bg;
uniform vec3 u_slab;
uniform vec3 u_accent;
uniform vec3 u_brass;
uniform float u_light;

const float PI = 3.14159265359;
const float TAU = 6.28318530718;

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }

float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

vec2 opU(vec2 a, vec2 b) { return (a.x < b.x) ? a : b; }

vec2 mapScene(vec3 p) {
    float phase = u_time * TAU;
    float hover = 0.056 * sin(phase);
    // 90-degree 4-fold symmetric architectural turn for unhurried seamless loop
    float coreYaw = 0.62 + u_time * (PI * 0.5);
    float corePitch = 0.044 * sin(phase);

    vec3 pc = p - vec3(0.0, 0.16 + hover, 0.0);
    pc.yz *= rot(corePitch);
    pc.xz *= rot(coreYaw);

    float gap = 0.032 * sin(phase);
    vec3 pTop = pc - vec3(0.0, 0.44 + gap, 0.0);
    vec3 pMid = pc;
    vec3 pBot = pc - vec3(0.0, -0.44 - gap, 0.0);

    pTop.xz *= rot(0.15 * sin(phase));
    pBot.xz *= rot(-0.15 * sin(phase));

    // Machined monolith slabs with fine architectural relief grooves
    float dTop = sdRoundBox(pTop, vec3(0.45, 0.122, 0.45), 0.042);
    float dTopCut = sdRoundBox(pTop - vec3(0.0, 0.035, 0.0), vec3(0.50, 0.016, 0.50), 0.005);
    dTop = max(dTop, -dTopCut);

    float dMid = sdRoundBox(pMid, vec3(0.54, 0.155, 0.54), 0.048);
    float dMidNotch = sdRoundBox(pMid, vec3(0.62, 0.042, 0.62), 0.010);
    dMid = max(dMid, -dMidNotch);

    float dBot = sdRoundBox(pBot, vec3(0.47, 0.122, 0.47), 0.042);
    float dBotCut = sdRoundBox(pBot - vec3(0.0, -0.035, 0.0), vec3(0.52, 0.016, 0.52), 0.005);
    dBot = max(dBot, -dBotCut);

    // Subtle brass cap bezel sitting atop top monolith
    float dCap = sdRoundBox(pTop - vec3(0.0, 0.155, 0.0), vec3(0.24, 0.016, 0.24), 0.010);

    float dSlabs = min(dTop, min(dMid, dBot));
    float dSpine = sdRoundBox(pc, vec3(0.32, 0.50, 0.32), 0.035);

    vec2 res = vec2(dSlabs, 1.0);
    res = opU(res, vec2(dSpine, 2.0));
    res = opU(res, vec2(dCap, 3.0));

    // Outer machined orbital gimbal ring with subtle micro-milled knurling
    vec3 po = p - vec3(0.0, 0.16 + hover * 0.5, 0.0);
    po.xy *= rot(0.37 + 0.09 * sin(phase));
    po.yz *= rot(0.33 + 0.09 * cos(phase));
    float ringAngle = atan(po.z, po.x);
    float knurl = 0.0028 * sin(ringAngle * 36.0);
    float dOuterRing = sdTorus(po, vec2(1.22, 0.031 + knurl));
    res = opU(res, vec2(dOuterRing, 3.0));

    // 4 chamfered precision satellite cubes orbiting seamlessly (90-deg shift = identical!)
    float satBase = u_time * (PI * 0.5);
    float dSats = 1e5;
    for (int i = 0; i < 4; i++) {
        float a = satBase + float(i) * (PI * 0.5);
        vec3 sp = po - vec3(cos(a) * 1.22, 0.0, sin(a) * 1.22);
        sp.xz *= rot(-a + phase);
        sp.xy *= rot(0.55);
        dSats = min(dSats, sdRoundBox(sp, vec3(0.056, 0.056, 0.056), 0.016));
    }
    res = opU(res, vec2(dSats, 4.0));

    // Inner counter-tilted kiln terracotta gimbal ring
    vec3 pi = p - vec3(0.0, 0.16 + hover * 0.7, 0.0);
    pi.xy *= rot(-0.56 - 0.11 * cos(phase));
    pi.yz *= rot(-0.28 + 0.11 * sin(phase));
    float dInnerRing = sdTorus(pi, vec2(0.92, 0.022));
    res = opU(res, vec2(dInnerRing, 2.0));

    // Studio floor plane for penumbra shadows & satin planar reflection
    float dFloor = p.y + 1.07;
    res = opU(res, vec2(dFloor, 5.0));

    return res;
}

vec3 calcNormal(vec3 p) {
    const vec2 e = vec2(0.0012, -0.0012);
    return normalize(
        e.xyy * mapScene(p + e.xyy).x + e.yyx * mapScene(p + e.yyx).x +
        e.yxy * mapScene(p + e.yxy).x + e.xxx * mapScene(p + e.xxx).x
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
    float occ = 0.0, sca = 1.0;
    for (int i = 0; i < 4; i++) {
        float h = 0.024 + 0.11 * float(i) / 3.0;
        occ += (h - mapScene(pos + h * nor).x) * sca;
        sca *= 0.78;
    }
    return clamp(1.0 - 2.35 * occ, 0.0, 1.0);
}

// Procedural studio softbox environment reflections (overhead warm strip + cool key strip)
vec3 sampleStudioEnv(vec3 r) {
    float overhead = smoothstep(0.62, 0.92, r.y) * smoothstep(0.55, 0.12, abs(r.x + 0.15));
    float sideStrip = smoothstep(0.55, 0.88, dot(r, normalize(vec3(-0.75, 0.45, 0.48))));
    float rimStrip = smoothstep(0.62, 0.92, dot(r, normalize(vec3(0.55, 0.38, -0.74))));
    vec3 warmBox = (u_light < 0.5) ? vec3(1.15, 1.02, 0.88) : vec3(1.12, 1.08, 1.02);
    vec3 coolBox = (u_light < 0.5) ? vec3(0.58, 0.68, 0.84) : vec3(0.84, 0.88, 0.94);
    vec3 terracottaRim = u_accent * ((u_light < 0.5) ? 0.85 : 0.45);
    return warmBox * overhead * 0.75 + coolBox * sideStrip * 0.48 + terracottaRim * rimStrip * 0.45;
}

vec3 aces(vec3 x) {
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

vec3 shadeObject(vec3 pos, vec3 nor, vec3 viewDir, float mat) {
    vec3 keyDir = normalize(vec3(-0.62, 0.86, 0.64));
    vec3 fillDir = normalize(vec3(0.76, 0.36, 0.44));
    vec3 rimDir = normalize(vec3(0.42, 0.56, -0.78));

    float keyDiff = max(dot(nor, keyDir), 0.0);
    float fillDiff = max(dot(nor, fillDir), 0.0);
    float rimDiff = max(dot(nor, rimDir), 0.0);
    float sh = calcSoftShadow(pos + nor * 0.006, keyDir, 0.02, 5.5, 10.5);
    float ao = calcAO(pos, nor);
    float fresnel = pow(clamp(1.0 - max(dot(nor, viewDir), 0.0), 0.0, 1.0), 3.2);
    vec3 reflDir = reflect(-viewDir, nor);
    vec3 envRefl = sampleStudioEnv(reflDir);

    vec3 albedo = u_slab;
    float specPower = 44.0, specStrength = 0.55, metallic = 0.35, envStrength = 0.38;
    vec3 emissive = vec3(0.0);

    if (mat < 1.5) {
        albedo = u_slab;
        specPower = (u_light < 0.5) ? 56.0 : 26.0;
        specStrength = (u_light < 0.5) ? 0.66 : 0.28;
        metallic = (u_light < 0.5) ? 0.48 : 0.08;
        envStrength = (u_light < 0.5) ? 0.44 : 0.18;
        float coreProx = exp(-abs(pos.y - 0.16) * 4.5) * exp(-length(pos.xz) * 1.25);
        emissive = u_accent * coreProx * ((u_light < 0.5) ? 0.34 : 0.11);
    } else if (mat < 2.5) {
        albedo = u_accent;
        specPower = 64.0; specStrength = 0.65; metallic = 0.25; envStrength = 0.34;
        emissive = u_accent * ((u_light < 0.5) ? 0.19 : 0.05);
    } else if (mat < 3.5) {
        albedo = u_brass;
        specPower = 112.0; specStrength = 1.15; metallic = 0.90; envStrength = 0.72;
    } else {
        albedo = mix(u_accent, vec3(1.0, 0.88, 0.76), 0.25);
        specPower = 108.0; specStrength = 1.0; metallic = 0.62; envStrength = 0.55;
        emissive = u_accent * ((u_light < 0.5) ? 0.30 : 0.09);
    }

    vec3 keyH = normalize(keyDir + viewDir);
    vec3 rimH = normalize(rimDir + viewDir);
    float keySpec = pow(max(dot(nor, keyH), 0.0), specPower) * specStrength;
    float rimSpec = pow(max(dot(nor, rimH), 0.0), specPower * 0.5) * specStrength * 0.48;

    vec3 keyCol = (u_light < 0.5) ? vec3(1.10, 1.00, 0.90) : vec3(1.06, 1.03, 0.97);
    vec3 fillCol = (u_light < 0.5) ? vec3(0.42, 0.50, 0.62) : vec3(0.68, 0.72, 0.78);
    vec3 rimCol = (u_light < 0.5) ? vec3(0.98, 0.78, 0.62) : vec3(0.92, 0.88, 0.82);

    vec3 specTint = mix(vec3(1.0), albedo, metallic);
    vec3 amb = albedo * ((u_light < 0.5) ? vec3(0.22, 0.25, 0.30) : vec3(0.55, 0.54, 0.52));

    vec3 col = amb * ao;
    col += albedo * (1.0 - 0.55 * metallic) * keyCol * keyDiff * (0.28 + 0.72 * sh);
    col += albedo * (1.0 - 0.45 * metallic) * fillCol * fillDiff * 0.46 * ao;
    col += specTint * keyCol * keySpec * (0.35 + 0.65 * sh);
    col += specTint * envRefl * envStrength * (0.25 + 0.75 * fresnel) * ao;
    col += specTint * rimCol * (rimSpec + fresnel * ((u_light < 0.5) ? 0.48 : 0.24)) * (0.4 + 0.6 * rimDiff);
    col += emissive;
    return col;
}

vec3 renderPixel(vec2 uv) {
    vec3 ro = vec3(0.0, 0.78, 4.55);
    vec3 ta = vec3(0.0, -0.02, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 2.02 * ww);

    float edgeFade = smoothstep(0.66, 0.10, length(uv * vec2(0.88, 1.10)));
    vec3 bgCol = u_bg;
    if (u_light < 0.5) {
        bgCol += vec3(0.036, 0.027, 0.022) * edgeFade;
    } else {
        bgCol -= vec3(0.024, 0.020, 0.015) * edgeFade;
    }

    vec3 oc = ro - vec3(0.0, -0.04, 0.0);
    float b = dot(oc, rd);
    float c = dot(oc, oc) - 1.96 * 1.96;
    float disc = b * b - c;
    if (disc < 0.0) return bgCol;

    float tStart = max(0.0, -b - sqrt(disc));
    float tMax = min(9.5, -b + sqrt(disc) + 1.5);
    float t = tStart, mat = -1.0;
    for (int i = 0; i < 64; i++) {
        vec2 h = mapScene(ro + rd * t);
        if (h.x < 0.0014) { mat = h.y; break; }
        t += h.x;
        if (t > tMax) break;
    }
    if (mat < 0.0) return bgCol;

    vec3 pos = ro + rd * t;
    vec3 nor = calcNormal(pos);
    vec3 viewDir = -rd;

    if (mat > 4.5) {
        float r2 = dot(pos.xz, pos.xz);
        float mask = exp(-r2 * 0.50);
        vec3 keyDir = normalize(vec3(-0.62, 0.86, 0.64));
        float sh = calcSoftShadow(pos + nor * 0.006, keyDir, 0.02, 5.5, 9.5);
        float ao = calcAO(pos, nor);
        float shadowFactor = mix(1.0, 0.52 + 0.48 * sh, mask);
        float aoFactor = mix(1.0, 0.70 + 0.30 * ao, mask);
        float ringHint = smoothstep(0.026, 0.0, abs(length(pos.xz) - 1.44)) * 0.14;
        vec3 floorCol = bgCol * shadowFactor * aoFactor;
        if (u_light < 0.5) floorCol += vec3(0.20, 0.21, 0.24) * ringHint;
        else floorCol -= vec3(0.12, 0.11, 0.10) * ringHint;

        // Subtle satin planar reflection bounce on studio floor!
        if (mask > 0.08) {
            vec3 rrd = reflect(rd, nor);
            float rt = 0.04, rmat = -1.0;
            for (int j = 0; j < 26; j++) {
                vec2 rh = mapScene(pos + rrd * rt);
                if (rh.x < 0.004) { rmat = rh.y; break; }
                rt += rh.x;
                if (rt > 3.2) break;
            }
            if (rmat > 0.5 && rmat < 4.5) {
                vec3 rpos = pos + rrd * rt;
                vec3 rnor = calcNormal(rpos);
                vec3 rcol = shadeObject(rpos, rnor, -rrd, rmat);
                float reflFade = mask * exp(-rt * 0.72) * ((u_light < 0.5) ? 0.24 : 0.11);
                floorCol = mix(floorCol, rcol, reflFade);
            }
        }
        return mix(bgCol, clamp(floorCol, 0.0, 1.0), mask);
    }

    vec3 col = shadeObject(pos, nor, viewDir, mat);
    col = mix(col, aces(col * 1.06), 0.56);
    return clamp(col, 0.0, 1.0);
}

void main() {
    vec2 uv1 = (gl_FragCoord.xy + vec2(-0.25, -0.25) - 0.5 * u_res) / u_res.y;
    vec2 uv2 = (gl_FragCoord.xy + vec2( 0.25,  0.25) - 0.5 * u_res) / u_res.y;
    fragColor = vec4(0.5 * (renderPixel(uv1) + renderPixel(uv2)), 1.0);
}
"""

# ---------------------------------------------------------------------------
# SHADER 2: FLAGSHIP MAU'S KITCHEN 3D PBR ORDER-FLOW DIORAMA
# ---------------------------------------------------------------------------
MAUS_FRAG_SHADER = r"""#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2 u_res;
uniform float u_time;
uniform vec3 u_bg;
uniform vec3 u_slab;
uniform vec3 u_accent;
uniform vec3 u_brass;
uniform float u_light;

const float PI = 3.14159265359;
const float TAU = 6.28318530718;

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }

float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

vec2 opU(vec2 a, vec2 b) { return (a.x < b.x) ? a : b; }

vec2 mapScene(vec3 p) {
    float ph = u_time * TAU;

    // Three elevated chamfered architectural kitchen operation platforms (Menu -> Queue -> Served)
    float h1 = 0.045 * sin(ph);
    float h2 = 0.055 * sin(ph + 2.094);
    float h3 = 0.045 * sin(ph + 4.188);

    vec3 p1 = p - vec3(-1.12, -0.18 + h1,  0.14);
    vec3 p2 = p - vec3( 0.00,  0.00 + h2, -0.12);
    vec3 p3 = p - vec3( 1.12, -0.14 + h3,  0.16);
    p1.xz *= rot(0.52);
    p2.xz *= rot(0.52);
    p3.xz *= rot(0.52);

    float d1 = sdRoundBox(p1, vec3(0.42, 0.11, 0.42), 0.036);
    float d2 = sdRoundBox(p2, vec3(0.46, 0.13, 0.46), 0.040);
    float d3 = sdRoundBox(p3, vec3(0.42, 0.11, 0.42), 0.036);

    // Subtle brass accent rail linking the 3 stations beneath
    vec3 pr1 = p - vec3(-0.56, -0.26, 0.01);
    pr1.xz *= rot(-0.22);
    float dRail1 = sdRoundBox(pr1, vec3(0.56, 0.018, 0.028), 0.008);

    vec3 pr2 = p - vec3(0.56, -0.24, 0.02);
    pr2.xz *= rot(0.24);
    float dRail2 = sdRoundBox(pr2, vec3(0.56, 0.018, 0.028), 0.008);

    vec2 res = vec2(d1, 1.0);          // Menu slab (obsidian/travertine)
    res = opU(res, vec2(d2, 2.0));     // Active Queue slab (kiln terracotta)
    res = opU(res, vec2(d3, 3.0));     // Served slab (brushed brass)
    res = opU(res, vec2(min(dRail1, dRail2), 3.0));

    // Animated chamfered 3D order cube arcing smoothly Menu -> Queue (seamless loop)
    float u1 = u_time;
    float arc1 = sin(u1 * PI) * 0.52;
    vec3 c1Pos = mix(vec3(-1.12, 0.10 + h1, 0.14), vec3(0.00, 0.28 + h2, -0.12), u1) + vec3(0.0, arc1, 0.0);
    vec3 pc1 = p - c1Pos;
    pc1.xz *= rot(u1 * PI * 1.5);
    pc1.xy *= rot(u1 * PI);
    float dCube1 = sdRoundBox(pc1, vec3(0.115, 0.115, 0.115), 0.026);
    res = opU(res, vec2(dCube1, 4.0));

    // Second order cube arcing smoothly Queue -> Served (exact seamless relay!)
    float u2 = u_time;
    float arc2 = sin(u2 * PI) * 0.50;
    vec3 c2Pos = mix(vec3(0.00, 0.28 + h2, -0.12), vec3(1.12, 0.14 + h3, 0.16), u2) + vec3(0.0, arc2, 0.0);
    vec3 pc2 = p - c2Pos;
    pc2.xz *= rot(-u2 * PI * 1.5);
    pc2.yz *= rot(u2 * PI);
    float dCube2 = sdRoundBox(pc2, vec3(0.115, 0.115, 0.115), 0.026);
    res = opU(res, vec2(dCube2, 2.0));

    // Studio floor for soft penumbra shadows
    res = opU(res, vec2(p.y + 0.64, 5.0));
    return res;
}

vec3 calcNormal(vec3 p) {
    const vec2 e = vec2(0.0014, -0.0014);
    return normalize(
        e.xyy * mapScene(p + e.xyy).x + e.yyx * mapScene(p + e.yyx).x +
        e.yxy * mapScene(p + e.yxy).x + e.xxx * mapScene(p + e.xxx).x
    );
}

float calcSoftShadow(vec3 ro, vec3 rd, float mint, float maxt, float k) {
    float res = 1.0, t = mint;
    for (int i = 0; i < 18; i++) {
        float h = mapScene(ro + rd * t).x;
        res = min(res, k * h / t);
        t += clamp(h, 0.025, 0.24);
        if (res < 0.005 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0, sca = 1.0;
    for (int i = 0; i < 4; i++) {
        float h = 0.024 + 0.10 * float(i) / 3.0;
        occ += (h - mapScene(pos + h * nor).x) * sca;
        sca *= 0.78;
    }
    return clamp(1.0 - 2.2 * occ, 0.0, 1.0);
}

vec3 aces(vec3 x) {
    const float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

vec3 renderPixel(vec2 uv) {
    vec3 ro = vec3(0.0, 1.76, 4.38);
    vec3 ta = vec3(0.0, -0.02, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 2.05 * ww);

    float edgeFade = smoothstep(0.82, 0.10, length(uv * vec2(0.72, 1.15)));
    vec3 bgCol = u_bg;
    if (u_light < 0.5) bgCol += vec3(0.038, 0.024, 0.019) * edgeFade;
    else bgCol -= vec3(0.022, 0.018, 0.013) * edgeFade;

    float t = 0.8, mat = -1.0;
    for (int i = 0; i < 58; i++) {
        vec2 h = mapScene(ro + rd * t);
        if (h.x < 0.0015) { mat = h.y; break; }
        t += h.x;
        if (t > 8.5) break;
    }
    if (mat < 0.0) return bgCol;

    vec3 pos = ro + rd * t;
    vec3 nor = calcNormal(pos);
    vec3 viewDir = -rd;
    vec3 keyDir = normalize(vec3(-0.55, 0.88, 0.60));
    vec3 fillDir = normalize(vec3(0.75, 0.40, 0.45));
    float keyDiff = max(dot(nor, keyDir), 0.0);
    float fillDiff = max(dot(nor, fillDir), 0.0);
    float sh = calcSoftShadow(pos + nor * 0.006, keyDir, 0.02, 4.5, 9.0);
    float ao = calcAO(pos, nor);
    float fresnel = pow(clamp(1.0 - max(dot(nor, viewDir), 0.0), 0.0, 1.0), 3.2);

    if (mat > 4.5) {
        float mask = exp(-dot(pos.xz * vec2(0.52, 0.88), pos.xz * vec2(0.52, 0.88)));
        float sf = mix(1.0, 0.50 + 0.50 * sh, mask);
        float af = mix(1.0, 0.74 + 0.26 * ao, mask);
        return mix(bgCol, bgCol * sf * af, mask);
    }

    vec3 albedo = u_slab;
    float specP = 48.0, specS = 0.55, met = 0.35;
    vec3 emissive = vec3(0.0);
    if (mat < 1.5) {
        albedo = u_slab;
        specP = (u_light < 0.5) ? 54.0 : 24.0;
        specS = (u_light < 0.5) ? 0.60 : 0.22;
        met = (u_light < 0.5) ? 0.42 : 0.08;
    } else if (mat < 2.5) {
        albedo = u_accent;
        specP = 64.0; specS = 0.65; met = 0.25;
        emissive = u_accent * ((u_light < 0.5) ? 0.14 : 0.04);
    } else if (mat < 3.5) {
        albedo = u_brass;
        specP = 96.0; specS = 0.96; met = 0.84;
    } else {
        albedo = mix(u_brass, vec3(1.0, 0.92, 0.80), 0.28);
        specP = 104.0; specS = 1.0; met = 0.72;
        emissive = u_brass * ((u_light < 0.5) ? 0.16 : 0.05);
    }

    vec3 keyH = normalize(keyDir + viewDir);
    float keySpec = pow(max(dot(nor, keyH), 0.0), specP) * specS;
    vec3 keyCol = (u_light < 0.5) ? vec3(1.08, 1.00, 0.90) : vec3(1.05, 1.02, 0.96);
    vec3 fillCol = (u_light < 0.5) ? vec3(0.42, 0.50, 0.62) : vec3(0.68, 0.72, 0.78);
    vec3 specTint = mix(vec3(1.0), albedo, met);
    vec3 amb = albedo * ((u_light < 0.5) ? vec3(0.24, 0.26, 0.31) : vec3(0.56, 0.55, 0.53));

    vec3 col = amb * ao;
    col += albedo * (1.0 - 0.52 * met) * keyCol * keyDiff * (0.30 + 0.70 * sh);
    col += albedo * (1.0 - 0.42 * met) * fillCol * fillDiff * 0.46 * ao;
    col += specTint * keyCol * keySpec * (0.35 + 0.65 * sh);
    col += specTint * fresnel * ((u_light < 0.5) ? 0.28 : 0.14);
    col += emissive;
    col = mix(col, aces(col * 1.05), 0.54);
    return clamp(col, 0.0, 1.0);
}

void main() {
    vec2 uv1 = (gl_FragCoord.xy + vec2(-0.25, -0.25) - 0.5 * u_res) / u_res.y;
    vec2 uv2 = (gl_FragCoord.xy + vec2( 0.25,  0.25) - 0.5 * u_res) / u_res.y;
    fragColor = vec4(0.5 * (renderPixel(uv1) + renderPixel(uv2)), 1.0);
}
"""


def _gl_script(frag_src: str, cfg: dict) -> str:
    return f"""
const CFG = {json.dumps(cfg)};
const VERT = {json.dumps(VERT_SHADER)};
const FRAG = {json.dumps(frag_src)};
const canvas = document.getElementById('gl');
const gl = canvas.getContext('webgl2', {{ preserveDrawingBuffer: true, antialias: false }});
if (!gl) throw new Error('WebGL2 unavailable');
function compile(type, src) {{
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}}
const prog = gl.createProgram();
gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
gl.linkProgram(prog);
if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
gl.useProgram(prog);
const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'a_pos');
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
gl.uniform2f(gl.getUniformLocation(prog, 'u_res'), canvas.width, canvas.height);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_bg'), CFG.bg);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_slab'), CFG.slab);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_accent'), CFG.accent);
gl.uniform3fv(gl.getUniformLocation(prog, 'u_brass'), CFG.brass);
gl.uniform1f(gl.getUniformLocation(prog, 'u_light'), CFG.isLight);
const uTime = gl.getUniformLocation(prog, 'u_time');
window.renderFrame = function(t) {{
  gl.viewport(0, 0, canvas.width, canvas.height);
  gl.uniform1f(uTime, t);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  gl.finish();
}};
window.renderFrame(0.0);
"""


def build_hero_html(theme: dict) -> str:
    cfg = {
        "bg": list(theme["surface_rgb"]),
        "slab": list(theme["slab_rgb"]),
        "accent": list(theme["accent_rgb"]),
        "brass": list(theme["brass_rgb"]),
        "isLight": theme["is_light"],
    }
    return f"""<!doctype html>
<html><head><meta charset="utf-8" /><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {HERO_W}px; height: {HERO_H}px; overflow: hidden; background: {theme["shell"]}; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; -webkit-font-smoothing: antialiased; }}
  .outer {{ width: {HERO_W}px; height: {HERO_H}px; padding: 7px; background: {theme["shell"]}; border: 1.5px solid {theme["shell_border"]}; border-radius: 16px; }}
  .inner {{ position: relative; width: 100%; height: 100%; background: {theme["surface"]}; border: 1px solid {theme["inner_border"]}; border-radius: 10px; overflow: hidden; }}
  #gl {{ position: absolute; right: 0; top: 0; width: 552px; height: 376px; display: block; }}
  .content {{ position: relative; z-index: 2; width: 632px; height: 100%; padding: 46px 0 42px 54px; display: flex; flex-direction: column; justify-content: space-between; }}
  .kicker {{ font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace; font-size: 12.5px; letter-spacing: 1.4px; color: {theme["text_muted"]}; text-transform: uppercase; }}
  h1 {{ font-family: Georgia, 'Times New Roman', serif; font-size: 54px; font-weight: 700; line-height: 1.06; letter-spacing: -0.9px; color: {theme["text_primary"]}; }}
  .rule {{ width: 54px; height: 3px; background: {theme["accent"]}; margin: 18px 0; }}
  .lead {{ font-size: 18.5px; line-height: 1.48; color: {theme["text_secondary"]}; max-width: 515px; }}
  .stack {{ font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace; font-size: 13px; color: {theme["text_muted"]}; letter-spacing: 0.25px; }}
  .stack strong {{ color: {theme["accent"]}; font-weight: 700; }}
  .ov {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 3; }}
</style></head><body>
  <div class="outer"><div class="inner">
    <canvas id="gl" width="552" height="376"></canvas>
    <div class="content">
      <div class="kicker">Depok, Indonesia &nbsp;·&nbsp; Backend &amp; Full-Stack</div>
      <div>
        <h1>Sutan Arlie Johan</h1>
        <div class="rule"></div>
        <p class="lead">Turning operational bottlenecks and scattered data into clear backend systems and web products.</p>
      </div>
      <div class="stack"><strong>CORE</strong> &nbsp; Laravel &middot; TypeScript &middot; REST API &middot; MySQL &middot; Next.js &middot; Supabase</div>
    </div>
    <svg class="ov" viewBox="0 0 1184 376" xmlns="http://www.w3.org/2000/svg">
      <defs><filter id="gr"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/></filter></defs>
      <rect x="0" y="0" width="618" height="376" filter="url(#gr)" opacity="{theme["grain_opacity"]}"/>
      <!-- Continuous 1px specular machined top rim spanning both typography & 3D stage -->
      <line x1="12" y1="0.8" x2="1172" y2="0.8" stroke="{theme["rim_top"]}" stroke-width="1.2"/>
      <g stroke="{theme["tick"]}" stroke-width="1.15" opacity="0.62" fill="none">
        <path d="M16,28 L16,16 L28,16"/><path d="M1156,16 L1168,16 L1168,28"/>
        <path d="M16,348 L16,360 L28,360"/><path d="M1156,360 L1168,360 L1168,348"/>
      </g>
      <line x1="628" y1="36" x2="628" y2="340" stroke="{theme["inner_border"]}" stroke-width="1" stroke-dasharray="3 5"/>
    </svg>
  </div></div>
<script>{_gl_script(HERO_FRAG_SHADER, cfg)}</script>
</body></html>"""


def build_maus_html(theme: dict) -> str:
    cfg = {
        "bg": list(theme["warm_rgb"]),
        "slab": list(theme["slab_rgb"]),
        "accent": list(theme["accent_rgb"]),
        "brass": list(theme["brass_rgb"]),
        "isLight": theme["is_light"],
    }
    return f"""<!doctype html>
<html><head><meta charset="utf-8" /><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {MAUS_W}px; height: {MAUS_H}px; overflow: hidden; background: {theme["shell"]}; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; -webkit-font-smoothing: antialiased; }}
  .outer {{ width: {MAUS_W}px; height: {MAUS_H}px; padding: 7px; background: {theme["shell"]}; border: 1.5px solid {theme["shell_border"]}; border-radius: 16px; }}
  .inner {{ position: relative; width: 100%; height: 100%; background: {theme["surface_warm"]}; border: 1px solid {theme["inner_border"]}; border-radius: 10px; overflow: hidden; }}
  #gl {{ position: absolute; right: 0; top: 0; width: 472px; height: 268px; display: block; }}
  .content {{ position: relative; z-index: 2; width: 696px; height: 100%; padding: 30px 0 28px 44px; display: flex; flex-direction: column; justify-content: space-between; }}
  .status-row {{ display: flex; align-items: center; gap: 14px; }}
  .live-tag {{ font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace; font-size: 11.5px; font-weight: 700; color: {theme["live"]}; background: {theme["live_bg"]}; border: 1px solid {theme["live"]}; border-radius: 6px; padding: 4px 12px; }}
  .domain {{ font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace; font-size: 13px; color: {theme["text_muted"]}; }}
  h2 {{ font-size: 38px; font-weight: 700; letter-spacing: -0.8px; line-height: 1.08; color: {theme["text_primary"]}; }}
  .rule {{ width: 46px; height: 3px; background: {theme["accent"]}; margin: 12px 0 14px 0; }}
  .desc {{ font-size: 16.5px; line-height: 1.46; color: {theme["text_secondary"]}; max-width: 590px; }}
  .tags {{ display: flex; gap: 10px; }}
  .tag {{ font-family: 'Cascadia Mono', Consolas, ui-monospace, monospace; font-size: 12px; color: {theme["text_primary"]}; background: {theme["raised"]}; border: 1px solid {theme["inner_border"]}; border-radius: 6px; padding: 5px 12px; }}
  .ov {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 3; }}
</style></head><body>
  <div class="outer"><div class="inner">
    <canvas id="gl" width="472" height="268"></canvas>
    <div class="content">
      <div class="status-row">
        <span class="live-tag">LIVE PRODUCTION</span>
        <span class="domain">maukitchen.my.id</span>
      </div>
      <div>
        <h2>Mau's Kitchen</h2>
        <div class="rule"></div>
        <p class="desc">Customer menu discovery, structured ordering, and daily kitchen admin operations running in production for an active food business.</p>
      </div>
      <div class="tags">
        <span class="tag">TypeScript</span>
        <span class="tag">Operations UI</span>
        <span class="tag">Order Flow</span>
      </div>
    </div>
    <svg class="ov" viewBox="0 0 1184 268" xmlns="http://www.w3.org/2000/svg">
      <defs><filter id="gr"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/></filter></defs>
      <rect x="0" y="0" width="700" height="268" filter="url(#gr)" opacity="{theme["grain_opacity"]}"/>
      <line x1="12" y1="0.8" x2="1172" y2="0.8" stroke="{theme["rim_top"]}" stroke-width="1.2"/>
      <line x1="708" y1="26" x2="708" y2="242" stroke="{theme["inner_border"]}" stroke-width="1" stroke-dasharray="3 5"/>
      <g text-anchor="middle" font-family="Cascadia Mono, Consolas, ui-monospace, monospace" font-size="11.5" font-weight="600" fill="{theme["text_secondary"]}">
        <text x="822" y="246">MENU</text>
        <text x="948" y="246">QUEUE</text>
        <text x="1074" y="246">SERVED</text>
      </g>
    </svg>
  </div></div>
<script>{_gl_script(MAUS_FRAG_SHADER, cfg)}</script>
</body></html>"""


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _encode_rgb_idat(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    raw = buf.getvalue()
    pos = 8
    parts: list[bytes] = []
    while pos < len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        cdata = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IDAT":
            parts.append(cdata)
    return b"".join(parts)


def save_delta_apng(frames: list[Image.Image], out_path: Path, duration_ms: int) -> None:
    """Write 24-bit APNG storing only the changed 3D stage rect for frames 1..N-1."""
    base = frames[0].convert("RGB")
    w, h = base.size
    x0, y0, x1, y1 = w, h, 0, 0
    for f in frames[1:]:
        bbox = ImageChops.difference(base, f.convert("RGB")).getbbox()
        if bbox:
            x0, y0 = min(x0, bbox[0]), min(y0, bbox[1])
            x1, y1 = max(x1, bbox[2]), max(y1, bbox[3])
    if x1 <= x0 or y1 <= y0:
        x0, y0, x1, y1 = 0, 0, w, h

    dw, dh = x1 - x0, y1 - y0
    chunks: list[bytes] = [
        b"\x89PNG\r\n\x1a\n",
        _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)),
        _png_chunk(b"acTL", struct.pack(">II", len(frames), 0)),
    ]
    seq = 0
    chunks.append(_png_chunk(b"fcTL", struct.pack(">IIIIIHHBB", seq, w, h, 0, 0, duration_ms, 1000, 0, 0)))
    seq += 1
    chunks.append(_png_chunk(b"IDAT", _encode_rgb_idat(base)))

    for f in frames[1:]:
        crop = f.convert("RGB").crop((x0, y0, x1, y1))
        chunks.append(_png_chunk(b"fcTL", struct.pack(">IIIIIHHBB", seq, dw, dh, x0, y0, duration_ms, 1000, 0, 0)))
        seq += 1
        chunks.append(_png_chunk(b"fdAT", struct.pack(">I", seq) + _encode_rgb_idat(crop)))
        seq += 1

    chunks.append(_png_chunk(b"IEND", b""))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"".join(chunks))
    print(f"Wrote {out_path.name}: {len(frames)}f, box=({x0},{y0},{x1},{y1}) [{dw}x{dh}], {out_path.stat().st_size/1024:.1f} KB", flush=True)


def render_scene(browser, html_str: str, w: int, h: int, clip: dict, frame_count: int, ms: int, out: Path, tag: str) -> None:
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
    page.set_content(html_str, wait_until="load")
    frames: list[Image.Image] = []
    page.evaluate("window.renderFrame(0.0)")
    base_img = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
    frames.append(base_img)
    for i in range(1, frame_count):
        page.evaluate(f"window.renderFrame({i / frame_count:.8f})")
        patch = Image.open(io.BytesIO(page.screenshot(type="png", clip=clip))).convert("RGB")
        full = base_img.copy()
        full.paste(patch, (clip["x"], clip["y"]))
        frames.append(full)
        if (i + 1) % 12 == 0:
            print(f"  [{tag}] {i + 1}/{frame_count} frames", flush=True)
    page.close()
    save_delta_apng(frames, out, ms)


def render_all(only: str = "") -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        for mode, theme in THEMES.items():
            if only in ("", "hero"):
                render_scene(
                    browser,
                    build_hero_html(theme),
                    HERO_W, HERO_H,
                    {"x": 640, "y": 8, "width": 552, "height": 376},
                    HERO_FRAMES, HERO_MS,
                    ASSETS / f"hero-{mode}.png",
                    f"hero-{mode}",
                )
            if only in ("", "maus"):
                render_scene(
                    browser,
                    build_maus_html(theme),
                    MAUS_W, MAUS_H,
                    {"x": 720, "y": 8, "width": 472, "height": 268},
                    MAUS_FRAMES, MAUS_MS,
                    ASSETS / f"project-maus-kitchen-{mode}.png",
                    f"maus-{mode}",
                )
        browser.close()


if __name__ == "__main__":
    import sys
    render_all(sys.argv[1] if len(sys.argv) > 1 else "")
