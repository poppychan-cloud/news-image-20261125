#!/usr/bin/env python3
"""Draw the 25 November 2026 one-day world-news front page, v2, 1024x1024 PNG.

Second-iteration layout for make.fun news-image-20261125: 45 stories
(1 lead + 2 secondaries + 42 dated briefs across seven regions), a
six-moment timeline band, and an eight-marker schematic world map.
Sections stack top to bottom from one geometry table instead of fixed
y constants, so moving one section moves everything below it. Briefs
use a tight two-line headline plus one-line body, which is what lets
six briefs fit each region cell without shrinking the type below
readable size.

All copy comes from stories.json beside this file. Deterministic:
cached fonts, a fixed-seed star field, no clock, no network, no
randomness. Writes entry.png beside this file and prints a layout
report; anything trimmed or overflowing is named, never hidden.
"""
import hashlib
import json
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 1024
MARGIN = 12
COL_W = 244
COL_GAP = 8

# Section geometry, stacked top to bottom. Each entry is (top, height);
# main() walks them in order, so a height change ripples down cleanly.
GEOM = {
    "masthead": (0, 92),
    "hero": (96, 204),
    "secondaries": (312, 100),
    "timeline": (424, 44),
    "grid": (474, 514),
    "footer": (996, 16),
}
GRID_ROWS = 2
ROW_H = GEOM["grid"][1] // GRID_ROWS

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

INK = (16, 16, 16)
RED = (178, 34, 34)
DARK = (38, 38, 38)
GREY = (95, 95, 95)
FAINT = (205, 205, 205)
BAND = (16, 16, 16)
MAP_LAND = (214, 214, 214)
MAP_LINE = (118, 118, 118)
MAP_SEA = (238, 242, 247)

REPORT = []
_FONTS = {}


def font(path, size):
    """Cached font loader: same (path, size) returns the same object."""
    key = (path, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(path, size)
    return _FONTS[key]


def wrap_text(text, f, draw, maxw):
    """Greedy word wrap to lines fitting maxw pixels; keeps blank lines."""
    out = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            out.append("")
            continue
        line = words[0]
        for word in words[1:]:
            trial = line + " " + word
            if draw.textlength(trial, font=f) <= maxw:
                line = trial
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def fit_headline(text, path, sizes, maxw, draw, max_lines):
    """Largest size in `sizes` whose wrap fits max_lines; returns font, lines."""
    best = None
    for size in sizes:
        f = font(path, size)
        lines = wrap_text(text, f, draw, maxw)
        if len(lines) <= max_lines:
            return f, lines
        best = (f, lines)
    return best


def clip_lines(lines, max_lines, f, draw, maxw):
    """Cut to max_lines, marking the cut with an ellipsis. Returns lines, cut?"""
    if len(lines) <= max_lines:
        return lines, False
    kept = lines[:max_lines]
    last = kept[-1]
    while last and draw.textlength(last + "…", font=f) > maxw:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    kept[-1] = last + "…"
    return kept, True


def put_lines(draw, x, y, lines, f, fill, leading):
    """Draw lines top to bottom; returns the y after the last line."""
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


def draw_badge(draw, x, y, n):
    """Red disc with a white number, 15px across."""
    draw.ellipse([x, y, x + 14, y + 14], fill=RED)
    f = font(SANS_B, 10)
    s = str(n)
    tw = draw.textlength(s, font=f)
    draw.text((x + (15 - tw) / 2, y + 1), s, font=f, fill=(255, 255, 255))


# ---------- Hero illustration: Long March launch, scaled to fit ----------

def draw_rocket(draw, x0, y0, w, h):
    """Procedural night-launch scene in (x0, y0, w, h).

    All inner coordinates are written for a 376x210 canvas and scaled
    by (w/376, h/210), so the same drawing works at any hero size.
    """
    sx, sy = w / 376.0, h / 210.0

    def X(v):
        return x0 + v * sx

    def Y(v):
        return y0 + v * sy

    def rect(x, y, ww, hh, **kw):
        draw.rectangle([X(x), Y(y), X(x + ww), Y(y + hh)], **kw)

    def poly(points, **kw):
        draw.polygon([(X(px), Y(py)) for px, py in points], **kw)

    # Sky gradient, dark navy at the top to steel blue at the horizon.
    top = (8, 18, 48)
    bot = (38, 62, 108)
    for i in range(h):
        t = i / max(h - 1, 1)
        c = tuple(int(top[j] + (bot[j] - top[j]) * t) for j in range(3))
        draw.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=c)
    # Fixed-seed star field (deterministic: same seed, same sky).
    seed = 7

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return seed / 0x7FFFFFFF

    for _ in range(46):
        px = x0 + int(rnd() * w)
        py = y0 + int(rnd() * int(h * 0.62))
        r = 1 if rnd() < 0.7 else 2
        b = 150 + int(rnd() * 105)
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(b, b, b))
    # Moon.
    mx, my, mr = x0 + w - 42, y0 + 26, 13
    draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(232, 230, 214))
    draw.ellipse([mx - 5, my - 3, mx + 1, my + 3], fill=(205, 203, 188))
    draw.ellipse([mx + 3, my + 4, mx + 8, my + 9], fill=(205, 203, 188))
    # Ground silhouette.
    gy = Y(184)
    draw.rectangle([x0, gy, x0 + w, y0 + h], fill=(12, 14, 20))
    # Launch tower, left of the rocket.
    rect(108, 52, 14, 132, fill=(52, 56, 66))
    for ay in (70, 96, 122, 148):
        draw.line([(X(122), Y(ay)), (X(160), Y(ay))], fill=(52, 56, 66),
                  width=4)
    rect(112, 44, 6, 8, fill=RED)
    # Rocket body, nose cone, red band and flag stripe.
    rect(216, 58, 34, 110, fill=(238, 238, 238))
    draw.rectangle([X(216), Y(58), X(250), Y(168)], outline=(150, 150, 150))
    poly([(216, 58), (250, 58), (233, 32)], fill=RED)
    rect(216, 76, 34, 10, fill=RED)
    rect(216, 100, 34, 4, fill=(200, 60, 60))
    # Boosters.
    for bx in (200, 252):
        rect(bx, 112, 14, 56, fill=(225, 225, 225))
        draw.rectangle([X(bx), Y(112), X(bx + 14), Y(168)],
                       outline=(150, 150, 150))
        poly([(bx, 112), (bx + 14, 112), (bx + 7, 100)], fill=RED)
    # Flame: layered fixed polygons, brightest at the core.
    fy = 168
    poly([(204, fy), (262, fy), (246, fy + 34), (233, fy + 44),
          (220, fy + 34)], fill=(255, 140, 0))
    poly([(214, fy), (252, fy), (242, fy + 26), (233, fy + 32),
          (224, fy + 26)], fill=(255, 200, 0))
    poly([(222, fy), (244, fy), (238, fy + 18), (233, fy + 22),
          (228, fy + 18)], fill=(255, 244, 180))
    # Smoke banks hugging the ground.
    for cx, cy, rw, rh in ((150, 178, 90, 16), (250, 182, 110, 18),
                           (300, 174, 70, 12)):
        draw.ellipse([X(cx - rw // 2), Y(cy - rh // 2),
                      X(cx + rw // 2), Y(cy + rh // 2)], fill=(196, 196, 196))
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=INK, width=2)


# ---------- Small schematic world map ----------

CONTINENTS = [
    # North America
    [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-115, 73), (-105, 73),
     (-95, 80), (-85, 80), (-80, 73), (-70, 62), (-60, 55), (-55, 52),
     (-60, 47), (-65, 44), (-70, 42), (-75, 35), (-80, 26), (-84, 30),
     (-90, 21), (-95, 19), (-97, 16), (-94, 17), (-90, 14), (-85, 12),
     (-80, 9), (-85, 15), (-90, 20), (-95, 22), (-100, 25), (-105, 28),
     (-110, 30), (-115, 32), (-120, 35), (-125, 40), (-125, 48), (-130, 55),
     (-140, 60), (-150, 59), (-160, 58), (-168, 60)],
    # Greenland
    [(-58, 64), (-55, 60), (-45, 60), (-40, 64), (-32, 68), (-25, 70),
     (-20, 74), (-25, 78), (-35, 80), (-50, 78), (-58, 74), (-58, 68)],
    # South America
    [(-80, 9), (-75, 6), (-72, 2), (-78, -4), (-81, -6), (-80, -12),
     (-75, -18), (-70, -22), (-70, -30), (-65, -35), (-68, -40), (-70, -45),
     (-68, -52), (-65, -55), (-60, -50), (-58, -40), (-55, -35), (-48, -28),
     (-41, -22), (-38, -15), (-35, -8), (-38, -4), (-42, 0), (-48, 2),
     (-52, 5), (-58, 8), (-65, 10), (-72, 11), (-78, 10)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-2, 50), (2, 51),
     (5, 53), (8, 55), (8, 57), (10, 59), (13, 56), (18, 56), (21, 55),
     (24, 58), (28, 60), (30, 63), (25, 66), (20, 70), (15, 70), (12, 68),
     (8, 63), (5, 60), (0, 55), (-5, 50), (-8, 43), (-10, 38)],
    # Africa
    [(-17, 15), (-16, 20), (-10, 28), (-6, 33), (0, 35), (10, 37), (15, 33),
     (20, 32), (25, 32), (30, 31), (33, 28), (35, 24), (38, 20), (40, 15),
     (43, 12), (48, 11), (51, 11), (50, 5), (45, 0), (42, -5), (40, -10),
     (37, -15), (35, -20), (32, -25), (28, -30), (22, -35), (18, -34),
     (15, -28), (12, -20), (10, -12), (9, -5), (8, 4), (4, 6), (-2, 5),
     (-8, 4), (-13, 8), (-17, 12)],
    # Asia
    [(30, 36), (33, 40), (38, 42), (42, 45), (48, 44), (52, 46), (55, 48),
     (60, 50), (65, 52), (68, 55), (70, 58), (72, 62), (75, 66), (78, 70),
     (82, 73), (88, 75), (95, 76), (102, 77), (110, 76), (118, 74),
     (125, 72), (132, 71), (140, 72), (148, 71), (155, 69), (162, 66),
     (170, 66), (178, 65), (175, 62), (170, 60), (163, 58), (158, 52),
     (155, 48), (150, 44), (145, 42), (142, 38), (140, 35), (138, 33),
     (135, 34), (132, 33), (130, 31), (127, 33), (126, 36), (124, 38),
     (122, 32), (120, 28), (118, 25), (115, 22), (112, 20), (110, 15),
     (108, 12), (106, 10), (104, 8), (102, 6), (100, 8), (98, 12), (96, 15),
     (94, 17), (92, 20), (90, 22), (88, 22), (86, 20), (84, 18), (82, 16),
     (80, 14), (78, 8), (76, 10), (74, 14), (72, 20), (70, 22), (68, 23),
     (66, 25), (64, 25), (62, 25), (60, 25), (58, 26), (56, 27), (54, 28),
     (52, 28), (50, 29), (48, 30), (46, 30), (44, 29), (42, 31), (40, 33),
     (38, 36), (35, 36), (33, 36), (30, 36)],
    # Australia
    [(113, -22), (114, -28), (115, -33), (118, -35), (122, -34), (126, -32),
     (130, -32), (134, -33), (137, -35), (140, -38), (144, -38), (148, -37),
     (150, -36), (153, -32), (152, -28), (150, -24), (147, -20), (144, -16),
     (142, -13), (140, -17), (138, -15), (136, -13), (134, -12), (132, -12),
     (130, -13), (128, -14), (126, -14), (124, -16), (122, -18), (120, -20),
     (118, -21), (115, -22)],
    # Madagascar
    [(43, -12), (45, -13), (47, -15), (50, -16), (50, -18), (48, -21),
     (46, -24), (44, -25), (43, -22), (42, -18), (42, -15)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (-2, 51)],
    # Japan
    [(130, 31), (131, 32), (133, 34), (135, 34), (137, 35), (139, 36),
     (140, 38), (141, 40), (142, 42), (144, 44), (143, 43), (141, 41),
     (140, 39), (138, 37), (136, 35), (134, 34), (132, 33)],
    # Indonesia
    [(95, 5), (98, 3), (100, 0), (102, -2), (105, -4), (108, -6), (110, -7),
     (113, -8), (116, -9), (119, -9), (122, -10), (125, -9), (128, -8),
     (130, -6), (132, -4), (134, -3), (136, -2), (138, -3), (140, -5),
     (138, -7), (135, -8), (132, -8), (128, -9), (124, -10), (120, -10),
     (116, -10), (112, -8), (108, -7), (104, -5), (100, -2), (97, 2)],
    # New Zealand
    [(167, -45), (169, -43), (171, -41), (173, -39), (175, -38), (174, -40),
     (172, -42), (170, -44), (168, -46)],
]


def draw_map(draw, x0, y0, w, h, markers):
    """Equirectangular schematic map with numbered red markers."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=MAP_SEA)

    def proj(lon, lat):
        return (x0 + (lon + 170) / 360.0 * w,
                y0 + (80 - lat) / 140.0 * h)

    for poly in CONTINENTS:
        draw.polygon([proj(lon, lat) for lon, lat in poly],
                     fill=MAP_LAND, outline=MAP_LINE)
    for m in markers:
        mx, my = proj(m["lon"], m["lat"])
        draw.ellipse([mx - 8, my - 8, mx + 8, my + 8], fill=RED,
                     outline=(255, 255, 255), width=1)
        f = font(SANS_B, 10)
        s = str(m["n"])
        tw = draw.textlength(s, font=f)
        draw.text((mx - tw / 2, my - 6), s, font=f, fill=(255, 255, 255))
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=FAINT, width=1)


# ---------- Briefs and region cells ----------

def draw_brief(draw, x, y, w, brief, cell_name):
    """One dated brief: bold dateline + headline (max 2 lines), then a
    one-line body. Returns the height used, including the gap below."""
    head_f = font(SANS_B, 12)
    body_f = font(SANS, 11)
    n = brief.get("map_no")
    indent = 19 if n else 0
    text = brief["dateline"] + " — " + brief["headline"]
    if n:
        # Narrow first line leaves room for the badge.
        words = text.split()
        lines, cur, lim = [], "", w - indent
        for word in words:
            trial = (cur + " " + word).strip()
            if draw.textlength(trial, font=head_f) <= lim:
                cur = trial
            else:
                lines.append(cur)
                cur, lim = word, w
        if cur:
            lines.append(cur)
    else:
        lines = wrap_text(text, head_f, draw, w)
    lines, hcut = clip_lines(lines, 2, head_f, draw, w - indent)
    blines = wrap_text(brief["body"], body_f, draw, w)
    blines, bcut = clip_lines(blines, 1, body_f, draw, w)
    if hcut or bcut:
        REPORT.append("TRIMMED %s: %s" % (cell_name, brief["headline"][:48]))
    yy = y
    prefix = brief["dateline"] + " — "
    for i, ln in enumerate(lines):
        tx = x + (indent if (i == 0 and n) else 0)
        if i == 0 and ln.startswith(prefix):
            pw = draw.textlength(prefix, font=head_f)
            draw.text((tx, yy), prefix, font=head_f, fill=RED)
            draw.text((tx + pw, yy), ln[len(prefix):], font=head_f, fill=INK)
        else:
            draw.text((tx, yy), ln, font=head_f, fill=INK)
        yy += 12
    if n:
        draw_badge(draw, x, y, n)
    yy = put_lines(draw, x, yy, blines, body_f, DARK, 11)
    return yy - y + 3


def draw_region(draw, x, y, w, h, region):
    """Region cell: black name band, then its briefs stacked to fit."""
    draw.rectangle([x, y, x + w, y + 22], fill=BAND)
    draw.text((x + 6, y + 4), region["name"], font=font(SANS_B, 13),
              fill=(255, 255, 255))
    count = "%d STORIES" % len(region["shorts"])
    cf = font(SANS_B, 10)
    draw.text((x + w - 6 - draw.textlength(count, font=cf), y + 5), count,
              font=cf, fill=(190, 190, 190))
    yy = y + 26
    for sh in region["shorts"]:
        yy += draw_brief(draw, x + 4, yy, w - 8, sh, region["name"])
    if yy > y + h - 3:
        REPORT.append("OVERFLOW %s: briefs end %dpx past cell bottom %d"
                      % (region["name"], yy - (y + h - 3), y + h - 3))


# ---------- Timeline band ----------

def draw_timeline(draw, x, y, w, spec):
    """Six moments in two lines; whole events stay intact per line."""
    f = font(SANS, 10)
    title_f = font(SANS_B, 11)
    draw.text((x, y), spec["title"], font=title_f, fill=RED)
    sep = "   •   "
    sep_w = draw.textlength(sep, font=f)
    lines, cur, cur_w = [], "", 0
    for ev in spec["events"]:
        ew = draw.textlength(ev, font=f)
        add = ew if not cur else sep_w + ew
        if cur and cur_w + add > w:
            lines.append(cur)
            cur, cur_w = ev, ew
        else:
            cur = (cur + sep + ev) if cur else ev
            cur_w += add
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        REPORT.append("TIMELINE %d lines, budget 2" % len(lines))
        lines = lines[:2]
    yy = y + 15
    for ln in lines:
        draw.text((x, yy), ln, font=f, fill=DARK)
        yy += 14
    return yy - y


# ---------- Page sections ----------

def section_masthead(draw, S):
    top, _ = GEOM["masthead"]
    name_f = font(SERIF_B, 40)
    name = S["masthead"]
    draw.text(((PAGE - draw.textlength(name, font=name_f)) / 2, top + 8),
              name, font=name_f, fill=INK)
    date_f = font(SANS_B, 26)
    date = S["date_line"]
    draw.text(((PAGE - draw.textlength(date, font=date_f)) / 2, top + 52),
              date, font=date_f, fill=RED)
    n = 1 + len(S["secondary"]) + sum(len(r["shorts"])
                                      for r in S["regions"])
    tag = "%d STORIES • 7 REGIONS" % n
    tf = font(SANS_B, 12)
    draw.text((PAGE - MARGIN - draw.textlength(tag, font=tf), top + 58),
              tag, font=tf, fill=GREY)
    draw.line([(MARGIN, top + 84), (PAGE - MARGIN, top + 84)], fill=INK,
              width=3)
    draw.line([(MARGIN, top + 89), (PAGE - MARGIN, top + 89)], fill=RED,
              width=2)


def section_hero(draw, S):
    top, height = GEOM["hero"]
    lead = S["lead"]
    draw_rocket(draw, MARGIN, top, 376, 160)
    cap = wrap_text(lead["caption"], font(SANS, 11), draw, 376)
    cap, _ = clip_lines(cap, 2, font(SANS, 11), draw, 376)
    put_lines(draw, MARGIN, top + 166, cap, font(SANS, 11), GREY, 13)
    tx = 404
    tw = PAGE - MARGIN - tx
    kx = tx
    if lead.get("map_no"):
        draw_badge(draw, tx, top, lead["map_no"])
        kx = tx + 19
    draw.text((kx, top), lead["kicker"], font=font(SANS_B, 15), fill=RED)
    hf, hlines = fit_headline(lead["headline"], SERIF_B, [30, 28], tw,
                              draw, 3)
    y = put_lines(draw, tx, top + 22, hlines, hf, INK, 32)
    sf = font(SANS, 15)
    slines = wrap_text(lead["summary"], sf, draw, tw)
    slines, scut = clip_lines(slines, 3, sf, draw, tw)
    if scut:
        REPORT.append("TRIMMED lead summary")
    y = put_lines(draw, tx, y + 6, slines, sf, DARK, 19)
    draw.rectangle([tx, y + 6, tx + 8, y + 14], fill=RED)
    draw.text((tx + 14, y + 2), lead["fact"], font=font(SANS_B, 14),
              fill=INK)
    if y + 20 > top + height:
        REPORT.append("OVERFLOW lead: ends at y=%d (budget %d)"
                      % (y + 20, top + height))


def section_secondaries(draw, S):
    top, height = GEOM["secondaries"]
    draw.line([(512, top + 6), (512, top + height - 6)], fill=FAINT, width=2)
    for i, st in enumerate(S["secondary"][:2]):
        x = MARGIN + i * 512
        cw = 488
        kx = x
        if st.get("map_no"):
            draw_badge(draw, x, top, st["map_no"])
            kx = x + 19
        draw.text((kx, top), st["kicker"], font=font(SANS_B, 13), fill=RED)
        kf, klines = fit_headline(st["headline"], SANS_B, [18, 17], cw,
                                  draw, 2)
        yy = put_lines(draw, x, top + 20, klines, kf, INK, 20)
        bf = font(SANS, 13)
        blines = wrap_text(st["summary"], bf, draw, cw)
        blines, bcut = clip_lines(blines, 2, bf, draw, cw)
        if bcut:
            REPORT.append("TRIMMED secondary: %s" % st["headline"][:40])
        yy = put_lines(draw, x, yy + 4, blines, bf, DARK, 16)
        if yy > top + height:
            REPORT.append("OVERFLOW secondary %d: ends at y=%d (budget %d)"
                          % (i + 1, yy, top + height))


def section_grid(draw, S):
    top, height = GEOM["grid"]
    regions = S["regions"]
    cells = regions[:4] + regions[4:7] + [None]
    for row in range(GRID_ROWS):
        for col in range(4):
            cell = cells[row * 4 + col]
            cx = MARGIN + col * (COL_W + COL_GAP)
            cy = top + row * ROW_H
            if cell is None:
                draw.rectangle([cx, cy, cx + COL_W, cy + 22], fill=BAND)
                draw.text((cx + 6, cy + 4), S["map"]["title"],
                          font=font(SANS_B, 13), fill=(255, 255, 255))
                draw_map(draw, cx + 4, cy + 28, COL_W - 8, 150,
                         S["map"]["markers"])
                lf = font(SANS, 11)
                ly = cy + 184
                for ln in S["map"]["legend"]:
                    lx = cx + (COL_W - draw.textlength(ln, font=lf)) / 2
                    draw.text((lx, ly), ln, font=lf, fill=DARK)
                    ly += 15
                draw.text((cx + (COL_W - draw.textlength(
                    "Numbers match the stories",
                    font=font(SANS, 10))) / 2, ly + 2),
                    "Numbers match the stories", font=font(SANS, 10),
                    fill=GREY)
            else:
                draw_region(draw, cx, cy, COL_W, ROW_H, cell)
    for col in (1, 2, 3):
        vx = MARGIN + col * (COL_W + COL_GAP) - COL_GAP // 2
        draw.line([(vx, top), (vx, top + height)], fill=FAINT, width=1)
    draw.line([(MARGIN, top + ROW_H), (PAGE - MARGIN, top + ROW_H)],
              fill=FAINT, width=1)


def build():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as fh:
        S = json.load(fh)

    img = Image.new("RGB", (PAGE, PAGE), "white")
    d = ImageDraw.Draw(img)

    section_masthead(d, S)
    section_hero(d, S)
    d.line([(MARGIN, GEOM["hero"][0] + GEOM["hero"][1] + 6),
            (PAGE - MARGIN, GEOM["hero"][0] + GEOM["hero"][1] + 6)],
           fill=INK, width=2)
    section_secondaries(d, S)
    d.line([(MARGIN, GEOM["secondaries"][0] + GEOM["secondaries"][1] + 6),
            (PAGE - MARGIN,
             GEOM["secondaries"][0] + GEOM["secondaries"][1] + 6)],
           fill=INK, width=2)
    draw_timeline(d, MARGIN, GEOM["timeline"][0], PAGE - 2 * MARGIN,
                  S["timeline"])
    section_grid(d, S)

    ff = font(SANS, 12)
    top, _ = GEOM["footer"]
    d.text(((PAGE - d.textlength(S["footer"], font=ff)) / 2, top),
           S["footer"], font=ff, fill=GREY)

    out_local = os.path.join(HERE, "entry.png")
    img.save(out_local, optimize=True)
    data = open(out_local, "rb").read()
    n_stories = 1 + len(S["secondary"]) + sum(
        len(r["shorts"]) for r in S["regions"])
    print("stories:", n_stories)
    print("size:", img.size, os.path.getsize(out_local), "bytes")
    print("sha256:", hashlib.sha256(data).hexdigest())
    if REPORT:
        print("LAYOUT REPORT (%d):" % len(REPORT))
        for r in REPORT:
            print("  -", r)
    else:
        print("layout: clean, no trims or overflows")


if __name__ == "__main__":
    build()
