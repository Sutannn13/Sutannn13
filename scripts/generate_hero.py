#!/usr/bin/env python3
"""Generate the self-hosted Neon Observatory hero animation."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1200, 420
FRAME_COUNT, FRAME_DURATION_MS = 44, 85
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "hero.gif"

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


EYEBROW = load_font(FONT_MONO_BOLD, 15)
TITLE = load_font(FONT_BOLD, 51)
SUBTITLE = load_font(FONT_REGULAR, 23)
MONO = load_font(FONT_MONO, 16)
MONO_BOLD = load_font(FONT_MONO_BOLD, 16)
SMALL = load_font(FONT_MONO, 13)


def background() -> Image.Image:
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float32)
    canvas[:] = (4, 8, 18)
    lights = [
        (230, 80, 300, (41, 73, 210), 0.76),
        (1045, 190, 265, (0, 182, 205), 0.58),
        (690, 440, 330, (113, 48, 194), 0.46),
    ]
    for cx, cy, radius, rgb, strength in lights:
        falloff = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius**2))[..., None]
        canvas += falloff * np.array(rgb, dtype=np.float32) * strength
    edge = np.clip(((xx - WIDTH / 2) / (WIDTH / 2)) ** 2 + ((yy - HEIGHT / 2) / (HEIGHT / 2)) ** 2, 0, 1)
    canvas *= (1 - edge[..., None] * 0.28)
    return Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGB")


def draw_grid(draw: ImageDraw.ImageDraw) -> None:
    for x in range(0, WIDTH + 40, 40):
        draw.line((x, 0, x, HEIGHT), fill=(86, 139, 190, 20), width=1)
    for y in range(0, HEIGHT + 40, 40):
        draw.line((0, y, WIDTH, y), fill=(86, 139, 190, 17), width=1)


def draw_header(draw: ImageDraw.ImageDraw, frame: int) -> None:
    phase = frame / FRAME_COUNT
    draw.rounded_rectangle((64, 43, 407, 75), radius=16, fill=(5, 15, 31, 205), outline=(70, 180, 230, 95))
    pulse = 4 + int((math.sin(phase * math.tau) + 1) * 1.2)
    draw.ellipse((81 - pulse, 59 - pulse, 81 + pulse, 59 + pulse), fill=(34, 211, 238))
    draw.text((98, 49), "SUTAN // DEVELOPER OBSERVATORY", font=EYEBROW, fill=(196, 237, 253))

    draw.text((64, 105), "SUTAN ARLIE JOHAN", font=TITLE, fill=(247, 250, 255))
    draw.text((67, 174), "Backend systems / Full-stack products / Automation", font=SUBTITLE, fill=(190, 219, 239))
    draw.text((67, 211), "Observe the problem. Design the flow. Ship the system.", font=SUBTITLE, fill=(146, 177, 206))

    draw.rounded_rectangle((66, 274, 713, 329), radius=12, fill=(4, 13, 29, 205), outline=(70, 138, 198, 75))
    commands = ["observe.problem()", "design.system()", "ship.product()"]
    active = int(phase * len(commands)) % len(commands)
    typed = int((phase * len(commands) % 1) * (len(commands[active]) + 4))
    visible = commands[active][: min(typed, len(commands[active]))]
    cursor = "_" if frame % 8 < 5 else " "
    draw.text((87, 286), ">", font=MONO_BOLD, fill=(34, 211, 238))
    draw.text((112, 286), visible + cursor, font=MONO_BOLD, fill=(222, 237, 248))
    draw.text((538, 288), "STATUS: BUILDING", font=SMALL, fill=(167, 139, 250))

    labels = ["LARAVEL", "TYPESCRIPT", "REST API", "PRODUCT UI"]
    x = 67
    for label in labels:
        width = draw.textlength(label, font=SMALL) + 26
        draw.rounded_rectangle((x, 356, x + width, 386), radius=8, fill=(7, 21, 39, 190), outline=(57, 128, 181, 75))
        draw.text((x + 13, 363), label, font=SMALL, fill=(172, 225, 243))
        x += width + 10


def draw_radar(draw: ImageDraw.ImageDraw, frame: int) -> None:
    phase = frame / FRAME_COUNT
    cx, cy = 1005, 204
    radii = (132, 96, 58)
    for radius in radii:
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(92, 164, 211, 48), width=1)
    draw.line((cx - 145, cy, cx + 145, cy), fill=(91, 159, 205, 40), width=1)
    draw.line((cx, cy - 145, cx, cy + 145), fill=(91, 159, 205, 40), width=1)

    sweep = phase * math.tau
    sx, sy = cx + 138 * math.cos(sweep), cy + 138 * math.sin(sweep)
    draw.line((cx, cy, sx, sy), fill=(34, 211, 238, 150), width=2)
    for offset in range(1, 7):
        angle = sweep - offset * 0.035
        ex, ey = cx + 134 * math.cos(angle), cy + 134 * math.sin(angle)
        draw.line((cx, cy, ex, ey), fill=(34, 211, 238, max(10, 65 - offset * 8)), width=1)

    nodes = [
        (116, 0.08, (34, 211, 238)),
        (88, 0.42, (129, 140, 248)),
        (55, 0.71, (192, 132, 252)),
    ]
    for radius, start, color in nodes:
        angle = (phase * 0.62 + start) * math.tau
        x, y = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        dot = 4 + int((math.sin(angle * 2) + 1) * 1.2)
        draw.ellipse((x - 11, y - 11, x + 11, y + 11), outline=(*color, 65), width=1)
        draw.ellipse((x - dot, y - dot, x + dot, y + dot), fill=color)

    draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(242, 250, 255))
    draw.text((935, 368), "SIGNAL / STABLE", font=SMALL, fill=(174, 214, 237))


def make_frames() -> list[Image.Image]:
    base = background().convert("RGBA")
    frames: list[Image.Image] = []
    for frame in range(FRAME_COUNT):
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        draw_grid(draw)
        draw_header(draw, frame)
        draw_radar(draw, frame)
        scan_x = int((frame / FRAME_COUNT) * (WIDTH + 180)) - 180
        draw.rectangle((scan_x, HEIGHT - 4, scan_x + 180, HEIGHT - 2), fill=(34, 211, 238, 205))
        draw.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), outline=(85, 165, 215, 60), width=1)
        frames.append(Image.alpha_composite(base, overlay).convert("RGB"))
    return frames


def save_gif(frames: list[Image.Image]) -> None:
    palette = frames[0].quantize(colors=144, method=Image.Quantize.MEDIANCUT)
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
