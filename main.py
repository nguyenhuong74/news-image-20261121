#!/usr/bin/env python3
"""The World in One Page -- Saturday 21 November 2026.

Draws a newspaper front page summing up the day's world news as one
1024x1024 PNG, using only the Python standard library.

Everything is drawn in code: a hand-built 5x7 bitmap font for all text,
small geometric pictograms for each story, a dusk city scene for the lead
story, and a PNG encoder built from zlib + struct. No network, no clock,
no randomness, no dependence on dict order -- every run writes a
byte-identical file.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes out/entry.png (or /output/entry.png when the variable is unset).
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# Palette -------------------------------------------------------------------
PAPER = (247, 243, 232)   # newsprint
INK = (24, 24, 24)        # body ink
RED = (164, 30, 30)       # accent red
BLUE = (30, 58, 110)      # deep blue
DUSK = (40, 46, 70)       # evening sky in the lead picture
DUSK2 = (58, 52, 74)      # lower evening sky
GOLD = (214, 164, 32)     # lit windows, flag stars
GREY = (128, 122, 110)    # smoke, muted rules
EMBER = (232, 122, 32)    # missile glow
FLAME = (245, 196, 66)    # explosion core
CLOUD = (232, 226, 210)   # light panel fill
MOON = (228, 226, 205)    # pale moon

# 5x7 bitmap font ------------------------------------------------------------
# One glyph per character: seven rows of five cells, '1' means ink.
# Lowercase letters use rows 2-6 (x-height); ascenders reach row 0.
GLYPHS = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "00000", "01110", "10001", "10001", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00100", "00000", "00100", "00100", "00100", "10100", "01000"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    'q': ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("00100", "00100", "11110", "00100", "00100", "00100", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '\u2014': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '\u00d7': ("00000", "10001", "01010", "00100", "01010", "10001", "00000"),
    '\u00b7': ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '\u20ac': ("00111", "01000", "11110", "01000", "11110", "01000", "00111"),
}
EMPTY_GLYPH = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


class Sheet:
    """An RGB canvas with small drawing primitives."""

    def __init__(self):
        self.buf = bytearray(bytes(PAPER) * (W * H))

    def dot(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.buf[i:i + len(row)] = row

    def rule_h(self, x, y, w, color, thick=1):
        self.fill(x, y, w, thick, color)

    def rule_v(self, x, y, h, color, thick=1):
        self.fill(x, y, thick, h, color)

    def frame(self, x, y, w, h, color, thick=1):
        self.fill(x, y, w, thick, color)
        self.fill(x, y + h - thick, w, thick, color)
        self.fill(x, y, thick, h, color)
        self.fill(x + w - thick, y, thick, h, color)

    def seg(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham segment; thick draws a square brush at each step."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.fill(x0 - half, y0 - half, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.rule_h(cx - dx, cy + dy, 2 * dx + 1, color)

    def ring(self, cx, cy, r, color, bg=PAPER, thick=2):
        """Circle outline: a filled disc with the middle punched out
        in the background colour behind it."""
        self.disc(cx, cy, r, color)
        self.disc(cx, cy, r - thick, bg)

    # -- text -------------------------------------------------------------
    def text_w(self, s, scale):
        if not s:
            return 0
        return len(s) * 6 * scale - scale

    def draw_text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = GLYPHS.get(ch, EMPTY_GLYPH)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def center(self, y, s, scale, color, x0=36, x1=988):
        w = self.text_w(s, scale)
        self.draw_text(x0 + (x1 - x0 - w) // 2, y, s, scale, color)

    def wrap(self, s, maxw, scale):
        """Greedy word wrap; returns a list of lines."""
        lines = []
        for chunk in s.split("\n"):
            words = chunk.split(" ")
            cur = ""
            for word in words:
                trial = word if not cur else cur + " " + word
                if self.text_w(trial, scale) <= maxw or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines

    def para(self, x, y, s, scale, maxw, color, leading):
        for line in self.wrap(s, maxw, scale):
            self.draw_text(x, y, line, scale, color)
            y += leading
        return y


# Pictograms (each 48x48 at the given top-left corner) -----------------------
def pic_cuffs(s, x, y):
    """Handcuffs: two rings joined by a short chain."""
    s.ring(x + 12, y + 24, 10, INK, PAPER, 3)
    s.ring(x + 36, y + 24, 10, INK, PAPER, 3)
    s.disc(x + 12, y + 24, 2, RED)
    s.disc(x + 36, y + 24, 2, RED)
    for cx in (20, 24, 28):
        s.disc(x + cx, y + 24, 2, INK)
    s.seg(x + 12, y + 12, x + 20, y + 6, INK, 2)
    s.seg(x + 36, y + 12, x + 28, y + 6, INK, 2)


def pic_globe_clock(s, x, y):
    """Globe with a small clock over it: climate talks running late."""
    s.ring(x + 22, y + 22, 20, BLUE, PAPER, 3)
    s.rule_h(x + 2, y + 22, 40, BLUE, 2)          # equator
    s.rule_v(x + 22, y + 2, 40, BLUE, 2)          # meridian
    s.seg(x + 6, y + 10, x + 38, y + 10, BLUE, 1)
    s.seg(x + 6, y + 34, x + 38, y + 34, BLUE, 1)
    # clock face overlapping the lower right
    s.disc(x + 36, y + 36, 11, PAPER)
    s.ring(x + 36, y + 36, 11, RED, PAPER, 2)
    s.seg(x + 36, y + 36, x + 36, y + 28, RED, 2)   # hand to 12
    s.seg(x + 36, y + 36, x + 42, y + 38, RED, 2)   # hand to 3


def pic_chart(s, x, y):
    """Falling market chart with a down arrow."""
    s.rule_v(x + 6, y + 4, 40, INK, 2)            # y axis
    s.rule_h(x + 6, y + 44, 40, INK, 2)           # x axis
    pts = [(10, 10), (18, 16), (26, 14), (34, 28), (42, 40)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        s.seg(x + ax, y + ay, x + bx, y + by, RED, 3)
    s.seg(x + 42, y + 40, x + 36, y + 38, RED, 2)  # arrowhead
    s.seg(x + 42, y + 40, x + 40, y + 34, RED, 2)
    s.disc(x + 10, y + 10, 2, RED)


def pic_missile(s, x, y):
    """A missile climbing, with a dotted trail and a burst."""
    # body
    s.seg(x + 24, y + 4, x + 30, y + 16, INK, 2)    # nose right
    s.seg(x + 24, y + 4, x + 18, y + 16, INK, 2)    # nose left
    s.fill(x + 19, y + 16, 10, 18, INK)             # body
    s.seg(x + 19, y + 20, x + 12, y + 32, INK, 2)   # left fin
    s.seg(x + 29, y + 20, x + 36, y + 32, INK, 2)   # right fin
    # flame
    s.disc(x + 24, y + 38, 4, EMBER)
    s.disc(x + 24, y + 38, 2, FLAME)
    # dotted trail below
    for dy in (44, 40 + 6):
        s.disc(x + 24, y + dy, 1, GREY)
    # small burst top right
    s.disc(x + 40, y + 8, 3, EMBER)
    s.disc(x + 40, y + 8, 1, FLAME)


def pic_eu_euro(s, x, y):
    """EU blue square, ring of twelve gold stars, euro sign."""
    s.fill(x, y, 48, 48, BLUE)
    for k in range(12):
        a = 2 * math.pi * k / 12
        dx = int(round(17 * math.cos(a)))
        dy = int(round(17 * math.sin(a)))
        s.disc(x + 24 + dx, y + 24 + dy, 2, GOLD)
    s.draw_text(x + 17, y + 17, "\u20ac", 2, GOLD)


def draw_lead_scene(s, x, y, w, h):
    """Dusk over a city skyline: two ballistic trails arc down to
    impact bursts, smoke rising from the rooftops."""
    s.fill(x, y, w, h, DUSK)
    # horizon band
    s.fill(x, y + h - 46, w, 46, DUSK2)
    # stars (fixed positions)
    stars = [(24, 12), (70, 26), (120, 8), (180, 30), (240, 10), (300, 24),
             (360, 12), (420, 28), (480, 10), (540, 26), (600, 12),
             (660, 28), (720, 10), (780, 24), (840, 12), (900, 26),
             (150, 44), (470, 46), (700, 44), (880, 46)]
    for sx, sy in stars:
        s.dot(x + sx, y + sy, MOON)
        s.dot(x + sx + 1, y + sy, MOON)
    # pale moon, upper left
    s.disc(x + 60, y + 34, 14, MOON)
    s.disc(x + 65, y + 31, 12, DUSK)
    # missile trails: curved descent in three segments each
    s.seg(x + 640, y + 2, x + 610, y + 34, (240, 200, 120), 2)
    s.seg(x + 610, y + 34, x + 580, y + 66, (240, 200, 120), 2)
    s.seg(x + 580, y + 66, x + 556, y + 92, (240, 200, 120), 2)
    s.seg(x + 830, y + 6, x + 810, y + 36, (240, 200, 120), 2)
    s.seg(x + 810, y + 36, x + 792, y + 62, (240, 200, 120), 2)
    s.seg(x + 792, y + 62, x + 778, y + 84, (240, 200, 120), 2)
    # skyline silhouettes along the bottom
    buildings = [(0, 44, 56), (56, 62, 48), (104, 38, 62), (166, 56, 42),
                 (208, 34, 64), (272, 60, 46), (318, 42, 58), (376, 58, 52),
                 (428, 36, 46), (474, 54, 60), (534, 40, 42), (576, 62, 56),
                 (632, 46, 50), (682, 66, 44), (726, 38, 46), (772, 56, 58),
                 (830, 42, 40), (870, 60, 52), (922, 48, 30)]
    for bx, bt, bw in buildings:
        s.fill(x + bx, y + h - bt, bw, bt, (12, 12, 14))
    # lit windows (fixed pattern)
    for wx in range(12, w - 8, 24):
        for wy in range(h - 58, h - 8, 14):
            if (wx * 7 + wy * 3) % 5 < 2:
                s.fill(x + wx, y + wy, 3, 4, GOLD)
    # impact bursts on two rooftops
    for ex, ey in [(300, h - 52), (800, h - 44)]:
        for k in range(8):
            a = math.pi * k / 4
            s.seg(x + ex, y + ey,
                  x + ex + int(13 * math.cos(a)),
                  y + ey + int(13 * math.sin(a)), EMBER, 2)
        s.disc(x + ex, y + ey, 6, EMBER)
        s.disc(x + ex, y + ey, 3, FLAME)
    # smoke columns rising from the impacts
    for sx in (296, 796):
        for k, (sw, sh) in enumerate([(10, 8), (14, 8), (18, 8)]):
            s.fill(x + sx - sw // 2, y + h - 58 - k * 10 - sh, sw, sh, GREY)


# Page assembly ---------------------------------------------------------------
def draw_story(s, x, y, w, kicker, headline, summary, icon):
    """One story block: kicker, headline, summary, pictogram top right."""
    s.draw_text(x, y, kicker, 2, RED)
    icon(s, x + w - 48, y)
    y2 = y + 20
    y2 = s.para(x, y2, headline, 3, w - 56, INK, 22)
    s.para(x, y2 + 4, summary, 2, w, INK, 16)


def draw_numbers_box(s, x, y, w, h):
    """By-the-numbers panel for the third row, right column."""
    s.fill(x, y, w, h, CLOUD)
    s.frame(x, y, w, h, INK, 2)
    s.center(y + 8, "BY THE NUMBERS", 2, RED, x, x + w)
    rows = [("60", "wounded in Kryvyi Rih"),
            ("11", "killed in Sinaloa"),
            ("5.28%", "Nasdaq's Friday fall")]
    ry = y + 32
    for num, label in rows:
        s.draw_text(x + 22, ry, num, 3, RED)
        s.draw_text(x + 132, ry + 4, label, 2, INK)
        ry += 26


def draw_page():
    s = Sheet()
    x0, x1 = 36, 988
    w = x1 - x0

    # Masthead ------------------------------------------------------------
    s.center(26, "THE WORLD IN ONE PAGE", 6, INK, x0, x1)
    date = "Saturday 21 November 2026"
    dw = s.text_w(date, 3)
    dcx = (W - dw) // 2
    s.rule_h(x0, 90, dcx - 20 - x0, INK, 2)
    s.rule_h(dcx + dw + 20, 90, x1 - (dcx + dw + 20), INK, 2)
    s.draw_text(dcx, 80, date, 3, RED)
    s.rule_h(x0, 112, w, INK, 3)
    s.rule_h(x0, 118, w, INK, 1)

    # Lead story ----------------------------------------------------------
    y = 130
    s.draw_text(x0, y, "LEAD STORY \u00b7 UKRAINE", 2, RED)
    y = 150
    s.draw_text(x0, y, "DOUBLE-TAP STRIKE", 5, INK)
    s.draw_text(x0, y + 42, "HITS ZELENSKYY'S HOMETOWN", 5, INK)
    y = 238
    draw_lead_scene(s, x0, y, w, 130)
    y = 378
    lead = ("Ballistic missiles hit Kryvyi Rih, President Zelenskyy's "
            "hometown, on Friday night, killing a seven-year-old boy and "
            "a 20-year-old woman and wounding 60 people, six of them "
            "children, in a second strike as rescuers arrived.")
    s.para(x0, y, lead, 2, w, INK, 18)

    # Rule above the story grid
    s.rule_h(x0, 446, w, INK, 1)

    # Five stories, two columns ------------------------------------------
    col_w = 466
    lx, rx = x0, x0 + col_w + 20
    s.rule_v(lx + col_w + 10, 462, 358, GREY, 1)

    draw_story(s, lx, 462, col_w, "MEXICO",
               "EL CHAPO ISIDRO CAPTURED IN SINALOA",
               "FBI Top 10 fugitive Fausto Isidro Meza Flores seized in "
               "Guasave with US help; 11 die in the fighting.",
               pic_cuffs)
    draw_story(s, rx, 462, col_w, "CLIMATE \u00b7 COP31",
               "COP31 RUNS INTO OVERTIME WITH NO DEAL",
               "Antalya talks run past their deadline, the draft still "
               "silent on fossil fuels. The EU: good deal or no deal.",
               pic_globe_clock)
    draw_story(s, lx, 584, col_w, "MARKETS",
               "NASDAQ ERASES ITS 2026 GAINS IN ROUT",
               "The Nasdaq falls 5.28% on Friday, erasing its 2026 gains; "
               "Nvidia drops 14% and Anthropic 8.5%.",
               pic_chart)
    draw_story(s, rx, 584, col_w, "WASHINGTON",
               "TRUMP WEIGHS NEW STRIKES ON IRAN",
               "President Trump weighs new strikes on Iran, officials say, "
               "as Israel presses him to move quickly.",
               pic_missile)
    draw_story(s, lx, 706, col_w, "EUROPE",
               "EU APPROVES 1BN EUROS OF ARMS FOR UKRAINE",
               "Brussels approves 1 billion euros of military support as "
               "Moscow rejects a peace deal.",
               pic_eu_euro)

    # By-the-numbers box, third row right ----------------------------------
    draw_numbers_box(s, rx, 706, col_w, 114)

    # Briefs strip ---------------------------------------------------------
    bx, by, bw, bh = x0, 836, w, 100
    s.fill(bx, by, bw, bh, CLOUD)
    s.frame(bx, by, bw, bh, INK, 2)
    s.draw_text(bx + 16, by + 9, "IN BRIEF", 2, RED)
    briefs = [
        "Nigeria \u2014 a boat capsizes on the way to a funeral, killing 24.",
        "Peru \u2014 a magnitude 6.7 earthquake strikes the Junin region.",
        "South Africa \u2014 Phumzile Mlambo-Ngcuka, ex-deputy president, "
        "dies at 71.",
    ]
    bw3 = (bw - 32 - 2 * 12) // 3
    for i, b in enumerate(briefs):
        cx = bx + 16 + i * (bw3 + 12)
        if i:
            s.rule_v(cx - 6, by + 28, bh - 38, GREY, 1)
        s.para(cx, by + 28, b, 2, bw3, INK, 16)

    # Footer ---------------------------------------------------------------
    s.center(956, "THE WORLD IN ONE PAGE \u2014 SATURDAY 21 NOVEMBER 2026",
             2, GREY, x0, x1)
    return s


# PNG encoder ---------------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, sheet):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += sheet.buf[yy * W * 3:(yy + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    sheet = draw_page()
    write_png(os.path.join(outdir, "entry.png"), sheet)


if __name__ == "__main__":
    main()
