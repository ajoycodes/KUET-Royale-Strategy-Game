#!/usr/bin/env python3
"""Big game lettering: chunky letters of carved silver and gold, with wide bevels, a thick dark edge and solid depth.

Each letter is lit by itself from a height map, so its chamfers catch the light on the top left and fall dark on the bottom right.
    python3 tools/lettering.py [font] [names]
Every picture is cropped evenly round the ink, so its centre is the centre of the letters.
"""
import json
import os
import random
import sys

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "..", "work", "sheets") + "/"
OUT = os.path.join(HERE, "..", "public", "text") + "/"
SCALE = 2           # picture pixels for each pixel of the film
CELL = 640
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ."
LINE_ROW = 240
LINE_SIZE = 150
LINES = ["Fast, cheap and clever.", "Heavy, slow and hard to stop.", "A sturdy wall that soaks up hits.", "And when it falls, everyone near it pays.",
         "One tank. One shooter. One runner. One surprise.", "One minute. No turns.", "Choose your side.", "Armour", "Splash", "Last blast", "Hover"]
INK = np.array([11, 9, 15], dtype=np.float32) / 255


def colour(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255


def ramp(stops):
    return np.array([s[0] for s in stops], dtype=np.float32), np.stack([colour(s[1]) for s in stops])


METALS = {
    "steel": dict(face=ramp([(0, "#fbfcfd"), (.22, "#e6e9ee"), (.45, "#b6bdc8"), (.5, "#818b98"), (.55, "#d0d5dc"), (.8, "#aeb5c0"), (1, "#737c88")]), near="#646c78", far="#23272e"),
    "gold": dict(face=ramp([(0, "#fff6bd"), (.2, "#ffdc66"), (.45, "#f2a828"), (.5, "#c77011"), (.56, "#ffc848"), (.8, "#e88f1a"), (1, "#9e530c")]), near="#96530f", far="#3a1a05"),
    "ice": dict(face=ramp([(0, "#f6fcff"), (.22, "#d4e9fc"), (.45, "#84b4e8"), (.5, "#3f72b8"), (.55, "#add1f6"), (.8, "#72a4de"), (1, "#2f5a99")]), near="#34588c", far="#101f3a"),
    "ember": dict(face=ramp([(0, "#ffeccf"), (.2, "#ffc07c"), (.45, "#ea742c"), (.5, "#a8410f"), (.56, "#ff9e54"), (.8, "#da631f"), (1, "#80300a")]), near="#7f320d", far="#2e1004"),
    "cream": dict(face=ramp([(0, "#ffffff"), (.5, "#fff3d6"), (1, "#e7cc9c")]), near="#6d5a3c", far="#2a2115"),
}


class Font:
    def __init__(self, name):
        sheet = np.asarray(Image.open(SHEETS + name + ".png").convert("L")).astype(np.float32) / 255
        self.glyph = {}
        for place, char in enumerate(CHARS):
            x, y = (place % 6) * CELL, (place // 6) * CELL
            self.glyph[char] = sheet[y:y + CELL, x:x + CELL]
        h = np.where(self.glyph["H"].max(axis=1) > 0.5)[0]
        self.cap_top, self.base = int(h[0]), int(h[-1]) + 1
        self.cap = self.base - self.cap_top


LINE_SHEET = None


def line_mask(text):
    global LINE_SHEET
    if LINE_SHEET is None:
        LINE_SHEET = np.asarray(Image.open(SHEETS + "lines.png").convert("L")).astype(np.float32) / 255
    row = LINES.index(text)
    return LINE_SHEET[row * LINE_ROW:(row + 1) * LINE_ROW]


def texture(shape, seed):
    rng = np.random.default_rng(seed)
    soft = cv2.resize(rng.random((max(2, shape[0] // 28), max(2, shape[1] // 28)), dtype=np.float32), (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    brushed = cv2.resize(rng.random((max(2, shape[0] // 3), max(2, shape[1] // 60)), dtype=np.float32), (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
    return (soft - 0.5) * 0.11 + (brushed - 0.5) * 0.03


def forge_piece(mask, cap, metal, seed, depth=0.105, bevel=0.095, edge=0.056, slant=0.12):
    """One letter, or one line of small words, as colour and alpha. cap is the letter height in picture pixels."""
    m = METALS[metal]
    B, O, E = max(1.5, cap * bevel), max(2.0, cap * edge), int(round(cap * depth))
    Ex = int(round(E * 0.26))
    pad = int(O + E + 6)
    mask = cv2.copyMakeBorder(mask, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    h, w = mask.shape
    solid = mask > 0.5
    # A height map: flat on top, falling away on a chamfer at every edge.
    d = np.clip((ndi.distance_transform_edt(solid).astype(np.float32) - 0.5 + (mask - 0.5) * solid) / B, 0, 1)
    height = cv2.GaussianBlur((1 - (1 - d) ** 1.25).astype(np.float32), (0, 0), max(0.7, cap * 0.0042))
    gy, gx = np.gradient(height * B)
    nz = np.full_like(gx, 0.62)
    length = np.sqrt(gx * gx + gy * gy + nz * nz)
    nx, ny, nz = -gx / length, -gy / length, nz / length
    L = np.array([-0.46, -0.78, 0.5], dtype=np.float32)
    L /= np.linalg.norm(L)
    diffuse = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    half = L + np.array([0, 0, 1], dtype=np.float32)
    half /= np.linalg.norm(half)
    shine = np.clip(nx * half[0] + ny * half[1] + nz * half[2], 0, 1) ** 40
    # The metal's colour by height on the letter, slanted, with a wavering line where it reflects the horizon.
    ys = np.where(solid.any(axis=1))[0]
    top, bottom = (ys[0], ys[-1]) if len(ys) else (0, h - 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    tex = texture((h, w), seed)
    t = (yy - top) / max(1, bottom - top) - (xx - w / 2) / max(1, cap) * slant * 0.5 + tex * 0.16
    stops, values = m["face"]
    face = np.stack([np.interp(t, stops, values[:, k]) for k in range(3)], axis=2).astype(np.float32)
    flat = 0.32 + 1.3 * L[2]
    light = (0.32 + 1.3 * diffuse) / flat
    face = face * light[..., None] * (1 + tex[..., None]) + shine[..., None] * 0.55
    # A soft dark line where the chamfer meets the flat top makes the bevel read as cut.
    crease = np.exp(-((d - 1.0) / 0.1) ** 2) * (d < 0.999)
    face *= (1 - 0.14 * crease)[..., None]
    face = np.clip(face, 0, 1)
    # Depth: the letter pushed down and a little to the right, lit near the face and dark further off.
    side = np.zeros((h, w, 3), dtype=np.float32)
    side_a = np.zeros((h, w), dtype=np.float32)
    near, far = colour(m["near"]), colour(m["far"])
    for k in range(E, 0, -1):
        M = np.array([[1, 0, Ex * k / max(E, 1)], [0, 1, k]], dtype=np.float32)
        shifted = cv2.warpAffine(mask, M, (w, h), flags=cv2.INTER_LINEAR)
        tone = near * (1 - k / E) + far * (k / E)
        side = side * (1 - shifted[..., None]) + tone * shifted[..., None]
        side_a = np.maximum(side_a, shifted)
    union = np.maximum(mask, side_a)
    out_d = ndi.distance_transform_edt(union < 0.5).astype(np.float32)
    contour = np.clip(O - out_d + 0.5, 0, 1)
    # Paint: the dark edge, then the depth, then the face.
    rgb = np.empty((h, w, 3), dtype=np.float32)
    rgb[:] = INK
    rgb = rgb * (1 - side_a[..., None]) + side * side_a[..., None]
    rgb = rgb * (1 - mask[..., None]) + face * mask[..., None]
    alpha = np.maximum(contour, union)
    return rgb, alpha, mask, pad


def transformed(glyph, scale, angle):
    """A letter at its size and tilt, on a canvas where its baseline and centre stay put."""
    size = int(round(CELL * scale))
    small = cv2.resize(glyph, (size, size), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    if angle:
        R = cv2.getRotationMatrix2D((size / 2, size / 2), angle, 1.0)
        small = cv2.warpAffine(small, R, (size, size), flags=cv2.INTER_CUBIC)
    return small


class Canvas:
    """Letters laid over one another; remembers which pixels are still bare metal, for the band of light."""

    def __init__(self, w, h):
        self.rgb = np.zeros((h, w, 3), dtype=np.float32)
        self.a = np.zeros((h, w), dtype=np.float32)
        self.bare = np.zeros((h, w), dtype=np.float32)

    def put(self, rgb, alpha, face, x, y):
        H, W = self.a.shape
        h, w = alpha.shape
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
        if x0 >= x1 or y0 >= y1:
            return
        c = rgb[y0 - y:y1 - y, x0 - x:x1 - x]
        a = alpha[y0 - y:y1 - y, x0 - x:x1 - x]
        f = face[y0 - y:y1 - y, x0 - x:x1 - x]
        under = self.a[y0:y1, x0:x1]
        out = a + under * (1 - a)
        self.rgb[y0:y1, x0:x1] = (c * a[..., None] + self.rgb[y0:y1, x0:x1] * (under * (1 - a))[..., None]) / np.maximum(out[..., None], 1e-4)
        self.a[y0:y1, x0:x1] = out
        self.bare[y0:y1, x0:x1] = self.bare[y0:y1, x0:x1] * (1 - a) + f


def word(font, text, metal, cap_film, seed=1, gap=0.012, arc=0.0, tilt=0.0, wobble=1.0, spacing=None):
    """One word on its own canvas: per-letter tilt and size, an optional arch, and letters set tight by their shapes."""
    r = random.Random(seed)
    cap = cap_film * SCALE
    scale0 = cap / font.cap
    pieces = []
    n = len(text)
    for place, char in enumerate(text):
        k = (place - (n - 1) / 2) / max(1, (n - 1) / 2)
        bulge = 1 + arc * 0.32 * (1 - k * k) if arc else 1.0
        s = scale0 * bulge * (1 + r.uniform(-0.016, 0.016) * wobble)
        angle = tilt + (-k * arc * 11) + r.uniform(-1.3, 1.3) * wobble
        lift = -(1 - k * k) * arc * cap * 0.34 + r.uniform(-0.012, 0.012) * cap * wobble
        glyph = transformed(font.glyph[char], s, angle)
        cols = np.where(glyph.max(axis=0) > 0.5)[0]
        glyph = glyph[:, cols[0]:cols[-1] + 1]
        pieces.append(dict(mask=glyph, size=int(round(CELL * s)), lift=lift, char=char, base=font.base * s))
    # Set them tight: each letter moves left until its nearest edge comes within a fixed distance of the one before.
    target = cap * (0.1 + gap)
    xs = [0]
    for a, b in zip(pieces, pieces[1:]):
        rows = int(cap * 3)
        right = np.full(rows, -1e6)
        left = np.full(rows, 1e6)
        for piece, side in ((a, right), (b, left)):
            offset = int(piece["lift"] - piece["base"] + cap * 2)
            for row in np.where(piece["mask"].max(axis=1) > 0.5)[0]:
                if 0 <= row + offset < rows:
                    cols = np.where(piece["mask"][row] > 0.5)[0]
                    side[row + offset] = cols[-1] if side is right else cols[0]
        # Nearby rows count too, so that shapes do not slide into each other.
        near = ndi.maximum_filter1d(right, int(cap * 0.08) * 2 + 1)
        both = (near > -1e5) & (left < 1e5)
        wide = a["mask"].shape[1]
        # How far the next letter's left edge is from this letter's right edge, if their boxes were to touch.
        slack = float(np.min(wide - near[both] + left[both])) if both.any() else 0.0
        # Never nest by more than a fifth of the letter height, so that A and Y do not collide.
        slack = min(slack, cap * 0.2)
        xs.append(xs[-1] + wide + target - slack)
    return pieces, xs, cap


def forge(rows, depth=0.105, bevel=0.095, edge=0.056, gapscale=0.34, shadow=1.0):
    """Lays out one or more rows, each made of words of chosen metals, and lights every letter."""
    placed = []
    y_cursor = 0.0
    for place, row in enumerate(rows):
        x = 0.0
        row_cap = max(w["cap"] for w in row["words"])
        for part in row["words"]:
            for piece, px in zip(part["pieces"], part["xs"]):
                placed.append(dict(piece=piece, x=x + px, row_y=y_cursor + row.get("nudge", 0) * SCALE, metal=part["metal"], cap=part["cap"], seed=part["seed"]))
            last = part["pieces"][-1]["mask"].shape[1]
            x += part["xs"][-1] + last + row_cap * gapscale
        row["width"] = x - row_cap * gapscale
        row["start"] = len(placed)
        if place + 1 < len(rows):
            # The next row's letters just overlap the foot of this row.
            next_cap = max(w["cap"] for w in rows[place + 1]["words"])
            y_cursor += next_cap + row_cap * row.get("depth_gap", 0.04)
    # Centre each row on the same line.
    i = 0
    widest = max(r["width"] for r in rows)
    for row in rows:
        shift = (widest - row["width"]) / 2
        while i < row["start"]:
            placed[i]["x"] += shift
            i += 1
    biggest = max(p["cap"] for p in placed)
    margin = int(biggest * 0.9) + 60
    W = int(widest) + margin * 2
    H = int(y_cursor + biggest * 2.4) + margin * 2
    canvas = Canvas(W, H)
    for k, p in enumerate(placed):
        piece = p["piece"]
        rgb, alpha, face, pad = forge_piece(piece["mask"], p["cap"], p["metal"], p["seed"] + k, depth=depth, bevel=bevel, edge=edge)
        px = int(round(margin + p["x"])) - pad
        py = int(round(margin + biggest + p["row_y"] + piece["lift"] - piece["base"])) - pad
        canvas.put(rgb, alpha, face, px, py)
    return finish(canvas, shadow)


def finish(canvas, shadow):
    ys, xs = np.where(canvas.a > 0.5)
    left, right, top, bottom = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    cx, cy = (left + right) / 2, (top + bottom) / 2
    margin = int(max(40, (bottom - top) * 0.32))
    half_w, half_h = (right - left) / 2 + margin, (bottom - top) / 2 + margin
    # An even crop round the ink, so that the middle of the picture is the middle of the letters.
    half_w, half_h = int(np.ceil(half_w)) // SCALE * SCALE + SCALE, int(np.ceil(half_h)) // SCALE * SCALE + SCALE
    x0, y0 = int(round(cx)) - half_w, int(round(cy)) - half_h
    box = lambda arr: _crop(arr, x0, y0, half_w * 2, half_h * 2)
    rgb, a, bare = box(canvas.rgb), box(canvas.a), box(canvas.bare)
    # A soft shadow to lift it off whatever is behind.
    blur = max(3.0, (bottom - top) * 0.05)
    M = np.array([[1, 0, 0], [0, 1, blur * 0.9]], dtype=np.float32)
    drop = cv2.GaussianBlur(cv2.warpAffine(a, M, (a.shape[1], a.shape[0])), (0, 0), blur) * 0.72 * shadow
    out_a = a + drop * (1 - a)
    out_rgb = (rgb * a[..., None]) / np.maximum(out_a[..., None], 1e-4)
    art = np.dstack([np.clip(out_rgb, 0, 1), np.clip(out_a, 0, 1)])
    # The face alone, brightened, for the band of light that runs across the metal.
    shine = np.dstack([np.clip(rgb * 0.5 + 0.62, 0, 1), np.clip(bare, 0, 1)])
    ink_w, ink_h = (right - left) / SCALE, (bottom - top) / SCALE
    return art, shine, dict(w=half_w * 2 / SCALE, h=half_h * 2 / SCALE, ink_w=round(ink_w, 1), ink_h=round(ink_h, 1))


def _crop(arr, x, y, w, h):
    out = np.zeros((h, w) + arr.shape[2:], dtype=arr.dtype)
    sx0, sy0 = max(x, 0), max(y, 0)
    sx1, sy1 = min(x + w, arr.shape[1]), min(y + h, arr.shape[0])
    out[sy0 - y:sy1 - y, sx0 - x:sx1 - x] = arr[sy0:sy1, sx0:sx1]
    return out


def save(name, result, table):
    art, shine, info = result
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray((art * 255 + 0.5).astype(np.uint8)).save(OUT + name + ".png", compress_level=6)
    Image.fromarray((shine * 255 + 0.5).astype(np.uint8)).save(OUT + name + "_shine.png", compress_level=6)
    table[name] = info


def small_line(text, cap_film, metal="cream"):
    """A line of small words, kept with the font's own spacing."""
    sheet = line_mask(text)
    ref = line_mask("Hover")
    cap = cap_film * SCALE
    capline = np.where(ref[:, :80 + 95].max(axis=1) > 0.5)[0]
    letter = capline[-1] + 1 - capline[0]
    s = cap / letter
    h, w = sheet.shape
    small = cv2.resize(sheet, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)
    cols = np.where(small.max(axis=0) > 0.5)[0]
    rows = np.where(small.max(axis=1) > 0.5)[0]
    small = small[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    rgb, alpha, face, pad = forge_piece(small, cap, metal, 5, depth=0.075, bevel=0.1, edge=0.11, slant=0)
    pad2 = 60
    canvas = Canvas(alpha.shape[1] + pad2 * 2, alpha.shape[0] + pad2 * 2)
    canvas.put(rgb, alpha, face, pad2, pad2)
    return finish(canvas, 0.9)


def caption(font, spec):
    """spec: rows of [(text, metal, cap)], plus keywords for the row and the arch."""
    rows = []
    for k, row in enumerate(spec["rows"]):
        words = []
        for j, (text, metal, cap) in enumerate(row):
            pieces, xs, c = word(font, text, metal, cap, seed=hash_seed(text), arc=spec.get("arc", 0.0), tilt=spec.get("tilt", 0.0), wobble=spec.get("wobble", 1.0))
            words.append(dict(pieces=pieces, xs=xs, cap=c, metal=metal, seed=hash_seed(text)))
        rows.append(dict(words=words))
    return forge(rows, depth=spec.get("depth", 0.105), bevel=spec.get("bevel", 0.095), edge=spec.get("edge", 0.056))


def hash_seed(text):
    return sum(ord(c) * (i + 3) for i, c in enumerate(text)) % 9973


CAPTIONS = {
    "four_armies": dict(rows=[[("FOUR", "steel", 74)], [("ARMIES.", "gold", 104)]], arc=0.1),
    "one_battlefield": dict(rows=[[("ONE", "steel", 80), ("BATTLEFIELD.", "gold", 80)]]),
    "cse": dict(rows=[[("CSE", "ice", 92)]]),
    "me": dict(rows=[[("ME", "ember", 92)]]),
    "vs": dict(rows=[[("VS", "gold", 118)]], tilt=4),
    "capacitor": dict(rows=[[("CAPACITOR", "gold", 88)]]),
    "hold_bridge": dict(rows=[[("HOLD", "steel", 70), ("THE", "steel", 70), ("BRIDGE.", "gold", 70)]]),
    "every_drop": dict(rows=[[("EVERY", "steel", 62), ("DROP", "steel", 62), ("COUNTS.", "gold", 62)]]),
    "choose_four": dict(rows=[[("CHOOSE", "steel", 66), ("YOUR", "steel", 66), ("FOUR.", "gold", 66)]]),
    "power_mode": dict(rows=[[("POWER", "ice", 94)], [("MODE", "gold", 122)]], arc=0.08),
    "one_minute": dict(rows=[[("ONE", "ice", 72), ("MINUTE.", "gold", 72)]]),
    "no_turns": dict(rows=[[("NO", "ice", 72), ("TURNS.", "gold", 72)]]),
    "hit_hard": dict(rows=[[("HIT", "ice", 72), ("HARD.", "gold", 72)]]),
    "finish_it": dict(rows=[[("FINISH", "steel", 72), ("IT.", "gold", 72)]]),
    "castle_down": dict(rows=[[("CASTLE", "steel", 92), ("DOWN.", "gold", 92)]]),
    "kuet_royale": dict(rows=[[("KUET", "steel", 112)], [("ROYALE", "gold", 150)]], arc=0.12),
    "logo_menu": dict(rows=[[("KUET", "steel", 56), ("ROYALE", "gold", 56)]]),
    "logo_bar": dict(rows=[[("KUET", "steel", 21), ("ROYALE", "gold", 21)]], wobble=0.5),
    "department_wars": dict(rows=[[("DEPARTMENT", "steel", 30), ("WARS", "steel", 30)]], wobble=0.4),
    "card_compiler": dict(rows=[[("COMPILER", "gold", 25)]], wobble=0.4),
    "card_logic_bomber": dict(rows=[[("LOGIC", "gold", 21), ("BOMBER", "gold", 21)]], wobble=0.4),
    "card_stack_runner": dict(rows=[[("STACK", "gold", 21), ("RUNNER", "gold", 21)]], wobble=0.4),
    "card_cloud_drone": dict(rows=[[("CLOUD", "gold", 21), ("DRONE", "gold", 21)]], wobble=0.4),
}
SMALL = {
    "line_cse": ("Fast, cheap and clever.", 24), "line_me": ("Heavy, slow and hard to stop.", 24),
    "line_cap1": ("A sturdy wall that soaks up hits.", 27), "line_cap2": ("And when it falls, everyone near it pays.", 27),
    "line_cards": ("One tank. One shooter. One runner. One surprise.", 26), "line_power": ("One minute. No turns.", 31),
    "line_title": ("Choose your side.", 29), "special_armour": ("Armour", 11), "special_splash": ("Splash", 11), "special_blast": ("Last blast", 11), "special_hover": ("Hover", 11),
}


def main():
    font_name = sys.argv[1] if len(sys.argv) > 1 else "titan"
    names = sys.argv[2:]
    font = Font(font_name)
    path = os.path.join(HERE, "..", "src", "text_index.json")
    table = json.load(open(path)) if os.path.exists(path) else {}
    for name, spec in CAPTIONS.items():
        if not names or name in names:
            save(name, caption(font, spec), table)
    for name, (text, cap) in SMALL.items():
        if not names or name in names:
            save(name, small_line(text, cap), table)
    json.dump(table, open(path, "w"), indent=0)
    print("made", len(names) or len(CAPTIONS) + len(SMALL))


if __name__ == "__main__":
    main()
