#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE -- a newspaper front page for Saturday 21 November 2026.

Draws a 1024x1024 PNG with pure Python (standard library only): its own
bitmap font, its own drawing helpers and its own PNG encoder. No network,
no clock, no randomness -- the same input always produces the same bytes.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes out/entry.png (or /output/entry.png when the variable is unset).
"""

import math
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

# ---------------------------------------------------------------- palette ---
PAPER = (247, 243, 232)   # newsprint off-white
INK = (24, 24, 24)       # body ink
RED = (158, 32, 32)      # kicker red
BLUE = (28, 58, 128)     # EU flag blue
GOLD = (216, 178, 60)    # stars / lit windows
SKY = (16, 22, 44)       # night sky over the lead illustration
BLDG = (9, 11, 24)       # building silhouettes
WINDOW_LIT = (255, 196, 90)
WINDOW_DARK = (32, 36, 56)
MOON = (236, 229, 192)
TRAIL = (255, 170, 80)
BURST = (255, 122, 40)
SMOKE = (96, 98, 112)
GREY = (120, 116, 104)   # thin rules inside the page

# ------------------------------------------------------------- bitmap font --
# A 5x7 pixel font. Each glyph is seven rows of five characters; '#' is a
# filled pixel, '.' is empty. Drawn by hand for this program.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##...", "#.#..", "...#.", "..#..", ".#...", "..#.#", "..##."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "EURO": ("..###", ".#...", "#....", "####.", "#....", ".#...", "..###"),
}

# The euro sign is stored under the key "EURO" because the glyph table is
# indexed by plain ASCII; the text helper maps the character "\u20ac" to it.
FONT["\u20ac"] = FONT["EURO"]


def text_width(text, scale):
    """Pixel width of `text` drawn at the given scale."""
    return len(text) * 6 * scale - scale


def wrap_text(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if len(trial) <= max_chars:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# ------------------------------------------------------------------ canvas --
class Canvas:
    """An RGB image held as one flat bytearray, with small drawing tools."""

    def __init__(self, width, height, background):
        self.w = width
        self.h = height
        self.px = bytearray(bytes(background) * (width * height))

    def _offset(self, x, y):
        return (y * self.w + x) * 3

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._offset(x, y)
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._offset(x0, yy)
            self.px[i:i + len(row)] = row

    def hline(self, x, y, length, color, thick=1):
        self.fill_rect(x, y, length, thick, color)

    def vline(self, x, y, length, color, thick=1):
        self.fill_rect(x, y, thick, length, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.fill_rect(x, y, w, thick, color)
        self.fill_rect(x, y + h - thick, w, thick, color)
        self.fill_rect(x, y, thick, h, color)
        self.fill_rect(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line; thick lines are drawn as small filled squares."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, filled=True):
        """Filled disc, or a 1px outline when filled is False."""
        if filled:
            for dy in range(-r, r + 1):
                half = int(math.sqrt(max(0, r * r - dy * dy)))
                self.hline(cx - half, cy + dy, 2 * half + 1, color)
        else:
            steps = max(24, r * 6)
            for k in range(steps):
                a = 2.0 * math.pi * k / steps
                self.set_px(cx + int(round(r * math.cos(a))),
                           cy + int(round(r * math.sin(a))), color)

    def triangle(self, p0, p1, p2, color):
        """Filled triangle, scanline by scanline."""
        xs = sorted([p0[0], p1[0], p2[0]])
        ys = sorted([p0[1], p1[1], p2[1]])
        for yy in range(ys[0], ys[2] + 1):
            edges = []
            for a, b in ((p0, p1), (p1, p2), (p2, p0)):
                if a[1] == b[1]:
                    continue
                lo, hi = (a, b) if a[1] < b[1] else (b, a)
                if lo[1] <= yy <= hi[1]:
                    t = (yy - lo[1]) / float(hi[1] - lo[1])
                    edges.append(int(round(lo[0] + t * (hi[0] - lo[0]))))
            if len(edges) >= 2:
                self.hline(min(edges), yy, max(edges) - min(edges) + 1, color)

    def polyline(self, points, color, thick=1):
        for a, b in zip(points, points[1:]):
            self.line(a[0], a[1], b[0], b[1], color, thick)

    # ------------------------------------------------------------ text -----
    def text(self, x, y, s, scale, color):
        """Draw `s` with the bitmap font; returns the x of the next char."""
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, y, s, scale, color):
        x = (self.w - text_width(s, scale)) // 2
        self.text(x, y, s, scale, color)
        return x

    def paragraph(self, x, y, s, scale, color, max_chars, line_gap=4):
        """Wrapped paragraph; returns the y just below the last line."""
        yy = y
        for line in wrap_text(s, max_chars):
            self.text(x, yy, line, scale, color)
            yy += 7 * scale + line_gap
        return yy


# -------------------------------------------------------------- PNG output --
def encode_png(canvas):
    """Encode the canvas as a PNG (8-bit RGB, no filtering)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter type 0: none
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


# --------------------------------------------------------------- pictograms --
# Each pictogram is drawn inside a 64x64 box whose top-left corner is (x, y).

def pic_handcuffs(cv, x, y):
    """Two linked rings: the Sinaloa arrest."""
    cv.circle(x + 18, y + 36, 12, INK, filled=False)
    cv.circle(x + 18, y + 36, 10, INK, filled=False)
    cv.circle(x + 46, y + 36, 12, INK, filled=False)
    cv.circle(x + 46, y + 36, 10, INK, filled=False)
    # Short chain joining the rings.
    cv.hline(x + 28, y + 24, 9, INK, thick=3)
    cv.circle(x + 30, y + 25, 3, INK, filled=False)
    cv.circle(x + 35, y + 25, 3, INK, filled=False)
    # Shackle stubs above each ring.
    cv.vline(x + 18, y + 14, 11, INK, thick=3)
    cv.vline(x + 46, y + 14, 11, INK, thick=3)


def pic_globe_clock(cv, x, y):
    """A globe with a small clock: climate talks running over time."""
    cv.circle(x + 28, y + 28, 20, INK, filled=False)
    cv.circle(x + 28, y + 28, 19, INK, filled=False)
    cv.vline(x + 28, y + 9, 39, INK)
    cv.hline(x + 9, y + 28, 39, INK)
    cv.line(x + 15, y + 13, x + 41, y + 43, INK)
    cv.line(x + 41, y + 13, x + 15, y + 43, INK)
    # Clock tucked at the lower right.
    cv.circle(x + 48, y + 48, 11, PAPER, filled=True)
    cv.circle(x + 48, y + 48, 11, INK, filled=False)
    cv.line(x + 48, y + 48, x + 48, y + 40, INK, thick=2)
    cv.line(x + 48, y + 48, x + 54, y + 50, INK, thick=2)


def pic_falling_chart(cv, x, y):
    """Axes and a falling line with an arrowhead: the Nasdaq slide."""
    cv.vline(x + 8, y + 8, 48, INK, thick=2)
    cv.hline(x + 8, y + 54, 48, INK, thick=2)
    points = [(x + 12, y + 14), (x + 22, y + 24), (x + 32, y + 22),
              (x + 42, y + 38), (x + 52, y + 50)]
    cv.polyline(points, RED, thick=3)
    # Arrowhead at the end of the fall.
    cv.line(x + 52, y + 50, x + 44, y + 48, RED, thick=3)
    cv.line(x + 52, y + 50, x + 50, y + 42, RED, thick=3)


def pic_missile(cv, x, y):
    """A rocket climbing diagonally: Washington weighing strikes."""
    # Body along the diagonal.
    cv.line(x + 14, y + 50, x + 38, y + 22, INK, thick=6)
    # Nose cone.
    cv.triangle((x + 36, y + 24), (x + 50, y + 8), (x + 44, y + 28), INK)
    # Fins at the tail.
    cv.triangle((x + 14, y + 50), (x + 8, y + 58), (x + 20, y + 54), INK)
    cv.triangle((x + 14, y + 50), (x + 6, y + 44), (x + 18, y + 44), INK)
    # Flame.
    cv.triangle((x + 12, y + 52), (x + 4, y + 60), (x + 16, y + 58), BURST)
    cv.triangle((x + 12, y + 52), (x + 8, y + 62), (x + 14, y + 56), GOLD)


def pic_eu_flag(cv, x, y):
    """EU flag (blue field, ring of gold stars) with a euro sign."""
    cv.fill_rect(x + 4, y + 10, 56, 40, BLUE)
    cv.rect(x + 4, y + 10, 56, 40, INK)
    cx, cy = x + 32, y + 30
    for k in range(12):
        a = 2.0 * math.pi * k / 12.0 - math.pi / 2.0
        sx = cx + int(round(13 * math.cos(a)))
        sy = cy + int(round(13 * math.sin(a)))
        cv.fill_rect(sx - 1, sy - 1, 3, 3, GOLD)
    cv.text(x + 27, y + 23, "\u20ac", 2, GOLD)


# ------------------------------------------------------- lead illustration --
def draw_skyline(cv, x, y, w, h):
    """Dusk skyline over Kryvyi Rih: stars, moon, lit windows, missile
    trails arcing down to two impact bursts, and smoke rising."""
    cv.fill_rect(x, y, w, h, SKY)

    # Stars: fixed positions from a simple deterministic pattern.
    for i in range(42):
        sx = x + 8 + (i * 173) % (w - 16)
        sy = y + 5 + (i * 97) % (h // 2)
        if i % 3 == 0:
            cv.fill_rect(sx, sy, 2, 2, (255, 255, 240))
        else:
            cv.set_px(sx, sy, (220, 220, 235))

    # Moon, upper right.
    mx, my = x + w - 92, y + 26
    cv.circle(mx, my, 16, MOON, filled=True)
    cv.circle(mx - 5, my - 3, 3, (205, 198, 162), filled=True)
    cv.circle(mx + 4, my + 5, 2, (205, 198, 162), filled=True)

    # Buildings along the bottom, with lit and dark windows.
    bottom = y + h
    buildings = [
        (0, 70, 52), (66, 54, 78), (116, 80, 44), (192, 60, 88),
        (248, 72, 58), (316, 58, 96), (370, 84, 50), (450, 64, 80),
        (510, 76, 46), (582, 60, 92), (638, 88, 54), (722, 66, 84),
        (784, 72, 48), (852, 64, 76), (912, 64, 58),
    ]
    for bx, bw, bh in buildings:
        cv.fill_rect(x + bx, bottom - bh, bw, bh, BLDG)
        # Aerial on some rooftops.
        if (bx // 10) % 3 == 0:
            cv.vline(x + bx + bw // 2, bottom - bh - 12, 12, BLDG, thick=2)
        for wx in range(bx + 8, bx + bw - 8, 15):
            for wy in range(bottom - bh + 10, bottom - 10, 17):
                lit = (wx * 7 + wy * 13) % 5 < 2
                cv.fill_rect(x + wx, wy, 5, 7,
                             WINDOW_LIT if lit else WINDOW_DARK)

    # Two missile trails arcing down from the top of the sky.
    def trail(x_from, x_to, y_hit):
        pts = []
        for step in range(25):
            t = step / 24.0
            px = int(x_from + (x_to - x_from) * t)
            py = int(y + 4 + (y_hit - (y + 4)) * t * t)
            pts.append((px, py))
        cv.polyline(pts, TRAIL, thick=2)

    impact_a = (x + 330, bottom - 62)
    impact_b = (x + 700, bottom - 48)
    trail(x + 296, impact_a[0], impact_a[1])
    trail(x + 662, impact_b[0], impact_b[1])

    # Impact bursts: layered discs plus radiating sparks.
    for ix, iy in (impact_a, impact_b):
        cv.circle(ix, iy, 13, BURST, filled=True)
        cv.circle(ix, iy, 8, (255, 200, 80), filled=True)
        cv.circle(ix, iy, 4, (255, 240, 170), filled=True)
        for k in range(8):
            a = 2.0 * math.pi * k / 8.0
            cv.line(ix, iy,
                    ix + int(round(20 * math.cos(a))),
                    iy + int(round(20 * math.sin(a))), TRAIL, thick=2)

    # Smoke drifting above each impact.
    for ix, iy in (impact_a, impact_b):
        cv.circle(ix - 8, iy - 26, 9, SMOKE, filled=True)
        cv.circle(ix + 6, iy - 34, 12, SMOKE, filled=True)
        cv.circle(ix + 16, iy - 22, 8, SMOKE, filled=True)

    cv.fill_rect(x, bottom - 5, w, 5, (6, 8, 18))


# ------------------------------------------------------------------- page ---
MARGIN = 24
COL_W = 476
ROW_H = 136
ROW_GAP = 10


def draw_masthead(cv):
    cv.fill_rect(MARGIN, 26, WIDTH - 2 * MARGIN, 3, INK)
    cv.text_centered(38, "THE WORLD IN ONE PAGE", 6, INK)
    cv.text_centered(88, "SATURDAY 21 NOVEMBER 2026", 2, INK)
    cv.fill_rect(MARGIN, 112, WIDTH - 2 * MARGIN, 3, INK)


def draw_lead(cv):
    cv.text(MARGIN, 128, "LEAD STORY - UKRAINE", 2, RED)
    cv.text(MARGIN, 150, "DOUBLE-TAP STRIKE ON KRYVYI RIH", 4, INK)
    cv.text(MARGIN, 184, "KILLS BOY, 7, AND WOMAN, 20", 4, INK)
    summary = (
        "A ballistic double-tap strike on Kryvyi Rih, President Zelenskyy's "
        "hometown, killed a seven-year-old boy and a 20-year-old woman and "
        "wounded 60 people, six of them children. The second missile hit as "
        "rescuers were still working at the scene."
    )
    cv.paragraph(MARGIN, 224, summary, 2, INK, 81, line_gap=4)
    draw_skyline(cv, MARGIN, 296, WIDTH - 2 * MARGIN, 132)
    cv.fill_rect(MARGIN, 442, WIDTH - 2 * MARGIN, 2, INK)


def draw_story(cv, x, y, kicker, headline, summary, pictogram):
    """One story block: pictogram at left, kicker + headline beside it,
    summary underneath across the full block width."""
    cv.rect(x, y, 64, 64, GREY)
    pictogram(cv, x, y)
    cv.text(x + 74, y + 2, kicker, 1, RED)
    yy = y + 16
    for line in wrap_text(headline, 33):
        cv.text(x + 74, yy, line, 2, INK)
        yy += 7 * 2 + 4
    cv.paragraph(x, y + 74, summary, 1, INK, 79, line_gap=3)


def draw_by_numbers(cv, x, y):
    cv.rect(x, y, COL_W, ROW_H, INK, thick=2)
    cv.text(x + 12, y + 10, "BY THE NUMBERS", 2, RED)
    rows = [
        ("60", "WOUNDED IN KRYVYI RIH"),
        ("11", "KILLED IN SINALOA"),
        ("5.28%", "NASDAQ'S FRIDAY FALL"),
    ]
    yy = y + 36
    for number, label in rows:
        cv.text(x + 12, yy, number, 3, INK)
        cv.text(x + 116, yy + 4, label, 2, INK)
        yy += 32


def draw_in_brief(cv, y):
    cv.text(MARGIN, y, "IN BRIEF", 2, RED)
    cv.fill_rect(MARGIN, y + 20, WIDTH - 2 * MARGIN, 1, GREY)
    briefs = [
        ("NIGERIA", "A boat capsizes on the way to a funeral, killing 24 people."),
        ("PERU", "A magnitude 6.7 earthquake strikes the Junin region."),
        ("SOUTH AFRICA", "Phumzile Mlambo-Ngcuka, ex-deputy president, dies at 71."),
    ]
    col_x = [MARGIN, 352, 680]
    for (place, text), bx in zip(briefs, col_x):
        cv.text(bx, y + 30, place, 1, RED)
        cv.paragraph(bx, y + 42, text, 1, INK, 53, line_gap=3)


def draw_footer(cv):
    cv.fill_rect(MARGIN, 970, WIDTH - 2 * MARGIN, 2, INK)
    cv.text_centered(982, "THE WORLD IN ONE PAGE - SATURDAY 21 NOVEMBER 2026",
                     1, INK)


def build_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)

    draw_masthead(cv)
    draw_lead(cv)

    stories = [
        ("MEXICO", "TOP FUGITIVE 'EL CHAPO ISIDRO' SEIZED IN SINALOA",
         "FBI Top 10 fugitive Fausto Isidro Meza Flores was seized in Guasave "
         "with US help. Eleven people died in the fighting.", pic_handcuffs),
        ("CLIMATE - COP31", "COP31 TALKS DRAG INTO OVERTIME WITH NO DEAL",
         "Negotiators in Antalya missed their deadline as the talks ran into "
         "overtime. The draft text is still silent on fossil fuels.",
         pic_globe_clock),
        ("MARKETS", "NASDAQ SINKS 5.28% AND ERASES 2026 GAINS",
         "Stocks fell sharply on Friday, wiping out the Nasdaq's gains for "
         "the year. Nvidia dropped 14 percent in a single session.",
         pic_falling_chart),
        ("WASHINGTON", "TRUMP WEIGHS NEW STRIKES ON IRAN",
         "President Trump is considering fresh strikes on Iran as Israel "
         "presses him to move quickly.", pic_missile),
        ("EUROPE", "EU APPROVES 1 BILLION EUROS FOR UKRAINE",
         "The European Union approved 1 billion euros of military support "
         "for Ukraine as Moscow rejected a peace deal.", pic_eu_flag),
    ]

    y = 456
    draw_story(cv, MARGIN, y, *stories[0])
    draw_story(cv, MARGIN + COL_W + 24, y, *stories[1])
    y += ROW_H + ROW_GAP
    draw_story(cv, MARGIN, y, *stories[2])
    draw_story(cv, MARGIN + COL_W + 24, y, *stories[3])
    y += ROW_H + ROW_GAP
    draw_story(cv, MARGIN, y, *stories[4])
    draw_by_numbers(cv, MARGIN + COL_W + 24, y)

    draw_in_brief(cv, 896)
    draw_footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(build_page())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()
