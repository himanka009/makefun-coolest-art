"""The Last Lighthouse — render a deterministic RGB PNG."""
import math
import os
from pathlib import Path
import random
import struct
import zlib

SIZE = 768
CENTER_X, CENTER_Y = 383, 291
HORIZON = 532
TAU = math.tau


def noise(x, y):
    seed = ((x * 374761393) ^ (y * 668265263)) & 0xFFFFFFFF
    seed = ((seed ^ (seed >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((seed ^ (seed >> 16)) & 255) / 255 - 0.5


def sky(x, y):
    dx, dy = x - CENTER_X, y - CENTER_Y
    radius = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)
    horizon = math.exp(-abs(y - HORIZON) / 88)
    glow = math.exp(-abs(radius - 146) / 32)
    filament = 0.55 + 0.21 * math.sin(angle * 19 + radius * .037)
    filament += 0.16 * math.sin(angle * 47 - radius * .051)
    plume = max(0, math.cos(angle - 3.85)) ** 18
    plume *= math.exp(-abs(radius - 151) / 67)
    rim = math.exp(-((radius - 144) / 3.7) ** 2)
    daybreak = math.exp(-((dx + 122) / 310) ** 2) * horizon
    if radius < 142:
        eclipse = max(0, 1 - (142 - radius) / 45)
        haze = eclipse * (.5 + .5 * math.cos(angle + 1.8)) ** 3
        return 8 + 45 * haze, 8 + 16 * haze, 20 + 29 * haze
    return (
        14 + 52 * daybreak + 170 * glow * filament + 155 * rim + 81 * plume,
        11 + 28 * daybreak + 55 * glow * filament + 101 * rim + 38 * plume,
        34 + 31 * daybreak + 65 * glow * filament + 56 * rim + 18 * plume,
    )


def ocean(x, y):
    depth = y - HORIZON
    dx = x - CENTER_X
    ridge = math.sin(y * .86 + math.sin(x * .022) * 2.8)
    ridge += .56 * math.sin(y * 1.57 + x * .018)
    ripples = max(0, ridge - .72)
    width = 47 + depth * .38
    shift = 15 * math.sin(y * .143) + 8 * math.sin(y * .61)
    reflection = math.exp(-((dx + shift) / width) ** 2)
    falloff = math.exp(-depth / 240)
    light = ripples * reflection * falloff
    turquoise = ripples * (1 - reflection * .75) * falloff
    return (
        8 + 43 * reflection * falloff + 172 * light,
        14 + 17 * reflection * falloff + 77 * light + 35 * turquoise,
        31 + 16 * reflection * falloff + 43 * light + 48 * turquoise,
    )


def silhouette(x, y):
    # A split basalt needle and the lamp suspended above it.
    if 335 <= y < 555:
        height = (y - 335) / 220
        middle = 391 - 14 * height + 3 * math.sin(height * 11)
        half_width = 3 + 36 * height ** 2 + 3 * math.sin(height * 28)
        side = (x - middle) / half_width
        if abs(side) < 1:
            seam = abs(side + .25 + .18 * math.sin(y * .08))
            strata = max(0, math.sin(y * .27 + x * .64)) * 6
            edge = 19 * max(0, -side) ** 5
            crack = 16 * max(0, 1 - seam * 24)
            return 8 + edge + strata + crack, 9 + strata + crack / 3, 19 + edge / 2
    if 539 <= y < 576:
        width = 54 * (1 - ((y - 554) / 23) ** 2)
        if abs(x - 378) < width + 4 * math.sin(x * .29):
            return 6, 10, 21
    return None


def stars():
    randomizer = random.Random(284)
    field = {}
    for _ in range(1650):
        x = randomizer.randrange(16, SIZE - 16)
        y = randomizer.randrange(12, HORIZON - 22)
        if math.hypot(x - CENTER_X, y - CENTER_Y) < 153:
            continue
        power = 18 + 132 * randomizer.random() ** 5
        field[x, y] = power
        if power > 120:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                field[x + dx, y + dy] = power * .23
    return field


def pixel(x, y, star):
    if y < HORIZON:
        red, green, blue = sky(x, y)
    else:
        red, green, blue = ocean(x, y)
    rock = silhouette(x, y)
    if rock:
        red, green, blue = rock
    else:
        red += star
        green += star * .88
        blue += star * .81

    # A warm point of light throws a thin beam across the dark disc.
    lamp_x, lamp_y = 390, 326
    dx, dy = x - lamp_x, y - lamp_y
    light = math.exp(-math.hypot(dx, dy) / 4.3)
    beam_width = .85 + max(0, dx) * .026
    beam_axis = abs(dy + dx * .18)
    beam = math.exp(-(beam_axis / beam_width) ** 1.5)
    beam *= math.exp(-abs(dx) / 137) * (.08 if dx < 0 else 1)
    flare = 270 * light + 108 * beam
    vignette = 1 - .29 * (((x - 384) / 520) ** 2 + ((y - 345) / 550) ** 2)
    grain = 8 * noise(x, y)
    return bytes(
        min(255, max(0, round(value * vignette + grain)))
        for value in (red + flare, green + .69 * flare, blue + .43 * flare)
    )


def chunk(tag, data):
    checksum = zlib.crc32(tag + data)
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", checksum)


def render():
    field = stars()
    rows = bytearray()
    for y in range(SIZE):
        rows.append(1)
        previous = b"\x00\x00\x00"
        for x in range(SIZE):
            current = pixel(x, y, field.get((x, y), 0))
            rows.extend((value - prior) & 255 for value, prior in zip(current, previous))
            previous = current
    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    output = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "entry.png").write_bytes(render())
