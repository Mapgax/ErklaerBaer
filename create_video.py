#!/usr/bin/env python3
"""
ErklaerBaer – Atome und Laser
Animiertes Erklärvideo für Kinder (5–6 Jahre)
Erstellt mit Pillow + imageio
"""

import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

# ─── CONFIG ───────────────────────────────────────────────────────────────────
W, H = 1280, 720
FPS  = 15
OUTPUT = "atom_laser.mp4"

# ─── FARB-PALETTE ─────────────────────────────────────────────────────────────
BG_SKY    = (200, 230, 255)   # Himmelblau
BG_SUN    = (255, 248, 200)   # Sonnig-gelb
BG_GRASS  = (215, 250, 215)   # Grün
BG_PURPLE = (240, 220, 255)   # Lila

RED_NUC   = (255,  80,  50)   # Kern-Rot
ORG_NUC   = (255, 150, 100)   # Kern-Highlight
E_BLUE    = ( 60, 155, 255)   # Elektron blau
E_GREEN   = ( 60, 210,  80)   # Elektron grün
E_YELLOW  = (255, 200,  40)   # Elektron gelb
EXCITED_C = (255, 255,  50)   # aufgeregt gelb-weiß
PHOTON_C  = (255, 230,   0)   # Photon-gelb
LASER_V   = (200,  40, 255)   # Laser violett
LASER_R   = (255,  50, 100)   # Laser rot

TXT_DARK  = ( 40,  25,  10)
TXT_WHITE = (255, 255, 255)
TITLE_R   = (200,  50,  20)
OUTLINE   = (  0,   0,   0)
WHITE     = (255, 255, 255)

# ─── FONTS ────────────────────────────────────────────────────────────────────
def load_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

FT_HUGE = load_font(88)
FT_BIG  = load_font(64)
FT_MED  = load_font(44)
FT_SML  = load_font(30)
FT_XSM  = load_font(22)

# ─── MATHEMATIK / HILFSFUNKTIONEN ─────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * t

def lerpc(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def eio(t):
    """Ease in-out."""
    t = clamp(t)
    return t * t * (3 - 2 * t)

def eo(t):
    """Ease out cubic."""
    t = clamp(t)
    return 1 - (1 - t) ** 3

def ei(t):
    """Ease in cubic."""
    t = clamp(t)
    return t * t * t

def bounce(t):
    """Kleiner Hüpf-Effekt."""
    t = clamp(t)
    if t < 0.5:
        return eio(t * 2) * 0.5
    else:
        b = math.sin((t - 0.5) * math.pi * 4) * (1 - t) * 0.3
        return 0.5 + (t - 0.5) * 2 * 0.5 + b

def wiggle(t, amp=5, freq=8):
    """Kleines Zittern."""
    return math.sin(t * freq * math.pi * 2) * amp

# ─── ZEICHEN-GRUNDBAUSTEINE ───────────────────────────────────────────────────
def gradient_bg(img, c_top, c_bot):
    """Vertikaler Farbverlauf."""
    px = img.load()
    for y in range(H):
        t = y / H
        r = int(lerp(c_top[0], c_bot[0], t))
        g = int(lerp(c_top[1], c_bot[1], t))
        b = int(lerp(c_top[2], c_bot[2], t))
        for x in range(W):
            px[x, y] = (r, g, b)

def circ(d, cx, cy, r, fill, ol=None, olw=4):
    """Kreis mit Umriss."""
    if ol and olw > 0:
        d.ellipse([cx-r-olw//2, cy-r-olw//2,
                   cx+r+olw//2, cy+r+olw//2], fill=ol)
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=fill)

def star(d, cx, cy, r_out, r_in, n, angle, fill, ol=None, olw=3):
    """N-zackiger Stern."""
    pts = []
    for i in range(n * 2):
        a = angle + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    if ol:
        d.polygon([(x+olw, y+olw) for x,y in pts], fill=(0,0,0,80))
    d.polygon(pts, fill=fill, outline=ol or fill, width=olw)

def glow(d, cx, cy, r, color, steps=4):
    """Leuchteffekt um Kreis."""
    for i in range(steps, 0, -1):
        alpha = int(120 * i / steps)
        extra = i * 8
        rgba = color + (alpha,)
        # PIL supports RGBA on RGBA images; we approximate with lighter color
        faded = lerpc(color, (255, 255, 255), 1 - i / steps)
        d.ellipse([cx-r-extra, cy-r-extra, cx+r+extra, cy+r+extra],
                  outline=faded, width=3)

def rounded_rect(d, x0, y0, x1, y1, radius, fill, ol=None, olw=4):
    """Abgerundetes Rechteck."""
    if ol:
        d.rounded_rectangle([x0-olw//2, y0-olw//2, x1+olw//2, y1+olw//2],
                             radius=radius+olw//2, fill=ol)
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)

def ctext(d, text, x, y, fnt, fill=TXT_DARK, shadow=True, anchor="mm"):
    """Text zentriert mit Schatten."""
    if shadow:
        d.text((x+3, y+4), text, font=fnt, fill=(0, 0, 0), anchor=anchor)
    d.text((x, y), text, font=fnt, fill=fill, anchor=anchor)

def wrapped_text(d, text, cx, cy, max_w, fnt, fill=TXT_DARK,
                 line_spacing=10, shadow=True):
    """Mehrzeiliger zentrierter Text."""
    words = text.split()
    lines, line = [], ""
    for w in words:
        trial = (line + " " + w).strip()
        bb = d.textbbox((0, 0), trial, font=fnt)
        if bb[2] - bb[0] <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    lh = fnt.size if hasattr(fnt, "size") else 30
    total_h = len(lines) * (lh + line_spacing) - line_spacing
    y0 = cy - total_h // 2
    for ln in lines:
        ctext(d, ln, cx, y0 + lh // 2, fnt, fill=fill, shadow=shadow)
        y0 += lh + line_spacing

def speech_bubble(d, cx, cy, bw, bh, text, fnt, tail="down"):
    """Sprechblase."""
    x0, y0 = cx - bw // 2, cy - bh // 2
    x1, y1 = cx + bw // 2, cy + bh // 2
    r = 28
    # Schatten
    d.rounded_rectangle([x0+5, y0+5, x1+5, y1+5], radius=r, fill=(160,150,140))
    # Hintergrund
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=WHITE,
                        outline=OUTLINE, width=4)
    # Schwänzchen
    if tail == "down":
        d.polygon([(cx-16, y1), (cx+16, y1), (cx, y1+30)], fill=WHITE)
        d.line([(cx-16, y1+1), (cx, y1+30)], fill=OUTLINE, width=4)
        d.line([(cx+16, y1+1), (cx, y1+30)], fill=OUTLINE, width=4)
    elif tail == "left":
        d.polygon([(x0, cy-12), (x0, cy+12), (x0-30, cy)], fill=WHITE)
        d.line([(x0, cy-12), (x0-30, cy)], fill=OUTLINE, width=4)
        d.line([(x0, cy+12), (x0-30, cy)], fill=OUTLINE, width=4)
    # Text
    wrapped_text(d, text, cx, cy, bw - 40, fnt, shadow=False)

# ─── ATOM ZEICHNEN ────────────────────────────────────────────────────────────
ORBIT_RADII  = [85, 130, 170]      # Orbitalradien
ORBIT_TILTS  = [0, 55, -55]       # Neigungswinkel (Grad)
ELEC_SPEEDS  = [1.8, 1.3, 1.0]   # Umdrehungen pro Sekunde
ELEC_COLORS  = [E_BLUE, E_GREEN, E_YELLOW]
ELEC_RADIUS  = 14

def orbit_pos(cx, cy, r, tilt_deg, angle):
    """Position eines Elektrons auf seiner Ellipsen-Umlaufbahn."""
    tilt = math.radians(tilt_deg)
    lx = r * math.cos(angle)
    ly = r * 0.38 * math.sin(angle)  # flache Ellipse
    rx = lx * math.cos(tilt) - ly * math.sin(tilt)
    ry = lx * math.sin(tilt) + ly * math.cos(tilt)
    return cx + rx, cy + ry

def draw_orbit(d, cx, cy, r, tilt_deg, col=(180, 200, 235)):
    """Ellipsen-Umlaufbahn zeichnen."""
    pts = []
    for i in range(120):
        a = i * 2 * math.pi / 120
        x, y = orbit_pos(cx, cy, r, tilt_deg, a)
        pts.append((x, y))
    if len(pts) >= 2:
        d.line(pts + [pts[0]], fill=col, width=2)

def draw_nucleus(d, cx, cy, r=46, smile=True, wobble=0.0):
    """Kern mit Smiley."""
    wx = wobble
    # Äußerer Leuchthof
    glow(d, int(cx + wx), cy, r, RED_NUC, steps=3)
    # Kern
    circ(d, int(cx + wx), cy, r, ORG_NUC, ol=RED_NUC, olw=6)
    # Innere Highlights
    circ(d, int(cx + wx) - 10, cy - 10, r // 3, (255, 200, 170), olw=0)
    # Augen
    ex1, ex2 = int(cx + wx) - 12, int(cx + wx) + 12
    ey = cy - 10
    circ(d, ex1, ey, 7, OUTLINE, olw=0)
    circ(d, ex2, ey, 7, OUTLINE, olw=0)
    circ(d, ex1+2, ey-2, 3, WHITE, olw=0)
    circ(d, ex2+2, ey-2, 3, WHITE, olw=0)
    # Lächeln
    if smile:
        mouth_x0 = int(cx + wx) - 16
        mouth_y0 = cy + 6
        d.arc([mouth_x0, mouth_y0, mouth_x0+32, mouth_y0+20],
              start=10, end=170, fill=OUTLINE, width=4)

def draw_atom(d, cx, cy, t, n_electrons=3, excited_idx=None, excited_t=0.0,
              show_orbits=True):
    """Komplettes Atom zeichnen."""
    # Orbits
    if show_orbits:
        for i in range(n_electrons):
            ri = ORBIT_RADII[i]
            if excited_idx == i:
                ri_actual = lerp(ri, ORBIT_RADII[min(i+1, 2)], eio(excited_t))
                draw_orbit(d, cx, cy, int(ri_actual), ORBIT_TILTS[i],
                           col=(255, 255, 100))
            else:
                draw_orbit(d, cx, cy, ri, ORBIT_TILTS[i])

    # Elektronen (hinter Kern: Winkel > π)
    angles = [t * ELEC_SPEEDS[i] * 2 * math.pi for i in range(n_electrons)]

    def draw_electron(i, back=False):
        ang = angles[i]
        ri = ORBIT_RADII[i]
        if excited_idx == i:
            ri = int(lerp(ri, ORBIT_RADII[min(i+1, 2)], eio(excited_t)))
        ex, ey = orbit_pos(cx, cy, ri, ORBIT_TILTS[i], ang)
        behind = math.sin(ang - math.radians(ORBIT_TILTS[i])) < 0
        if back != behind:
            return
        er = ELEC_RADIUS
        ecol = EXCITED_C if excited_idx == i else ELEC_COLORS[i]
        if excited_idx == i and excited_t > 0.5:
            glow(d, int(ex), int(ey), er, ecol, steps=3)
        circ(d, int(ex), int(ey), er, ecol, ol=OUTLINE, olw=3)
        circ(d, int(ex)-4, int(ey)-4, 4, WHITE, olw=0)

    for i in range(n_electrons):
        draw_electron(i, back=True)

    wobble = wiggle(t, amp=3, freq=2)
    draw_nucleus(d, cx, cy, wobble=wobble)

    for i in range(n_electrons):
        draw_electron(i, back=False)

# ─── SPEZIALOBJEKTE ───────────────────────────────────────────────────────────
def draw_photon_ball(d, cx, cy, r=22, phase=0.0, color=PHOTON_C):
    """Leuchtendes Licht-Teilchen."""
    glow(d, int(cx), int(cy), r, color, steps=4)
    circ(d, int(cx), int(cy), r, color, ol=(200, 160, 0), olw=3)
    # Zackenkranz
    for i in range(8):
        a = phase + i * math.pi / 4
        x1 = cx + (r + 6) * math.cos(a)
        y1 = cy + (r + 6) * math.sin(a)
        x2 = cx + (r + 14) * math.cos(a)
        y2 = cy + (r + 14) * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=(255, 210, 0), width=4)

def draw_energy_arrow(d, x0, y0, x1, y1, col=(255, 220, 50)):
    """Pfeil für Energie."""
    d.line([(x0, y0), (x1, y1)], fill=col, width=6)
    # Pfeilspitze
    angle = math.atan2(y1 - y0, x1 - x0)
    for a in [angle + 2.4, angle - 2.4]:
        d.line([(x1, y1), (x1 - 22 * math.cos(a), y1 - 22 * math.sin(a))],
               fill=col, width=6)

def draw_laser_beam(d, x0, y, x1, width=18, col=LASER_V, t=0.0):
    """Laser-Strahl mit Leuchten."""
    # Schein-Ebenen
    for w, alpha_factor in [(width + 30, 0.15), (width + 16, 0.3),
                             (width + 6, 0.6), (width, 1.0)]:
        c = lerpc(col, (255, 255, 255), 1 - alpha_factor)
        d.line([(x0, y), (x1, y)], fill=c, width=w)
    # Animierte Punkte im Strahl
    for i in range(10):
        px = x0 + (i + t * 3) % 1.0 * (x1 - x0)
        circ(d, int(px), y, 5, WHITE, olw=0)

def draw_lightning(d, cx, cy):
    """Blitz-Symbol."""
    pts = [(cx, cy-25), (cx+10, cy-5), (cx+3, cy-5),
           (cx+15, cy+25), (cx-5, cy+5), (cx+3, cy+5), (cx, cy-25)]
    d.polygon(pts, fill=(255, 240, 0), outline=OUTLINE, width=2)

def draw_sparkles(d, cx, cy, t, n=5, r=40):
    """Glitzerpunkte um einen Mittelpunkt."""
    for i in range(n):
        angle = t * 2 + i * 2 * math.pi / n
        sx = cx + r * math.cos(angle)
        sy = cy + r * math.sin(angle)
        scale = 0.5 + 0.5 * math.sin(t * 4 + i)
        rs = int(6 * scale)
        if rs > 0:
            circ(d, int(sx), int(sy), rs, PHOTON_C, ol=(200,160,0), olw=2)

# ─── TITLE-KARTE ─────────────────────────────────────────────────────────────
def scene_title_card(d, img, t, title, subtitle="", bg_top=BG_SKY,
                     bg_bot=BG_SUN):
    """Volle Titel-Karte."""
    gradient_bg(img, bg_top, bg_bot)
    alpha = min(1.0, t * 4)

    # Rahmen
    bw, bh = 900, 180
    cx, cy = W // 2, H // 2 - 30
    x0, y0 = cx - bw//2, cy - bh//2
    rounded_rect(d, x0, y0, x0+bw, y0+bh, 40, (255, 255, 220),
                 ol=(200, 80, 20), olw=8)

    # Titel
    fill = lerpc(bg_top, TITLE_R, alpha)
    ctext(d, title, cx, cy, FT_BIG, fill=TITLE_R)

    if subtitle:
        ctext(d, subtitle, cx, cy + 120, FT_MED, fill=TXT_DARK)

    # Sterne-Dekoration
    for i in range(6):
        a = t * 0.5 + i * math.pi / 3
        sx = cx + 460 * math.cos(a * 0.3 + i)
        sy = cy + 100 * math.sin(a * 0.5 + i * 0.7)
        star(d, int(sx) % W, int(sy + H//2) % H, 16, 7, 5,
             t + i, PHOTON_C, olw=2)

# ─── SZENENGENERATOREN ────────────────────────────────────────────────────────
def frames_intro(total_frames):
    """Intro-Titel."""
    for f in range(total_frames):
        t = f / total_frames
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        gradient_bg(img, BG_SKY, BG_SUN)

        # Animierter Hintergrund-Sterne
        for i in range(8):
            a = f / FPS * 0.4 + i * 0.8
            sx = int(W * 0.1 + (W * 0.8) * (i / 8))
            sy = int(H * 0.15 + H * 0.1 * math.sin(a + i))
            star(d, sx, sy, 20, 8, 5, a, PHOTON_C, olw=2)

        # Haupt-Box
        alpha = min(1.0, t * 3)
        bw, bh = 1000, 300
        cx, cy = W//2, H//2
        rounded_rect(d, cx-bw//2, cy-bh//2, cx+bw//2, cy+bh//2, 50,
                     (255, 250, 230), ol=(200, 70, 20), olw=10)

        # Bär-Emoji-Ersatz: Großer Kreis mit Ohren
        bx, by = 160, cy - 90
        circ(d, bx-35, by-35, 28, (180, 130, 90), ol=OUTLINE, olw=4)
        circ(d, bx+35, by-35, 28, (180, 130, 90), ol=OUTLINE, olw=4)
        circ(d, bx, by, 55, (210, 160, 110), ol=OUTLINE, olw=5)
        circ(d, bx-14, by-10, 10, OUTLINE, olw=0)
        circ(d, bx+14, by-10, 10, OUTLINE, olw=0)
        circ(d, bx-11, by-12, 4, WHITE, olw=0)
        circ(d, bx+11+3, by-12, 4, WHITE, olw=0)
        d.arc([bx-18, by+5, bx+18, by+25], start=5, end=175,
              fill=OUTLINE, width=4)
        circ(d, bx, by+2, 12, (230, 180, 140), ol=OUTLINE, olw=3)

        # Titel-Text
        ctext(d, "ErklaerBaer", cx + 50, cy - 50, FT_BIG, fill=TITLE_R)
        ctext(d, "Atome und Laser", cx + 50, cy + 30, FT_MED, fill=TXT_DARK)
        ctext(d, "Für neugierige Kinder!", cx + 50, cy + 95, FT_SML,
              fill=(100, 80, 40))

        yield np.array(img)


def frames_scene1(total_frames):
    """Szene 1: Was ist ein Atom?"""
    T = total_frames

    # Phase-Grenzen (in Frames)
    P = {
        "title_in":   0,
        "title_hold": int(T * 0.07),
        "text1":      int(T * 0.13),
        "build":      int(T * 0.22),
        "orbit":      int(T * 0.45),
        "text2":      int(T * 0.72),
        "text3":      int(T * 0.87),
    }

    for f in range(T):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        t_sec = f / FPS
        gradient_bg(img, BG_SKY, (230, 255, 230))

        # Dekoratives Muster oben
        for i in range(20):
            x = i * 65 + 30
            y_pos = 30 + 10 * math.sin(t_sec + i * 0.4)
            circ(d, x, int(y_pos), 12, (180, 220, 255), olw=0)
        for i in range(20):
            x = i * 65 + 60
            y_pos = H - 30 - 10 * math.sin(t_sec + i * 0.4 + 1)
            circ(d, x, int(y_pos), 12, (180, 255, 200), olw=0)

        cx, cy = W // 2, H // 2 - 20

        if f < P["title_hold"]:
            # === Titel-Karte ===
            alpha = min(1.0, f / max(1, P["title_hold"] * 0.4))
            rounded_rect(d, cx-480, cy-70, cx+480, cy+70, 40,
                         (255, 250, 220), ol=(200, 70, 20), olw=8)
            ctext(d, "Was ist ein Atom?", cx, cy, FT_BIG, fill=TITLE_R)

        elif f < P["build"]:
            # === Text + kleine Welt-Partikel ===
            tt = (f - P["title_hold"]) / max(1, P["build"] - P["title_hold"])
            # Viele kleine Punkte fliegen zusammen
            np.random.seed(42)
            n_parts = 40
            for i in range(n_parts):
                rx = np.random.uniform(-1, 1)
                ry = np.random.uniform(-1, 1)
                start_x = cx + rx * 450 * (1 - eio(tt))
                start_y = cy + ry * 250 * (1 - eio(tt))
                c_i = [E_BLUE, E_GREEN, E_YELLOW, RED_NUC][i % 4]
                circ(d, int(start_x), int(start_y), 8, c_i,
                     ol=OUTLINE, olw=2)

            speech_bubble(d, cx, cy - 180, 820, 110,
                          "Alles um uns herum besteht aus", FT_MED)
            ctext(d, "winzigen Teilchen …", cx, cy - 95, FT_MED,
                  fill=TITLE_R)

        elif f < P["text2"]:
            # === Atom aufbauen + animieren ===
            build_f = f - P["build"]
            build_T = P["orbit"] - P["build"]

            n_e = 0
            build_t = 0.0
            if f < P["orbit"]:
                prog = build_f / max(1, build_T)
                # Kern erscheint in erstem Drittel
                nuc_t = clamp((prog - 0.0) / 0.3)
                if nuc_t > 0:
                    # Kern wächst
                    r_nuc = int(46 * eo(nuc_t))
                    glow(d, cx, cy, r_nuc, RED_NUC, steps=3)
                    circ(d, cx, cy, r_nuc, ORG_NUC, ol=RED_NUC, olw=6)
                    if nuc_t > 0.8:
                        draw_nucleus(d, cx, cy, wobble=0)

                # Elektronen erscheinen
                for i in range(3):
                    e_start = 0.3 + i * 0.2
                    et = clamp((prog - e_start) / 0.2)
                    if et > 0:
                        draw_orbit(d, cx, cy, ORBIT_RADII[i], ORBIT_TILTS[i])
                        ang = t_sec * ELEC_SPEEDS[i] * 2 * math.pi
                        ex, ey = orbit_pos(cx, cy, ORBIT_RADII[i],
                                           ORBIT_TILTS[i], ang)
                        er = int(ELEC_RADIUS * eo(et))
                        circ(d, int(ex), int(ey), er, ELEC_COLORS[i],
                             ol=OUTLINE, olw=3)
                n_e = 3
            else:
                # Normales Atom
                draw_atom(d, cx, cy, t_sec, n_electrons=3)

            # Erklärungstext
            if f >= P["orbit"]:
                speech_bubble(d, cx, cy + 230, 860, 120,
                              "Das nennen wir ein ATOM!", FT_MED,
                              tail="down")

        else:
            # === Atom + Info-Text ===
            draw_atom(d, cx, cy - 40, t_sec, n_electrons=3)
            if f < P["text3"]:
                speech_bubble(d, cx, cy + 200, 1050, 120,
                              "Atome sind viiiiiel kleiner als ein Sandkorn!",
                              FT_MED)
            else:
                speech_bubble(d, cx, cy + 200, 980, 140,
                              "Alles besteht aus Atomen – du auch! :-)",
                              FT_MED)

        yield np.array(img)


def frames_scene2(total_frames):
    """Szene 2: Elektron wird aufgeregt."""
    T = total_frames
    P = {
        "title":   int(T * 0.0),
        "arrow":   int(T * 0.18),
        "photon":  int(T * 0.30),
        "jump":    int(T * 0.52),
        "text":    int(T * 0.72),
    }

    for f in range(T):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        t_sec = f / FPS
        gradient_bg(img, (220, 245, 255), BG_SUN)

        cx, cy = W // 2, H // 2 - 10

        if f < P["arrow"]:
            # Titel
            rounded_rect(d, cx-560, cy-70, cx+560, cy+70, 40,
                         (255, 250, 220), ol=(200, 70, 20), olw=8)
            ctext(d, "Was passiert mit Licht?", cx, cy, FT_BIG, fill=TITLE_R)

        elif f < P["photon"]:
            # Atom + Energiepfeil kommt von links
            draw_atom(d, cx, cy, t_sec)
            prog = (f - P["arrow"]) / max(1, P["photon"] - P["arrow"])
            px = int(lerp(100, cx - 220, eo(prog)))
            py = cy - 50
            draw_photon_ball(d, px, py, phase=t_sec * 3)
            draw_energy_arrow(d, 100, py, px - 30, py)

            speech_bubble(d, cx, cy + 220, 900, 110,
                          "Ein Licht-Teilchen fliegt auf das Atom zu ...",
                          FT_SML, tail="down")

        elif f < P["jump"]:
            # Photon trifft auf Elektron → Elektron springt hoch
            prog = (f - P["photon"]) / max(1, P["jump"] - P["photon"])
            jump_t = eio(prog)

            draw_atom(d, cx, cy, t_sec, excited_idx=0, excited_t=jump_t)

            # Photon wird kleiner (wird absorbiert)
            if prog < 0.5:
                abs_t = prog / 0.5
                px = int(lerp(cx - 220, cx - 100, eo(abs_t)))
                pr = int(22 * (1 - abs_t))
                if pr > 2:
                    draw_photon_ball(d, px, cy - 50, r=pr, phase=t_sec*3)

            # Flash-Effekt beim Aufprall
            if 0.4 < prog < 0.65:
                flash_t = (prog - 0.4) / 0.25
                fr = int(60 * math.sin(flash_t * math.pi))
                if fr > 0:
                    glow(d, cx, cy, fr, (255, 255, 150), steps=2)

            draw_lightning(d, cx + 80, cy - 110)
            draw_sparkles(d, cx, cy, t_sec, n=4, r=int(30 + 60 * jump_t))

            speech_bubble(d, cx, cy + 220, 900, 110,
                          "Das Elektron springt auf einen weiter entfernten Ring!",
                          FT_SML, tail="down")

        else:
            # Elektron oben – aufgeregt
            prog = (f - P["jump"]) / max(1, T - P["jump"])
            draw_atom(d, cx, cy, t_sec, excited_idx=0, excited_t=1.0)
            draw_sparkles(d, cx, cy - 80, t_sec, n=6, r=40)

            speech_bubble(d, cx, cy + 210, 920, 120,
                          "Das Elektron hat Energie aufgenommen! Es ist aufgeregt! :-D",
                          FT_SML, tail="down")

        yield np.array(img)


def frames_scene3(total_frames):
    """Szene 3: Elektron fällt zurück, Photon wird emittiert."""
    T = total_frames
    P = {
        "title":  int(T * 0.0),
        "hold":   int(T * 0.18),
        "fall":   int(T * 0.30),
        "emit":   int(T * 0.52),
        "text":   int(T * 0.72),
    }

    for f in range(T):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        t_sec = f / FPS
        gradient_bg(img, (240, 220, 255), (255, 248, 200))

        cx, cy = W // 2, H // 2 - 10

        if f < P["hold"]:
            # Titel
            rounded_rect(d, cx-600, cy-70, cx+600, cy+70, 40,
                         (255, 250, 220), ol=(200, 70, 20), olw=8)
            ctext(d, "Und dann ...", cx, cy, FT_BIG, fill=TITLE_R)

        elif f < P["fall"]:
            # Atom mit aufgeregtem Elektron
            draw_atom(d, cx, cy, t_sec, excited_idx=0, excited_t=1.0)
            draw_sparkles(d, cx, cy - 80, t_sec, n=6, r=40)
            speech_bubble(d, cx, cy + 220, 860, 110,
                          "Das Elektron ist noch ganz oben ...", FT_SML)

        elif f < P["emit"]:
            # Elektron fällt zurück
            prog = (f - P["fall"]) / max(1, P["emit"] - P["fall"])
            fall_t = eio(prog)
            excited_t = 1.0 - fall_t  # Fällt von 1→0

            draw_atom(d, cx, cy, t_sec, excited_idx=0, excited_t=excited_t)

            # Photon entsteht und fliegt weg
            if prog > 0.4:
                emit_t = (prog - 0.4) / 0.6
                px = int(cx + lerp(80, 420, eo(emit_t)))
                py = cy - 60
                draw_photon_ball(d, px, py, phase=t_sec * 4, color=PHOTON_C)
                if emit_t > 0.2:
                    draw_energy_arrow(d, cx + 80, py, px - 30, py,
                                      col=(255, 200, 0))

            # Flash beim Fallen
            if 0.35 < prog < 0.55:
                flash_t = (prog - 0.35) / 0.2
                fr = int(50 * math.sin(flash_t * math.pi))
                if fr > 0:
                    glow(d, cx, cy, fr, PHOTON_C, steps=2)

            speech_bubble(d, cx, cy + 220, 880, 110,
                          "Das Elektron fällt zurück ... und sendet Licht aus!",
                          FT_SML)

        else:
            # Normales Atom + fliegendes Photon
            prog = (f - P["emit"]) / max(1, T - P["emit"])
            draw_atom(d, cx, cy, t_sec)

            px = int(cx + 420 + 180 * eo(prog))
            py = cy - 60
            if px < W + 50:
                draw_photon_ball(d, px, py, phase=t_sec * 4)
                # Spur
                for i in range(5):
                    tx = px - 25 - i * 18
                    if tx > cx + 80:
                        circ(d, tx, py, int(8 - i), (255, 240, 100), olw=0)

            speech_bubble(d, cx, cy + 210, 960, 130,
                          "Das Licht-Teilchen heißt PHOTON! Jedes Atom macht das!",
                          FT_SML)

        yield np.array(img)


def frames_scene4(total_frames):
    """Szene 4: Der Laser."""
    T = total_frames
    P = {
        "title":    int(T * 0.00),
        "atoms_in": int(T * 0.18),
        "excite":   int(T * 0.38),
        "emit":     int(T * 0.58),
        "beam":     int(T * 0.76),
    }

    N_ATOMS = 5
    ATOM_CX = [int(W * 0.12 + i * W * 0.16) for i in range(N_ATOMS)]
    ATOM_CY = H // 2 - 30

    for f in range(T):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        t_sec = f / FPS
        gradient_bg(img, (255, 240, 255), (200, 235, 255))

        cx = W // 2

        if f < P["atoms_in"]:
            # Titel
            rounded_rect(d, cx-480, ATOM_CY-70, cx+480, ATOM_CY+70, 40,
                         (255, 250, 220), ol=(200, 70, 20), olw=8)
            ctext(d, "Was ist ein LASER?", cx, ATOM_CY, FT_BIG, fill=TITLE_R)

        elif f < P["excite"]:
            # Viele Atome erscheinen
            prog = (f - P["atoms_in"]) / max(1, P["excite"] - P["atoms_in"])
            for i, acx in enumerate(ATOM_CX):
                at = clamp((prog - i * 0.12) / 0.25)
                if at > 0:
                    scale = eo(at)
                    # Mini-Atom (skaliert durch Orbitalradius)
                    if scale > 0.5:
                        r_scale = scale
                        d.ellipse([acx - int(80*r_scale), ATOM_CY - int(80*r_scale),
                                   acx + int(80*r_scale), ATOM_CY + int(80*r_scale)],
                                  fill=None, outline=(180, 200, 240), width=2)
                    circ(d, acx, ATOM_CY, int(28 * eo(at)), ORG_NUC,
                         ol=RED_NUC, olw=4)

            speech_bubble(d, cx, ATOM_CY + 200, 900, 110,
                          "Wir nehmen ganz viele Atome zusammen!", FT_SML)

        elif f < P["emit"]:
            # Alle aufgeregt
            prog = (f - P["excite"]) / max(1, P["emit"] - P["excite"])
            for i, acx in enumerate(ATOM_CX):
                delay = i * 0.08
                et = clamp((prog - delay) / 0.3)
                draw_atom(d, acx, ATOM_CY, t_sec + i * 0.7,
                          n_electrons=1, excited_idx=0, excited_t=et)
                if et > 0.7:
                    draw_sparkles(d, acx, ATOM_CY, t_sec + i, n=3, r=25)

            speech_bubble(d, cx, ATOM_CY + 195, 900, 110,
                          "Jetzt werden alle Elektronen gleichzeitig aufgeregt!",
                          FT_SML)

        elif f < P["beam"]:
            # Alle emittieren Photonen
            prog = (f - P["emit"]) / max(1, P["beam"] - P["emit"])
            for i, acx in enumerate(ATOM_CX):
                draw_atom(d, acx, ATOM_CY, t_sec + i * 0.7,
                          n_electrons=1, excited_idx=0, excited_t=0.0)
                # Photon fliegt nach rechts
                delay = i * 0.06
                pt = clamp((prog - delay) / 0.7)
                if pt > 0:
                    px = int(acx + lerp(0, W * 0.7, eo(pt)))
                    if px < W - 20:
                        draw_photon_ball(d, px, ATOM_CY, r=14,
                                         phase=t_sec * 5 + i, color=PHOTON_C)

            speech_bubble(d, cx, ATOM_CY + 195, 880, 110,
                          "Alle senden gleichzeitig ein Photon aus!", FT_SML)

        else:
            # Laser-Strahl
            prog = (f - P["beam"]) / max(1, T - P["beam"])
            for i, acx in enumerate(ATOM_CX):
                draw_atom(d, acx, ATOM_CY, t_sec + i * 0.7, n_electrons=1)

            beam_x = int(lerp(ATOM_CX[0] + 80, W - 30, eo(prog)))
            draw_laser_beam(d, ATOM_CX[0] + 60, ATOM_CY,
                            beam_x, width=22, col=LASER_V, t=t_sec)

            # "LASER!"-Beschriftung am Strahl
            if prog > 0.4:
                ctext(d, "LASER!", int(W - 120), ATOM_CY - 45,
                      FT_MED, fill=LASER_V)

            speech_bubble(d, cx, ATOM_CY + 190, 960, 130,
                          "Die Photonen vereinen sich zu einem super starken Lichtstrahl!",
                          FT_SML)

        yield np.array(img)


def frames_outro(total_frames):
    """Outro / Abschluss."""
    for f in range(total_frames):
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        t_sec = f / FPS
        gradient_bg(img, BG_SUN, (255, 220, 200))

        cx, cy = W // 2, H // 2 - 20

        # Sterne rundherum
        for i in range(12):
            a = t_sec * 0.3 + i * math.pi / 6
            rx = cx + 450 * math.cos(a * 0.4 + i * 0.3)
            ry = cy + 200 * math.sin(a * 0.6 + i * 0.2)
            star(d, int(rx) % W, int(ry + H//2) % H, 22, 9, 5, a, PHOTON_C)

        # Haupt-Box
        rounded_rect(d, cx-580, cy-160, cx+580, cy+160, 50,
                     (255, 255, 230), ol=(200, 80, 20), olw=10)

        ctext(d, "Super gemacht!", cx, cy - 70, FT_BIG, fill=TITLE_R)
        ctext(d, "Du weißt jetzt, wie ein Laser funktioniert!", cx, cy + 10,
              FT_MED, fill=TXT_DARK)
        ctext(d, "Atome · Elektronen · Photonen · Laser", cx, cy + 75,
              FT_SML, fill=(120, 90, 50))

        # Animiertes Mini-Atom rechts
        ax, ay = cx + 400, cy - 30
        draw_atom(d, ax, ay, t_sec, n_electrons=2)

        # Laserstrahle diagonal
        lt = (t_sec * 0.2) % 1.0
        lx = int(lerp(-100, W + 100, lt))
        d.line([(lx - 80, H - 60), (lx + 80, H - 60)],
               fill=LASER_V, width=10)
        d.line([(lx - 50, H - 40), (lx + 50, H - 40)],
               fill=PHOTON_C, width=6)

        yield np.array(img)


# ─── ÜBERBLENDEN ──────────────────────────────────────────────────────────────
def frames_fade(total_frames, col=(255, 255, 255)):
    """Weiß-Überblendung."""
    half = total_frames // 2
    for f in range(total_frames):
        img = Image.new("RGB", (W, H), col)
        yield np.array(img)


# ─── HAUPTPROGRAMM ────────────────────────────────────────────────────────────
def main():
    out_path = OUTPUT

    # Sequenz definieren: (Generator-Funktion, Dauer in Sekunden)
    SEQUENCE = [
        (frames_intro,    4),
        (frames_scene1,  40),
        (frames_fade,     2),
        (frames_scene2,  35),
        (frames_fade,     2),
        (frames_scene3,  35),
        (frames_fade,     2),
        (frames_scene4,  40),
        (frames_fade,     2),
        (frames_outro,    8),
    ]

    total_secs = sum(d for _, d in SEQUENCE)
    total_frames = sum(int(d * FPS) for _, d in SEQUENCE)

    print(f"Video: {W}x{H} @ {FPS}fps")
    print(f"Dauer: {total_secs}s = {total_frames} Frames")
    print(f"Ausgabe: {out_path}")

    writer = imageio.get_writer(
        out_path,
        fps=FPS,
        quality=8,
        output_params=["-pix_fmt", "yuv420p"],
    )

    frame_count = 0
    for gen_fn, dur_secs in SEQUENCE:
        n = int(dur_secs * FPS)
        label = gen_fn.__name__.replace("frames_", "")
        print(f"  Rendere {label} ({n} Frames) ...", end="", flush=True)
        for frame in gen_fn(n):
            writer.append_data(frame)
            frame_count += 1
        pct = 100 * frame_count // total_frames
        print(f" fertig ({pct}%)")

    writer.close()
    print(f"\nVideo gespeichert: {out_path}")
    import os
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Dateigröße: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
