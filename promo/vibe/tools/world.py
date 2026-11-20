#!/usr/bin/env python3
"""A battlefield seen from the ground, built from the game's real map, for the promo's stills.

World units are tiles. x runs across the arena (0 to 7), z runs along it away from the camera (0 to 13).
Everything is added up in linear light and graded at the end, like a film frame.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(__file__))
from light import lit

HERE = os.path.dirname(os.path.abspath(__file__))
HERO = os.path.join(HERE, "..", "public", "hero")
W, H = 1920, 1080
PX = 96                 # texture pixels per tile
X0, X1, Z0, Z1 = -22.0, 29.0, -7.0, 40.0
SPRITE_TILES = 75 / 48  # a warrior picture's side, in tiles
FEET = 1340 / 1500

MAP = json.load(open(os.path.join(HERE, "..", "..", "..", "ai", "data", "map.json")))["rows"]


def srgb(hex_colour):
    h = hex_colour.lstrip("#")
    return (np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255) ** 2.2


def noise(shape, cell, seed, octaves=5, falloff=0.55):
    rng = np.random.default_rng(seed)
    out = np.zeros(shape, dtype=np.float32)
    amp, total = 1.0, 0.0
    for _ in range(octaves):
        small = (max(2, int(shape[0] / cell) + 2), max(2, int(shape[1] / cell) + 2))
        grid = rng.random(small, dtype=np.float32)
        out += amp * cv2.resize(grid, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)
        total += amp
        amp *= falloff
        cell = max(1.5, cell / 2)
    return out / total


_texture = None


def texture():
    """The game's map painted as ground: the same lanes, mud, river and bridges, seen as real terrain."""
    global _texture
    if _texture is not None:
        return _texture
    cache = os.path.join(HERE, ".ground.npy")
    if os.path.exists(cache):
        _texture = np.load(cache)
        return _texture
    h, w = int((Z1 - Z0) * PX), int((X1 - X0) * PX)
    n1 = noise((h, w), 220, 1)
    n2 = noise((h, w), 26, 2, octaves=4)
    n3 = noise((h, w), 6, 3, octaves=3)
    grass_a, grass_b = srgb("#5f9a3a"), srgb("#4f8a33")
    ground = np.zeros((h, w, 3), dtype=np.float32)
    ground[:] = grass_b
    zz, xx = np.mgrid[0:h, 0:w]
    tx, tz = xx / PX + X0, Z1 - zz / PX
    checker = ((np.floor(tx) + np.floor(tz)) % 2 == 0)
    inside = (tx >= 0) & (tx < 7) & (tz >= 0) & (tz < 13)
    ground[checker & inside] = grass_a
    ground *= (0.62 + 0.75 * n1[..., None]) * (0.72 + 0.56 * n2[..., None]) * (0.86 + 0.28 * n3[..., None])
    # Everything outside the arena is darker, rougher field.
    outside = ~inside
    ground[outside] *= np.array([0.62, 0.66, 0.52])

    def tile_mask(mark_set, grow=0.0):
        mask = np.zeros((h, w), dtype=np.float32)
        for col, _ in enumerate(MAP[0]):
            for row, line in enumerate(MAP):
                if line[col] in mark_set:
                    tile_x, tile_z = row, 12 - col
                    x0, x1 = int((tile_x - X0 + grow) * PX), int((tile_x + 1 - X0 - grow) * PX)
                    z0, z1 = int((Z1 - tile_z - 1 + grow) * PX), int((Z1 - tile_z - grow) * PX)
                    mask[z0:z1, x0:x1] = 1
        return mask

    def rough(mask, cell, amount, seed, blur=5):
        wob = noise((h, w), cell, seed, octaves=3) - 0.5
        soft = cv2.GaussianBlur(mask, (0, 0), blur + 8)
        return np.clip(((soft + wob * amount) - 0.5) * 12 + 0.5, 0, 1)

    # Lanes: packed dirt with worn edges.
    road = rough(tile_mask("=SB"), 44, 0.5, 11)
    dirt = srgb("#b89a63") * (0.55 + 0.75 * n2[..., None]) * (0.78 + 0.44 * n3[..., None])
    ground = ground * (1 - road[..., None]) + dirt * road[..., None]
    edge = np.clip(cv2.GaussianBlur(road, (0, 0), 7) - road, 0, 1)
    ground *= 1 - 0.9 * edge[..., None]
    # Mud: dark and wet.
    mud = rough(tile_mask("m"), 30, 0.7, 12)
    wet = srgb("#7a5a3e") * (0.6 + 0.8 * n3[..., None])
    ground = ground * (1 - mud[..., None]) + wet * mud[..., None]
    # River: dark moving water with light on it, running out past the arena on both sides.
    river = np.zeros((h, w), dtype=np.float32)
    rz0, rz1 = int((Z1 - 7 + 0.12) * PX), int((Z1 - 6 - 0.12) * PX)
    river[rz0:rz1, :] = 1
    river = rough(river, 60, 0.32, 13, blur=3)
    streak = noise((h, w), 40, 14, octaves=4)
    streak = cv2.resize(cv2.resize(streak, (w // 8, h)), (w, h), interpolation=cv2.INTER_CUBIC)
    water = srgb("#1d6fa8") * (0.5 + 0.9 * streak[..., None]) + np.array([0.5, 0.65, 0.8]) * np.clip(streak - 0.62, 0, 1)[..., None] * 5
    bank = np.clip(cv2.GaussianBlur(river, (0, 0), 16) * 1.1, 0, 1)
    ground *= 1 - 0.75 * (bank * (1 - river))[..., None]
    ground = ground * (1 - river[..., None]) + water * river[..., None]
    # Bridges: planks across the water, with dark gaps.
    for col, _ in enumerate(MAP[0]):
        for row, line in enumerate(MAP):
            if line[col] == "B":
                x0, x1 = int((row + 0.08 - X0) * PX), int((row + 0.92 - X0) * PX)
                z0, z1 = int((Z1 - (12 - col) - 1 - 0.2) * PX), int((Z1 - (12 - col) + 0.2) * PX)
                wood = srgb("#a0703f") * (0.7 + 0.6 * n3[z0:z1, x0:x1, None])
                for plank in range(z0, z1, 17):
                    wood[plank - z0:plank - z0 + 4] *= 0.28
                ground[z0:z1, x0:x1] = wood
                ground[z0:z1, x0:x0 + 8] *= 0.3
                ground[z0:z1, x1 - 8:x1] *= 0.3
    # The hedge round the arena, as a dark rough band.
    rim = np.zeros((h, w), dtype=np.float32)
    x0, x1, z0, z1 = int((-0.3 - X0) * PX), int((7.3 - X0) * PX), int((Z1 - 13.3) * PX), int((Z1 + 0.3) * PX)
    rim[z0:z1, x0:x1] = 1
    inner = np.zeros((h, w), dtype=np.float32)
    inner[int((Z1 - 13) * PX):int(Z1 * PX), int(-X0 * PX):int((7 - X0) * PX)] = 1
    band = rim * (1 - inner) * (1 - river)
    ground = ground * (1 - band[..., None]) + srgb("#2f5a2a") * (0.5 + 0.9 * n2[..., None]) * band[..., None]
    np.save(cache, ground.astype(np.float32))
    _texture = ground.astype(np.float32)
    return _texture


class Camera:
    def __init__(self, x=3.5, z=-2.5, height=0.8, focal=1500, horizon=470, centre=960, roll=0.0):
        self.x, self.z, self.h, self.f, self.hy, self.cx, self.roll = x, z, height, focal, horizon, centre, roll

    def project(self, wx, wz, wy=0.0):
        d = wz - self.z
        return self.cx + self.f * (wx - self.x) / d, self.hy + self.f * (self.h - wy) / d, self.f / d

    def ground(self):
        """The painted ground as this camera sees it, with the distance to every pixel."""
        tex = texture()
        ss = 2
        near = self.z + 0.55
        far = Z1 - 0.5
        wide = 40.0
        corners_world = [(self.x - wide, far), (self.x + wide, far), (self.x + wide * 0.1, near), (self.x - wide * 0.1, near)]
        src, dst = [], []
        for wx, wz in corners_world:
            sx, sy, _ = self.project(wx, wz)
            src.append([(wx - X0) * PX, (Z1 - wz) * PX])
            dst.append([sx * ss, sy * ss])
        M = cv2.getPerspectiveTransform(np.array(src, dtype=np.float32), np.array(dst, dtype=np.float32))
        blurred = cv2.GaussianBlur(tex, (0, 0), 1.4)
        out = cv2.warpPerspective(blurred, M, (W * ss, H * ss), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.06, 0.09, 0.05))
        out = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
        rows = np.arange(H, dtype=np.float32)
        depth = self.f * self.h / np.maximum(rows - self.hy, 0.5)
        return out, np.repeat(depth[:, None], W, axis=1), rows


class Scene:
    def __init__(self, camera, sun=(1120, 430), fog=(0.85, 0.42, 0.20), fog_density=0.05, sky=("#070c1a", "#1a1a2c", "#b3481f", "#ffb060"), seed=1, light=None):
        self.cam, self.sun, self.fog, self.density, self.seed = camera, sun, np.array(fog, dtype=np.float32), fog_density, seed
        # Backlit by default: little light on the side we see, a strong warm rim from the sun behind.
        self.light = {"key": (0.20, 0.22, 0.30), "fill": (0.055, 0.065, 0.10), "rim": (1.0, 0.50, 0.20), "rim_amount": 3.0, "gain": 1.0}
        self.light.update(light or {})
        self.frame = self._sky(sky)
        self._ground()
        self.bright = None

    def _sky(self, stops):
        hy = self.cam.hy
        ys = np.linspace(0, 1, H, dtype=np.float32)
        colours = [srgb(c) for c in stops]
        at = [0.0, 0.55, 0.9, 1.0]
        band = np.stack([np.interp(ys * H / max(hy + 10, 1), at, [c[i] for c in colours]) for i in range(3)], axis=1)
        sky = np.repeat(band[:, None, :], W, axis=1).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - self.sun[0]) / 1.7, yy - self.sun[1])
        sky += np.array([1.0, 0.45, 0.16]) * (np.exp(-d / 280) * 0.55)[..., None]
        sky += np.array([1.0, 0.78, 0.48]) * (np.exp(-d / 62) * 3.0)[..., None]
        # Storm clouds: big soft masses, dark, with fire on their undersides near the sun.
        def clouds(seed, cw, ch, falloff):
            n = np.zeros((H, W), dtype=np.float32)
            amp, total = 1.0, 0.0
            rng = np.random.default_rng(seed)
            for _ in range(6):
                grid = rng.random((ch, cw), dtype=np.float32)
                n += amp * cv2.resize(grid, (W, H), interpolation=cv2.INTER_CUBIC)
                total += amp
                amp *= falloff
                cw, ch = cw * 2, ch * 2
            return n / total
        n = clouds(self.seed + 40, 4, 4, 0.5)
        n = cv2.GaussianBlur(n, (0, 0), 3)
        lifted = cv2.warpAffine(n, np.array([[1, 0, 0], [0, 1, -60]], dtype=np.float32), (W, H), borderMode=cv2.BORDER_REPLICATE)
        cover = np.clip((n - 0.34) / 0.30, 0, 1) ** 1.2
        height_fade = np.clip((hy - yy) / 260 + 0.12, 0, 1)
        cover = cover * height_fade
        glow = np.exp(-np.hypot((xx - self.sun[0]) / 2.6, (yy - self.sun[1]) * 1.15) / 430)
        underlit = np.clip((lifted - n) * 8 + 0.1, 0, 1)
        dark = srgb("#080b18") * (0.6 + 1.1 * n[..., None])
        colour = dark + np.array([1.0, 0.27, 0.07]) * (underlit * glow * 0.62)[..., None] + np.array([0.012, 0.018, 0.038]) * underlit[..., None]
        return sky * (1 - cover[..., None]) + colour * cover[..., None]

    def _ground(self):
        cam = self.cam
        ground, depth, rows = cam.ground()
        # The ground falls into deep shadow near the camera, and only catches the fire of the sky far away.
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - self.sun[0]) / 2.4, (yy - cam.hy) * 1.5)
        light = 0.035 + 0.62 * np.exp(-d / 300)
        lum = ground.mean(axis=2, keepdims=True)
        muted = ground * 0.55 + lum * 0.45
        lit_ground = muted * light[..., None] * np.array([1.25, 0.82, 0.56])
        # Low haze along the far ground.
        haze = np.clip(1 - (rows[:, None] - cam.hy) / 90, 0, 1) ** 2
        lit_ground = lit_ground * (1 - haze[..., None] * 0.6) + self.fog * (0.32 * np.exp(-d / 620))[..., None] * haze[..., None]
        mask = np.clip((rows - cam.hy) / 3, 0, 1)[:, None, None]
        self.frame = self.frame * (1 - mask) + lit_ground * mask
        self.depth = depth

    def treeline(self, seed=7, height=34, colour="#0e1422", at=None, haze=0.16):
        """A dark ragged line of trees and hills along the horizon."""
        hy = self.cam.hy if at is None else at
        line = noise((1, W), 70, seed, octaves=5)[0] * height * 1.1 + noise((1, W), 700, seed + 1, octaves=3)[0] * height * 1.6
        yy = np.arange(H, dtype=np.float32)[:, None]
        mask = np.clip((yy - (hy - line[None, :])) / 1.5, 0, 1) * np.clip((hy + 6 - yy) / 6, 0, 1)
        value = srgb(colour) + self.fog * haze
        self.frame = self.frame * (1 - mask[..., None]) + value * mask[..., None]

    def _place(self, colour, alpha, cx, feet_y, size, flip, fog, blur, tint=None):
        s = int(max(8, round(size)))
        c = cv2.resize(colour, (s, s), interpolation=cv2.INTER_AREA if s < colour.shape[0] else cv2.INTER_CUBIC)
        a = cv2.resize(alpha, (s, s), interpolation=cv2.INTER_AREA if s < alpha.shape[0] else cv2.INTER_CUBIC)
        if flip:
            c, a = c[:, ::-1], a[:, ::-1]
        if tint is not None:
            c = c * np.array(tint, dtype=np.float32)
        if fog > 0:
            c = c * (1 - fog) + self.fog * 0.34 * fog
        if blur > 0.3:
            pad = int(blur * 4) + 2
            c = cv2.copyMakeBorder(c, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
            a = cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
            premult = c * a[..., None]
            premult = cv2.GaussianBlur(premult, (0, 0), blur)
            a = cv2.GaussianBlur(a, (0, 0), blur)
            c = premult / np.maximum(a[..., None], 1e-3)
            s += pad * 2
        left = int(round(cx - s / 2))
        top = int(round(feet_y - s * FEET - (0 if blur <= 0.3 else 0)))
        x0, y0 = max(left, 0), max(top, 0)
        x1, y1 = min(left + s, W), min(top + s, H)
        if x0 >= x1 or y0 >= y1:
            return
        cc = c[y0 - top:y1 - top, x0 - left:x1 - left]
        aa = a[y0 - top:y1 - top, x0 - left:x1 - left][..., None]
        self.frame[y0:y1, x0:x1] = self.frame[y0:y1, x0:x1] * (1 - aa) + cc * aa

    def shadow(self, alpha, cx, feet_y, size, flip, strength=0.42):
        """A long shadow thrown towards the camera, because the sun is behind the warrior."""
        s = int(max(8, round(size)))
        a = cv2.resize(alpha, (s, s), interpolation=cv2.INTER_AREA)
        if flip:
            a = a[:, ::-1]
        sx, sy = self.sun
        lean = np.clip((cx - sx) / 900, -1.4, 1.4)
        length = 0.62
        foot = int(s * FEET)
        M = np.array([[1, lean * length, cx - s / 2 - lean * length * foot], [0, -length, feet_y + foot * length]], dtype=np.float32)
        layer = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)
        layer = cv2.GaussianBlur(layer, (0, 0), max(1.5, s / 70))
        self.frame *= (1 - np.clip(layer, 0, 1) * strength)[..., None]

    def warrior(self, name, wx, wz, pose="idle", flip=False, scale=1.0, wy=0.0, blur=None, focus=None, light=None, shadow=True, tint=None):
        sx, sy, per_tile = self.cam.project(wx, wz, wy)
        kw = dict(self.light)
        kw.update(light or {})
        if "rim_dir" not in kw:
            kw["rim_dir"] = (0.9 if self.sun[0] > sx else -0.9, -0.45)
        colour, alpha = _sprite(name, pose, tuple(sorted((k, tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in kw.items())))
        size = SPRITE_TILES * per_tile * scale
        d = wz - self.cam.z
        fog = 1 - np.exp(-max(d - 1.5, 0) * self.density * 1.35)
        if blur is None:
            blur = 0.0 if focus is None else min(11, abs(1 / d - 1 / focus) * 6)
        if shadow and wy == 0:
            self.shadow(alpha, sx, sy, size, flip)
        self._place(colour, alpha, sx, sy, size, flip, fog, blur, tint)

    def castle(self, department, wx, wz, broken=False, scale=2.6, flip=False, light=None):
        self.warrior("castle-%s" % department, wx, wz, pose="ruin" if broken else "whole", scale=scale, flip=flip, light=light or {"radius": 60})

    def smoke(self, y0, y1, amount=0.7, colour=(0.75, 0.48, 0.32), cell=300, seed=5):
        """A bank of dust between y0 and y1."""
        n = noise((H, W), cell, seed, octaves=6, falloff=0.6)
        rows = np.arange(H, dtype=np.float32)
        shape = np.clip((rows - y0) / max(1, (y1 - y0) * 0.45), 0, 1) * np.clip((y1 - rows) / max(1, (y1 - y0) * 0.55), 0, 1)
        a = np.clip((n - 0.40) * 3.4, 0, 1) * shape[:, None] * amount
        self.frame = self.frame * (1 - a[..., None]) + np.array(colour, dtype=np.float32) * a[..., None]

    def rays(self, strength=0.5):
        """Shafts of light from the sun, cut by whatever stands in front of it."""
        small = cv2.resize(self.frame, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
        bright = np.clip(small - 1.6, 0, 4)
        sx, sy = self.sun[0] / 3, self.sun[1] / 3
        out = np.zeros_like(bright)
        for i in range(50):
            k = 1 + i * 0.03
            M = np.array([[k, 0, sx * (1 - k)], [0, k, sy * (1 - k)]], dtype=np.float32)
            out += cv2.warpAffine(bright, M, (W // 3, H // 3)) * (0.955 ** i)
        out = cv2.resize(out / 50, (W, H), interpolation=cv2.INTER_CUBIC)
        self.frame += cv2.GaussianBlur(out, (0, 0), 4) * strength * np.array([1.0, 0.66, 0.36])

    def embers(self, count=70, seed=9, colour=(1.0, 0.42, 0.10), big=4, low=0.35):
        """Sparks drifting up from the fight: small, uneven, thicker near the ground."""
        rng = np.random.default_rng(seed)
        layer = np.zeros((H, W, 3), dtype=np.float32)
        for _ in range(count):
            x, y = rng.uniform(0, W), H * (low + (1 - low) * rng.beta(2.2, 1.4))
            length = rng.uniform(1, 9) ** 1.1
            angle = rng.uniform(-1.5, -0.7)
            value = rng.uniform(0.3, 1.8) ** 2
            p2 = (int(x + np.cos(angle) * length), int(y + np.sin(angle) * length))
            cv2.line(layer, (int(x), int(y)), p2, tuple(float(v) * value for v in colour), 1, cv2.LINE_AA)
        soft = cv2.GaussianBlur(layer, (0, 0), 2.0)
        bokeh = np.zeros((H, W, 3), dtype=np.float32)
        for _ in range(big):
            x, y = rng.uniform(0, W), rng.uniform(H * 0.3, H)
            r = rng.uniform(5, 16)
            cv2.circle(bokeh, (int(x), int(y)), int(r), tuple(float(v) * rng.uniform(0.12, 0.35) for v in colour), -1, cv2.LINE_AA)
        bokeh = cv2.GaussianBlur(bokeh, (0, 0), 2.2)
        self.frame += layer * 1.1 + soft * 1.6 + bokeh

    def foreground(self, seed=3, height=150, colour="#04060a"):
        """Dark blades of grass right in front of the lens, out of focus."""
        rng = np.random.default_rng(seed)
        layer = np.zeros((H, W), dtype=np.float32)
        for _ in range(420):
            x = rng.uniform(-40, W + 40)
            h = rng.uniform(0.25, 1.0) * height
            lean = rng.uniform(-0.35, 0.35) * h
            base = H + 6
            points = np.array([[x - rng.uniform(4, 12), base], [x + lean, base - h], [x + rng.uniform(4, 12), base]], dtype=np.int32)
            cv2.fillConvexPoly(layer, points, 1.0, cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), 5)
        self.frame = self.frame * (1 - layer[..., None]) + srgb(colour) * layer[..., None]

    def place(self, name, pose, cx, feet_y, size, flip=False, blur=0.0, light=None, fog=0.0, tint=None):
        """A warrior put straight on the picture, for close-ups."""
        kw = dict(self.light)
        kw.update(light or {})
        if "rim_dir" not in kw:
            kw["rim_dir"] = (0.9 if self.sun[0] > cx else -0.9, -0.45)
        colour, alpha = _sprite(name, pose, tuple(sorted((k, tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in kw.items())))
        self._place(colour, alpha, cx, feet_y, size, flip, fog, blur, tint)

    def bolt(self, start, end, seed=1, width=3.0, colour=(0.75, 0.86, 1.0), amount=5.0, jag=70, branches=3):
        """A strike of lightning."""
        rng = np.random.default_rng(seed)
        layer = np.zeros((H, W, 3), dtype=np.float32)

        def strike(a, b, thick, jitter, level):
            steps = 14
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = np.hypot(dx, dy) or 1
            points = []
            for i in range(steps + 1):
                k = i / steps
                off = 0 if i in (0, steps) else rng.normal(0, jitter) * np.sin(k * np.pi) ** 0.5
                points.append((a[0] + dx * k - dy / length * off, a[1] + dy * k + dx / length * off))
            pts = np.array(points, dtype=np.int32)
            cv2.polylines(layer, [pts], False, tuple(float(v) * amount for v in colour), max(1, int(thick)), cv2.LINE_AA)
            if level > 0:
                for _ in range(branches):
                    i = rng.integers(3, steps - 2)
                    start_point = points[i]
                    far = (start_point[0] + rng.uniform(-0.45, 0.45) * length, start_point[1] + rng.uniform(0.1, 0.4) * length)
                    strike(start_point, far, max(1, thick * 0.5), jitter * 0.5, level - 1)

        strike(start, end, width, jag, 2)
        self.frame += layer + cv2.GaussianBlur(layer, (0, 0), 5) * 0.7 + cv2.GaussianBlur(layer, (0, 0), 24) * 0.55 + cv2.GaussianBlur(layer, (0, 0), 80) * 0.4

    def wash(self, left, right):
        """Colours the whole picture from left to right, like two lights on two armies."""
        k = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
        k = k * k * (3 - 2 * k)
        self.frame *= np.array(left, dtype=np.float32)[None, None] * (1 - k) + np.array(right, dtype=np.float32)[None, None] * k

    def zoom_blur(self, x, y, amount=0.05, samples=18):
        """The picture rushing out from a point, for an impact."""
        out = np.zeros_like(self.frame)
        for i in range(samples):
            k = 1 + amount * i / samples
            M = np.array([[k, 0, x * (1 - k)], [0, k, y * (1 - k)]], dtype=np.float32)
            out += cv2.warpAffine(self.frame, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
        self.frame = out / samples

    def impact(self, x, y, seed=2, size=1.0, colour=(1.0, 0.62, 0.22)):
        """The moment two weapons meet: a white core, a flash, sparks flying out in straight lines, and a ring of dust."""
        rng = np.random.default_rng(seed)
        layer = np.zeros((H, W, 3), dtype=np.float32)
        for _ in range(int(150 * size)):
            angle = rng.uniform(0, np.tau) if hasattr(np, "tau") else rng.uniform(0, 6.283)
            start = rng.uniform(20, 180) * size
            length = rng.uniform(20, 220) * size * rng.random() ** 1.5
            a = (int(x + np.cos(angle) * start), int(y + np.sin(angle) * start * 0.8))
            b = (int(x + np.cos(angle) * (start + length)), int(y + np.sin(angle) * (start + length) * 0.8))
            value = rng.uniform(0.6, 4.5)
            cv2.line(layer, a, b, tuple(float(v) * value for v in colour), int(rng.integers(1, 4)), cv2.LINE_AA)
        self.frame += layer + cv2.GaussianBlur(layer, (0, 0), 6) * 1.2
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot(xx - x, (yy - y) * 1.1) / size
        angle_map = np.arctan2(yy - y, xx - x)
        spikes = 0.55 + 0.45 * np.cos(angle_map * 9 + 1.3) * np.cos(angle_map * 5 + 0.4)
        self.frame += np.array(colour, dtype=np.float32) * (np.exp(-d / (120 * spikes + 40)) * 3.2)[..., None]
        self.frame += np.array([1.0, 0.95, 0.85], dtype=np.float32) * (np.exp(-d / 24) * 10)[..., None]
        ring = np.exp(-((d - 300) / 26) ** 2)
        wob = noise((H, W), 60, seed + 5, octaves=4)
        self.frame = self.frame * (1 - (ring * wob * 0.55)[..., None]) + np.array([0.62, 0.42, 0.28], dtype=np.float32) * (ring * wob * 0.55)[..., None]

    def rain(self, seed=4, count=900, amount=0.5, angle=0.16):
        rng = np.random.default_rng(seed)
        layer = np.zeros((H, W), dtype=np.float32)
        for _ in range(count):
            x, y = rng.uniform(-100, W + 100), rng.uniform(-100, H)
            length = rng.uniform(18, 70)
            cv2.line(layer, (int(x), int(y)), (int(x - angle * length), int(y + length)), float(rng.uniform(0.15, 1.0)), 1, cv2.LINE_AA)
        self.frame += cv2.GaussianBlur(layer, (0, 0), 0.7)[..., None] * np.array([0.6, 0.72, 0.95], dtype=np.float32) * amount

    def explosion(self, x, y, radius=300, seed=6):
        """A fireball, with its smoke above it and stones thrown out of it."""
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        # Smoke rising.
        n = noise((H, W), 170, seed + 1, octaves=6, falloff=0.6)
        dy = np.clip((y + radius * 0.3 - yy) / (radius * 3.0), 0, 1)
        spread = radius * (0.65 + dy * 1.25)
        column = np.exp(-((xx - x - dy * 90) / spread) ** 2) * np.clip(1 - dy * 0.75, 0, 1) * (yy < y + radius * 0.4)
        smoke = np.clip((n - 0.3) * 3.6, 0, 1) * column
        self.frame = self.frame * (1 - smoke[..., None] * 0.93) + (srgb("#120d0d") + np.array([0.5, 0.17, 0.05]) * np.exp(-np.maximum(y - yy, 0) / (radius * 0.9))[..., None]) * smoke[..., None] * 0.93
        # Fire.
        n2 = noise((H, W), 80, seed + 2, octaves=6, falloff=0.6)
        d = np.hypot(xx - x, (yy - y) * 1.15) / radius
        heat = np.clip((1.15 - d) + (n2 - 0.5) * 1.5, 0, 1.2)
        fire = np.zeros((H, W, 3), dtype=np.float32)
        fire[..., 0] = np.clip(heat * 3.6, 0, 7)
        fire[..., 1] = np.clip((heat - 0.28) * 3.4, 0, 5)
        fire[..., 2] = np.clip((heat - 0.72) * 3.2, 0, 3)
        a = np.clip(heat * 3.2, 0, 1)
        self.frame = self.frame * (1 - a[..., None]) + fire * a[..., None]
        self.frame += np.array([1.0, 0.42, 0.12], dtype=np.float32) * (np.exp(-d / 1.4) * 0.8)[..., None]
        # Stones.
        rng = np.random.default_rng(seed + 3)
        stones = np.zeros((H, W), dtype=np.float32)
        for _ in range(60):
            angle = rng.uniform(-np.pi, 0.1)
            r = radius * rng.uniform(0.7, 2.4)
            cx, cy = x + np.cos(angle) * r, y + np.sin(angle) * r * 0.85
            size = rng.uniform(4, 26) * rng.random() ** 1.2 + 3
            pts = np.array([[cx + np.cos(k) * size * rng.uniform(0.6, 1.2), cy + np.sin(k) * size * rng.uniform(0.6, 1.2)] for k in np.linspace(0, 6.28, 6, endpoint=False)], dtype=np.int32)
            cv2.fillConvexPoly(stones, pts, 1.0, cv2.LINE_AA)
        self.frame = self.frame * (1 - stones[..., None]) + srgb("#0e0c0e") * stones[..., None]

    def add_light(self, x, y, radius, colour, amount=1.0):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot(xx - x, yy - y)
        self.frame += np.array(colour, dtype=np.float32) * (np.exp(-d / radius) * amount)[..., None]

    def vignette(self, amount=0.55):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
        self.frame *= (1 - amount * np.clip(d - 0.42, 0, 1) ** 1.6 * 1.7)[..., None]

    def finish(self, path, exposure=1.0, grain=0.012, teal=0.18):
        f = self.frame * exposure
        # Bloom.
        bright = np.clip(f - 1.0, 0, 8)
        f = f + cv2.GaussianBlur(bright, (0, 0), 14) * 0.5 + cv2.GaussianBlur(bright, (0, 0), 50) * 0.35
        # A filmic curve.
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        f = np.clip((f * (a * f + b)) / (f * (c * f + d) + e), 0, 1)
        out = f ** (1 / 2.2)
        # Teal in the shadows, warm in the lights.
        lum = out.mean(axis=2, keepdims=True)
        out = out + (1 - lum) ** 2 * np.array([-0.5, 0.05, 0.28]) * teal
        rng = np.random.default_rng(3)
        out = out + rng.normal(0, grain, (H, W, 1)).astype(np.float32)
        Image.fromarray((np.clip(out, 0, 1) * 255).round().astype(np.uint8)).save(path, quality=93)


_cache = {}


def _sprite(name, pose, key):
    k = (name, pose, key)
    if k not in _cache:
        _cache[k] = lit(os.path.join(HERO, "%s_%s.png" % (name, pose)), **dict(key))
    return _cache[k]
