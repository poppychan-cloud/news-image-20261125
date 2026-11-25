#!/usr/bin/env python3
"""Draw the 25 November 2026 one-day world-news front page, 1024x1024 PNG.

High-density layout for make.fun news-image-20261125: a masthead with the
date set very large, one lead story with a drawn Long March rocket-launch
illustration, two secondary stories, seven region columns of dated shorts,
and a small numbered world map whose numbers match the stories they mark.
All copy comes from stories.json beside this file.

Deterministic: fixed fonts, a fixed-seed star field, no clock, no network,
no randomness. Writes entry.png beside this file and prints a layout
report; any short that had to be trimmed is named, so a bad fit is
visible instead of silently overflowing its column.
"""
import hashlib
import json
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024
MARGIN = 12
COL_W = 244
COL_GAP = 8
GRID_TOP = 474
ROW_H = 257

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


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap_px(text, f, draw, maxw):
    """Wrap text to lines that fit maxw pixels, honouring explicit \\n."""
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


def wrap_first(text, f, draw, w_first, w_rest):
    """Wrap with a narrower first line (room for a number badge)."""
    words = text.split()
    lines = []
    cur = ""
    w = w_first
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
            w = w_rest
    if cur:
        lines.append(cur)
    return lines


def fit_lines(text, path, sizes, maxw, draw, max_lines):
    """Largest size whose wrap fits max_lines; returns (font, lines)."""
    fallback = None
    for size in sizes:
        f = F(path, size)
        lines = wrap_px(text, f, draw, maxw)
        if len(lines) <= max_lines:
            return f, lines
        fallback = (f, lines)
    return fallback


def draw_lines(draw, x, y, lines, f, fill, leading):
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += leading
    return y


def badge(draw, x, y, n):
    """Small red circle with a white number, 16px across."""
    draw.ellipse([x, y, x + 15, y + 15], fill=RED)
    f = F(SANS_B, 11)
    s = str(n)
    tw = draw.textlength(s, font=f)
    draw.text((x + (16 - tw) / 2, y + 1), s, font=f, fill=(255, 255, 255))


def trunc_to(lines, max_lines, f, draw, maxw):
    """Cut lines to max_lines, marking the cut with an ellipsis."""
    if len(lines) <= max_lines:
        return lines, False
    kept = lines[:max_lines]
    last = kept[-1]
    while last and draw.textlength(last + "…", font=f) > maxw:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    kept[-1] = last + "…"
    return kept, True


# ---------- Hero illustration: Long March launch at night ----------

def draw_rocket(draw, x0, y0, w, h):
    """Procedural night-launch scene inside (x0, y0, w, h)."""
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
        sx = x0 + int(rnd() * w)
        sy = y0 + int(rnd() * int(h * 0.62))
        r = 1 if rnd() < 0.7 else 2
        b = 150 + int(rnd() * 105)
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(b, b, b))
    # Moon.
    mx, my, mr = x0 + w - 42, y0 + 26, 13
    draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(232, 230, 214))
    draw.ellipse([mx - 5, my - 3, mx + 1, my + 3], fill=(205, 203, 188))
    draw.ellipse([mx + 3, my + 4, mx + 8, my + 9], fill=(205, 203, 188))
    # Ground silhouette.
    gy = y0 + h - 26
    draw.rectangle([x0, gy, x0 + w, y0 + h], fill=(12, 14, 20))
    # Launch tower, left of the rocket.
    tx = x0 + 108
    draw.rectangle([tx, y0 + 52, tx + 14, gy], fill=(52, 56, 66))
    for ay in (y0 + 70, y0 + 96, y0 + 122, y0 + 148):
        draw.line([(tx + 14, ay), (tx + 52, ay)], fill=(52, 56, 66), width=4)
    draw.rectangle([tx + 4, y0 + 44, tx + 10, y0 + 52], fill=RED)
    # Rocket body, centred near x0+232.
    rx = x0 + 216
    draw.rectangle([rx, y0 + 58, rx + 34, y0 + 168], fill=(238, 238, 238))
    draw.rectangle([rx, y0 + 58, rx + 34, y0 + 168], outline=(150, 150, 150))
    # Nose cone.
    draw.polygon([(rx, y0 + 58), (rx + 34, y0 + 58), (rx + 17, y0 + 32)],
                 fill=RED)
    # Red band and flag stripe.
    draw.rectangle([rx, y0 + 76, rx + 34, y0 + 86], fill=RED)
    draw.rectangle([rx, y0 + 100, rx + 34, y0 + 104], fill=(200, 60, 60))
    # Boosters.
    for bx in (rx - 16, rx + 36):
        draw.rectangle([bx, y0 + 112, bx + 14, y0 + 168], fill=(225, 225, 225))
        draw.rectangle([bx, y0 + 112, bx + 14, y0 + 168],
                       outline=(150, 150, 150))
        draw.polygon([(bx, y0 + 112), (bx + 14, y0 + 112), (bx + 7, y0 + 100)],
                     fill=RED)
    # Flame: layered fixed polygons, brightest at the core.
    fy = y0 + 168
    draw.polygon([(rx - 12, fy), (rx + 46, fy), (rx + 30, fy + 34),
                  (rx + 17, fy + 44), (rx + 4, fy + 34)], fill=(255, 140, 0))
    draw.polygon([(rx - 2, fy), (rx + 36, fy), (rx + 26, fy + 26),
                  (rx + 17, fy + 32), (rx + 8, fy + 26)], fill=(255, 200, 0))
    draw.polygon([(rx + 6, fy), (rx + 28, fy), (rx + 22, fy + 18),
                  (rx + 17, fy + 22), (rx + 12, fy + 18)], fill=(255, 244, 180))
    # Smoke banks hugging the ground.
    for cx, cy, rw, rh in ((x0 + 150, gy - 6, 90, 16), (x0 + 250, gy - 2, 110, 18),
                           (x0 + 300, gy - 10, 70, 12)):
        draw.ellipse([cx - rw // 2, cy - rh // 2, cx + rw // 2, cy + rh // 2],
                     fill=(196, 196, 196))
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
    """Schematic equirectangular world map with numbered story markers."""
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=MAP_SEA)

    def proj(lon, lat):
        return (x0 + (lon + 170) / 360.0 * w,
                y0 + (80 - lat) / 140.0 * h)

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_LAND, outline=MAP_LINE)
    for m in markers:
        mx, my = proj(m["lon"], m["lat"])
        draw.ellipse([mx - 8, my - 8, mx + 8, my + 8], fill=RED,
                     outline=(255, 255, 255), width=1)
        f = F(SANS_B, 10)
        s = str(m["n"])
        tw = draw.textlength(s, font=f)
        draw.text((mx - tw / 2, my - 6), s, font=f, fill=(255, 255, 255))
    draw.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], outline=FAINT, width=1)


# ---------- Region column ----------

def draw_short(draw, x, y, w, short, max_lines, cell_name):
    """One dated short: bold dateline+headline, then body. Returns height."""
    bold = F(SANS_B, 12)
    body_f = F(SANS, 11)
    lead = 12
    n = short.get("map_no")
    indent = 20 if n else 0
    full = short["dateline"] + " — " + short["headline"]
    if n:
        hlines = wrap_first(full, bold, draw, w - indent, w)
    else:
        hlines = wrap_px(full, bold, draw, w)
    hlines, hcut = trunc_to(hlines, 2, bold, draw, w - indent)
    blines = wrap_px(short["body"], body_f, draw, w)
    room = max_lines - len(hlines)
    blines, bcut = trunc_to(blines, max(room, 0), body_f, draw, w)
    if hcut or bcut:
        REPORT.append("TRIMMED %s: %s" % (cell_name, short["headline"][:48]))
    yy = y
    prefix = short["dateline"] + " — "
    for i, ln in enumerate(hlines):
        tx = x + (indent if (i == 0 and n) else 0)
        if i == 0:
            pw = draw.textlength(prefix, font=bold)
            if ln.startswith(prefix):
                draw.text((tx, yy), prefix, font=bold, fill=RED)
                draw.text((tx + pw, yy), ln[len(prefix):], font=bold, fill=INK)
            else:
                draw.text((tx, yy), ln, font=bold, fill=INK)
        else:
            draw.text((tx, yy), ln, font=bold, fill=INK)
        yy += lead
    if n:
        badge(draw, x, y, n)
    yy = draw_lines(draw, x, yy, blines, body_f, DARK, lead)
    return yy - y


def draw_region_cell(draw, x, y, w, h, region):
    d = draw
    d.rectangle([x, y, x + w, y + 22], fill=BAND)
    d.text((x + 6, y + 4), region["name"], font=F(SANS_B, 13),
           fill=(255, 255, 255))
    count = "%d STORIES" % len(region["shorts"])
    cf = F(SANS_B, 10)
    d.text((x + w - 6 - d.textlength(count, font=cf), y + 5), count,
           font=cf, fill=(190, 190, 190))
    shorts = region["shorts"]
    max_lines = 4 if len(shorts) == 4 else 6
    yy = y + 28
    for i, sh in enumerate(shorts):
        used = draw_short(d, x + 4, yy, w - 8, sh, max_lines, region["name"])
        yy += used
        if i < len(shorts) - 1:
            yy += 3
            d.line([(x + 4, yy), (x + w - 4, yy)], fill=FAINT, width=1)
            yy += 3
    if yy > y + h - 4:
        REPORT.append("OVERFLOW %s: shorts end %dpx past cell bottom %d"
                      % (region["name"], yy - (y + h - 4), y + h - 4))
    return yy


def main():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as fh:
        S = json.load(fh)

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    # ---------- Masthead: name, then the DATE very large ----------
    d.text(((W - d.textlength(S["masthead"], font=F(SERIF_B, 40))) / 2, 8),
           S["masthead"], font=F(SERIF_B, 40), fill=INK)
    d.text(((W - d.textlength(S["date_line"], font=F(SANS_B, 26))) / 2, 52),
           S["date_line"], font=F(SANS_B, 26), fill=RED)
    d.line([(MARGIN, 84), (W - MARGIN, 84)], fill=INK, width=3)
    d.line([(MARGIN, 89), (W - MARGIN, 89)], fill=RED, width=2)

    # ---------- Lead story with drawn illustration ----------
    lead = S["lead"]
    draw_rocket(d, MARGIN, 96, 376, 210)
    cap = wrap_px(lead["caption"], F(SANS, 11), d, 376)
    draw_lines(d, MARGIN, 310, cap, F(SANS, 11), GREY, 14)
    tx = 404
    tw = W - MARGIN - tx
    kx = tx
    if lead.get("map_no"):
        badge(d, tx, 96, lead["map_no"])
        kx = tx + 20
    d.text((kx, 96), lead["kicker"], font=F(SANS_B, 15), fill=RED)
    hf, hlines = fit_lines(lead["headline"], SERIF_B, [36, 32], tw, d, 3)
    y = draw_lines(d, tx, 120, hlines, hf, INK, int(hf.size * 1.06))
    y += 8
    sf = F(SANS, 16)
    slines = wrap_px(lead["summary"], sf, d, tw)
    slines, scut = trunc_to(slines, 4, sf, d, tw)
    if scut:
        REPORT.append("TRIMMED lead summary")
    y = draw_lines(d, tx, y, slines, sf, DARK, 21)
    y += 6
    d.rectangle([tx, y + 4, tx + 8, y + 12], fill=RED)
    d.text((tx + 14, y), lead["fact"], font=F(SANS_B, 14), fill=INK)
    if y + 18 > 334:
        REPORT.append("OVERFLOW lead: ends at y=%d (budget 334)" % (y + 18))

    # ---------- Secondary stories (2 columns) ----------
    d.line([(MARGIN, 340), (W - MARGIN, 340)], fill=INK, width=2)
    d.line([(512, 346), (512, 470)], fill=FAINT, width=2)
    for i, st in enumerate(S["secondary"][:2]):
        x = MARGIN + i * 512
        cw = 488
        kx = x
        if st.get("map_no"):
            badge(d, x, 346, st["map_no"])
            kx = x + 20
        d.text((kx, 346), st["kicker"], font=F(SANS_B, 13), fill=RED)
        kf, klines = fit_lines(st["headline"], SANS_B, [20, 18], cw, d, 2)
        yy = draw_lines(d, x, 368, klines, kf, INK, int(kf.size * 1.12))
        bf = F(SANS, 14)
        blines = wrap_px(st["summary"], bf, d, cw)
        blines, bcut = trunc_to(blines, 3, bf, d, cw)
        if bcut:
            REPORT.append("TRIMMED secondary: %s" % st["headline"][:40])
        yy = draw_lines(d, x, yy + 4, blines, bf, DARK, 18)
        if yy > 470:
            REPORT.append("OVERFLOW secondary %d: ends at y=%d (budget 470)"
                          % (i + 1, yy))

    # ---------- Region grid: 7 regions + map, 4 columns x 2 rows ----------
    regions = S["regions"]
    cells = regions[:4] + regions[4:7] + [None]
    for row in range(2):
        for col in range(4):
            cell = cells[row * 4 + col]
            cx = MARGIN + col * (COL_W + COL_GAP)
            cy = GRID_TOP + row * ROW_H
            if cell is None:
                d.rectangle([cx, cy, cx + COL_W, cy + 22], fill=BAND)
                d.text((cx + 6, cy + 4), S["map"]["title"],
                       font=F(SANS_B, 13), fill=(255, 255, 255))
                draw_map(d, cx + 4, cy + 28, COL_W - 8, 150,
                         S["map"]["markers"])
                lf = F(SANS, 11)
                ly = cy + 184
                for ln in S["map"]["legend"]:
                    lx = cx + (COL_W - d.textlength(ln, font=lf)) / 2
                    d.text((lx, ly), ln, font=lf, fill=DARK)
                    ly += 15
                d.text((cx + (COL_W - d.textlength("Numbers match the stories",
                                                   font=F(SANS, 10))) / 2,
                        ly + 2), "Numbers match the stories",
                       font=F(SANS, 10), fill=GREY)
            else:
                draw_region_cell(d, cx, cy, COL_W, ROW_H, cell)
    for col in (1, 2, 3):
        vx = MARGIN + col * (COL_W + COL_GAP) - COL_GAP // 2
        d.line([(vx, GRID_TOP), (vx, GRID_TOP + 2 * ROW_H)], fill=FAINT,
               width=1)
    d.line([(MARGIN, GRID_TOP + ROW_H), (W - MARGIN, GRID_TOP + ROW_H)],
           fill=FAINT, width=1)

    # ---------- Footer ----------
    ff = F(SANS, 12)
    d.text(((W - d.textlength(S["footer"], font=ff)) / 2, 996),
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
    main()
