#!/usr/bin/env python3
"""Generate the self-hosted animated banner used by the profile README."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 360
FRAME_COUNT = 36
FRAME_DURATION_MS = 85
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "hero.gif"

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


LABEL = font(FONT_MONO_BOLD, 18)
TITLE = font(FONT_BOLD, 56)
SUBTITLE = font(FONT_REGULAR, 25)
MONO = font(FONT_MONO, 17)
MONO_BOLD = font(FONT_MONO_BOLD, 17)
SMALL = font(FONT_MONO, 14)


def ease(value: float) -> float:
    return (1.0 - math.cos(value * math.pi)) / 2.0


def background() -> Image.Image:
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    base = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
    base[:] = (5, 8, 17)

    lights = [
        (
            300,
            75,
            270,
            np.array([48, 65, 210], dtype=np.float32),
            0.82,
        ),
        (
            1050,
            250,
            250,
            np.array([5, 178, 214], dtype=np.float32),
            0.70,
        ),
        (
            700,
            380,
            300,
            np.array([118, 51, 205], dtype=np.float32),
            0.52,
        ),
    ]

    for cx, cy, radius, color, strength in lights:
        distance = ((xx - cx) ** 2 + (yy - cy) ** 2) / (2.0 * radius**2)
        glow = np.exp(-distance)[..., None] * strength
        base += glow * color

    vignette_x = np.abs((xx - WIDTH / 2) / (WIDTH / 2))
    vignette_y = np.abs((yy - HEIGHT / 2) / (HEIGHT / 2))
    vignette = np.clip((vignette_x**2 + vignette_y**2) * 0.25, 0, 0.42)
    base *= (1.0 - vignette[..., None])
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


def draw_grid(draw: ImageDraw.ImageDraw) -> None:
    for x in range(0, WIDTH + 40, 40):
        draw.line((x, 0, x, HEIGHT), fill=(104, 142, 190, 22), width=1)
    for y in range(0, HEIGHT, 40):
        draw.line((0, y, WIDTH, y), fill=(104, 142, 190, 18), width=1)


def draw_orbit(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    phase = frame_index / FRAME_COUNT
    center = (1018, 181)
    rings = [(152, 104), (112, 74), (70, 44)]
    for width, height in rings:
        box = (
            center[0] - width,
            center[1] - height,
            center[0] + width,
            center[1] + height,
        )
        draw.ellipse(box, outline=(105, 164, 255, 45), width=1)

    nodes = [
        (148, 104, 0.00, (34, 211, 238)),
        (110, 74, 0.34, (129, 140, 248)),
        (70, 44, 0.67, (192, 132, 252)),
    ]
    points: list[tuple[float, float]] = []
    for rx, ry, start, color in nodes:
        angle = (phase + start) * math.tau
        px = center[0] + rx * math.cos(angle)
        py = center[1] + ry * math.sin(angle)
        pulse = 4 + int(2 * ease((math.sin(angle) + 1) / 2))
        draw.ellipse((px - pulse, py - pulse, px + pulse, py + pulse), fill=color)
        draw.ellipse((px - 11, py - 11, px + 11, py + 11), outline=(*color, 65), width=1)
        points.append((px, py))

    for first, second in zip(points, points[1:]):
        draw.line((*first, *second), fill=(99, 210, 255, 58), width=1)

    glow = 8 + int(2 * math.sin(phase * math.tau))
    draw.ellipse(
        (
            center[0] - glow,
            center[1] - glow,
            center[0] + glow,
            center[1] + glow,
        ),
        fill=(240, 249, 255),
    )
    draw.text((center[0] - 61, 309), "SYSTEMS / WEB", font=SMALL, fill=(177, 211, 235))


def draw_copy(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    phase = frame_index / FRAME_COUNT
    draw.rounded_rectangle((66, 48, 320, 82), radius=17, fill=(8, 17, 34, 190), outline=(76, 177, 255, 90))
    dot = 4 + int((math.sin(phase * math.tau) + 1) * 1.3)
    draw.ellipse((82 - dot, 65 - dot, 82 + dot, 65 + dot), fill=(34, 211, 238))
    draw.text((99, 54), "SUTAN.DEV / DEPOK, ID", font=LABEL, fill=(203, 236, 255))

    draw.text((66, 112), "SUTAN ARLIE JOHAN", font=TITLE, fill=(247, 250, 255))
    draw.text((69, 184), "Backend-focused full-stack developer", font=SUBTITLE, fill=(192, 219, 238))
    draw.text((69, 222), "Building useful systems from rough ideas.", font=SUBTITLE, fill=(160, 186, 210))

    draw.rounded_rectangle((68, 280, 750, 322), radius=10, fill=(7, 15, 29, 175), outline=(88, 151, 218, 70))
    draw.text((89, 292), "LARAVEL  /  TYPESCRIPT  /  REST API  /  PRODUCT UI", font=MONO_BOLD, fill=(172, 229, 248))

    scan_x = int(66 + (phase * 2 % 1) * 710)
    draw.line((scan_x, 329, min(scan_x + 72, 780), 329), fill=(34, 211, 238), width=2)


def make_frames() -> list[Image.Image]:
    frames: list[Image.Image] = []
    base = background().convert("RGBA")
    for frame_index in range(FRAME_COUNT):
        image = base.copy()
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        draw_grid(draw)
        draw_copy(draw, frame_index)
        draw_orbit(draw, frame_index)
        draw.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), outline=(105, 183, 236, 60), width=1)
        frames.append(Image.alpha_composite(image, overlay).convert("RGB"))
    return frames


def save_gif(frames: list[Image.Image]) -> None:
    # One shared palette keeps the gradient stable instead of flickering per frame.
    palette = frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG) for frame in frames]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        OUTPUT,
        save_all=True,
        append_images=indexed[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=1,
    )
    print(f"Generated {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB)")


if __name__ == "__main__":
    save_gif(make_frames())
