#!/usr/bin/env python3
"""The moving pictures of the 60-second film, frame by frame.

    python3 tools/film.py sample [shots]     a few frames of each shot on one sheet
    python3 tools/film.py render [shots]     the shots as video files

A real camera moves over the game's map, and every warrior walks with their own drawn frames.
"""
import hashlib
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
import cv2
import numpy as np
from PIL import Image

cv2.setNumThreads(1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from light import lit
from world import FEET, SPRITE_TILES, X0, X1, Z0, Z1, PX, W, H, Camera, noise, srgb, texture

SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work")
ANIM = SCRATCH + "/anim/"
CUTS = SCRATCH + "/cuts/"
HERO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "hero") + "/"
CACHE = SCRATCH + "/litcache/"
OUT = SCRATCH + "/shots/"
FPS = 30
BEAT = 15       # frames: 120 beats a minute
BAR = 60
RUN, STAND, HIT = 12, 8, 10

CSE = ["compiler", "kernel", "algorithmist", "optimizer", "logic-bomber", "debugger", "stack-runner", "cloud-drone"]
EEE = ["capacitor", "transformer", "signal-processor", "circuit-engineer", "oscillator", "power-engineer", "relay-runner", "electron"]
ME = ["heavy-machine", "gearwheel-guard", "robotic-arm", "steel-rain-cannon", "mech-warrior", "gear-runner", "mini-bot", "quadcopter"]
CE = ["excavator", "road-roller", "site-engineer", "crane-operator", "seismic-crew", "surveyor", "construction-crew", "survey-drone"]

BACKLIT = dict(key=(0.20, 0.22, 0.30), fill=(0.055, 0.065, 0.10), rim=(1.0, 0.50, 0.20), rim_amount=3.0)
FIRE_KEY = dict(key=(0.95, 0.62, 0.40), fill=(0.06, 0.08, 0.13), rim=(1.0, 0.55, 0.22), rim_amount=3.2, key_dir=(0.5, -0.5, 0.6))
COLD_KEY = dict(key=(0.42, 0.62, 1.0), fill=(0.05, 0.08, 0.16), rim=(0.5, 0.8, 1.0), rim_amount=3.4, key_dir=(0.5, -0.5, 0.6))
COLD_BACK = dict(key=(0.2, 0.28, 0.5), fill=(0.04, 0.06, 0.13), rim=(0.55, 0.78, 1.0), rim_amount=3.4)
FIRE_SKY = dict(stops=("#070c1a", "#1a1a2c", "#b3481f", "#ffb060"), fog=(0.85, 0.42, 0.20), under=(1.0, 0.27, 0.07))
COLD_SKY = dict(stops=("#050814", "#10183a", "#34508f", "#a7c4ee"), fog=(0.35, 0.5, 0.9), under=(0.32, 0.46, 1.0))

GRID_Y, GRID_X = np.mgrid[0:H, 0:W].astype(np.float32)
GRID4_Y, GRID4_X = np.mgrid[0:H // 4, 0:W // 4].astype(np.float32) * 4
GRID2_Y, GRID2_X = np.mgrid[0:H // 2, 0:W // 2].astype(np.float32) * 2
RNG = np.random.default_rng(77)
GRAIN = RNG.normal(0, 1, (H + 64, W + 64, 1)).astype(np.float32)

SPR = {}
TEX = None


# ---------------------------------------------------------------- helpers

def ss(a, b, x):
    k = np.clip((x - a) / float(b - a), 0, 1)
    return float(k * k * (3 - 2 * k))


def eout(a, b, x):
    k = np.clip((x - a) / float(b - a), 0, 1)
    return float(1 - (1 - k) ** 3)


def lerp(a, b, k):
    return a + (b - a) * k


def key_of(light):
    return tuple(sorted((k, tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in light.items()))


def sprite_file(name, pose, idx):
    if name.startswith("castle-"):
        return HERO + "%s_%s.png" % (name, pose)
    return ANIM + "%s_%s_%02d.png" % (name, pose, idx)


def cache_path(item):
    return CACHE + hashlib.md5(repr(item).encode()).hexdigest() + ".npy"


def make_sprite(item):
    name, pose, idx, res, light = item
    path = cache_path(item)
    if os.path.exists(path):
        return
    colour, alpha = lit(sprite_file(name, pose, idx), size=res, **dict(light))
    np.save(path, np.dstack([colour, alpha]).astype(np.float16))


class Bake:
    """What a shot works out once: clouds, smoke, grass and embers, ready to be moved."""

    def __init__(self, seed=1, under=(1.0, 0.25, 0.045), embers=70, ember_colour=(1.0, 0.42, 0.10), low=0.35):
        self.seed, self.under = seed, np.array(under, dtype=np.float32)
        rng = np.random.default_rng(seed + 900)
        n = np.zeros((H // 2 + 500, W // 2 + 800), dtype=np.float32)
        amp, total, cw, ch = 1.0, 0.0, 6, 6
        for _ in range(6):
            n += amp * cv2.resize(rng.random((ch, cw), dtype=np.float32), (n.shape[1], n.shape[0]), interpolation=cv2.INTER_CUBIC)
            total += amp
            amp *= 0.5
            cw, ch = cw * 2, ch * 2
        self.clouds = cv2.GaussianBlur(n / total, (0, 0), 1.5)
        big = (H + 500, W + 800)
        self.smoke = [noise(big, 300, seed + 10, octaves=6, falloff=0.6), noise(big, 420, seed + 11, octaves=6, falloff=0.6)]
        self.fire = noise(big, 80, seed + 12, octaves=6, falloff=0.6)
        self.tree = noise((1, W + 800), 70, seed + 13, octaves=5)[0] * 28 + noise((1, W + 800), 700, seed + 14, octaves=3)[0] * 42
        layer = np.zeros((H, W + 400), dtype=np.float32)
        for _ in range(460):
            x = rng.uniform(-40, W + 440)
            h = rng.uniform(0.25, 1.0)
            lean = rng.uniform(-0.35, 0.35) * h
            pts = np.array([[x - rng.uniform(4, 12), H + 6], [x + lean * 150, H + 6 - h * 150], [x + rng.uniform(4, 12), H + 6]], dtype=np.int32)
            cv2.fillConvexPoly(layer, pts, 1.0, cv2.LINE_AA)
        self.grass = cv2.GaussianBlur(layer, (0, 0), 5)
        self.ember = dict(x=rng.uniform(0, W, embers), y=H * (low + (1 - low) * rng.beta(2.2, 1.4, embers)), v=rng.uniform(16, 70, embers), drift=rng.uniform(-14, 20, embers),
                          phase=rng.uniform(0, 6.28, embers), size=rng.uniform(1.2, 9, embers), value=rng.uniform(0.3, 1.8, embers) ** 2, colour=np.array(ember_colour, dtype=np.float32))
        self.bokeh = [(rng.uniform(0, W), rng.uniform(H * 0.3, H), rng.uniform(5, 16), rng.uniform(0.12, 0.34), rng.uniform(6, 22), rng.uniform(0, 6.28)) for _ in range(4)]


class Stage:
    def __init__(self, bake, i, dry=False):
        self.bake, self.i, self.t, self.dry = bake, i, i / FPS, dry
        self.frame = None
        self.cam = None
        self.sun = (960, 540)
        self.fog = np.array((0.85, 0.42, 0.2), dtype=np.float32)
        self.density = 0.05
        self.needs = set()
        self.base_light = dict(BACKLIT)

    # ------------------------------------------------------------ the world

    def world(self, cam, sun, stops=FIRE_SKY["stops"], fog=FIRE_SKY["fog"], ambient=0.035, gain=0.62, reach=300.0, cloud_shift=0.0, density=0.05, ground=True):
        self.cam, self.sun, self.fog, self.density = cam, sun, np.array(fog, dtype=np.float32), density
        if self.dry:
            return
        hy = cam.hy
        colours = [srgb(c) for c in stops]
        ys = np.clip(np.arange(H // 2) * 2 / max(hy + 10, 1), 0, 1)
        band = np.stack([np.interp(ys, [0, 0.55, 0.9, 1], [c[k] for c in colours]) for k in range(3)], axis=1).astype(np.float32)[:, None, :]
        sky = np.repeat(band, W // 2, axis=1)
        d = np.hypot((GRID2_X - sun[0]) / 1.7, GRID2_Y - sun[1])
        tint = np.array(self.bake.under, dtype=np.float32)
        sky = sky + (tint * 0.5 + np.array([0.5, 0.2, 0.09], dtype=np.float32) * (tint[0] > 0.6)) * (np.exp(-d / 280) * 0.55)[..., None]
        sky = sky + (np.array([1.0, 0.78, 0.48], dtype=np.float32) if tint[0] > 0.6 else np.array([0.75, 0.85, 1.0], dtype=np.float32)) * (np.exp(-d / 62) * 3.0)[..., None]
        ox = 400 - cloud_shift * 0.5 - (cam.cx - 960) * 0.1
        oy = 250
        M = np.array([[1, 0, -ox], [0, 1, -oy]], dtype=np.float32)
        n = cv2.warpAffine(self.bake.clouds, M, (W // 2, H // 2), borderMode=cv2.BORDER_REFLECT)
        M[1, 2] = -(oy - 30)
        lifted = cv2.warpAffine(self.bake.clouds, M, (W // 2, H // 2), borderMode=cv2.BORDER_REFLECT)
        cover = np.clip((n - 0.34) / 0.30, 0, 1) ** 1.2 * np.clip((hy - GRID2_Y) / 260 + 0.12, 0, 1)
        glow = np.exp(-np.hypot((GRID2_X - sun[0]) / 2.6, (GRID2_Y - sun[1]) * 1.15) / 430)
        underlit = np.clip((lifted - n) * 8 + 0.1, 0, 1)
        dark = srgb("#080b18") * (0.6 + 1.1 * n[..., None])
        colour = dark + tint * (underlit * glow * 0.40)[..., None] + np.array([0.010, 0.012, 0.022], dtype=np.float32) * underlit[..., None]
        sky = sky * (1 - cover[..., None]) + colour * cover[..., None]
        self.frame = cv2.resize(sky, (W, H), interpolation=cv2.INTER_LINEAR)
        if ground:
            self._ground(ambient, gain, reach)

    def _ground(self, ambient, gain, reach):
        cam, sun = self.cam, self.sun
        ss_w, ss_h = int(W * 1.5), int(H * 1.5)
        near, far, wide = cam.z + 0.6, Z1 - 0.5, 40.0
        src, dst = [], []
        for wx, wz in ((cam.x - wide, far), (cam.x + wide, far), (cam.x + wide * 0.1, near), (cam.x - wide * 0.1, near)):
            sx, sy, _ = cam.project(wx, wz)
            src.append([(wx - X0) * PX, (Z1 - wz) * PX])
            dst.append([sx * 1.5, sy * 1.5])
        M = cv2.getPerspectiveTransform(np.array(src, dtype=np.float32), np.array(dst, dtype=np.float32))
        out = cv2.warpPerspective(TEX, M, (ss_w, ss_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0.05, 0.07, 0.04))
        out = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
        d = np.hypot((GRID4_X - sun[0]) / 2.4, (GRID4_Y - cam.hy) * 1.5)
        light = cv2.resize(ambient + gain * np.exp(-d / reach), (W, H), interpolation=cv2.INTER_LINEAR)
        lum = out.mean(axis=2, keepdims=True)
        tone = np.array([1.25, 0.82, 0.56], dtype=np.float32) if self.fog[0] > self.fog[2] else np.array([0.62, 0.78, 1.15], dtype=np.float32)
        ground = (out * 0.55 + lum * 0.45) * light[..., None] * tone
        rows = np.arange(H, dtype=np.float32)
        haze = np.clip(1 - (rows - cam.hy) / 90, 0, 1) ** 2
        ground = ground * (1 - haze[:, None, None] * 0.6) + self.fog * 0.32 * cv2.resize(np.exp(-d / 620), (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * haze[:, None, None]
        mask = np.clip((rows - cam.hy) / 3, 0, 1)[:, None, None]
        self.frame = self.frame * (1 - mask) + ground * mask

    def treeline(self, colour="#0e1422", haze=0.16, scale=1.0):
        if self.dry:
            return
        hy = self.cam.hy
        shift = int(400 - (self.cam.x - 3.5) * 12)
        line = self.bake.tree[shift:shift + W] * scale
        y0, y1 = max(0, int(hy - 120)), min(H, int(hy + 8))
        if y1 <= y0:
            return
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        mask = np.clip((yy - (hy - line[None, :])) / 1.5, 0, 1) * np.clip((hy + 6 - yy) / 6, 0, 1)
        value = srgb(colour) + self.fog * haze
        self.frame[y0:y1] = self.frame[y0:y1] * (1 - mask[..., None]) + value * mask[..., None]

    # ------------------------------------------------------------ warriors

    def _sprite(self, name, pose, idx, size, light):
        res = 1500 if size > 640 else 750 if size > 270 else 375
        item = (name, pose, idx, res, key_of(light))
        if self.dry:
            self.needs.add(item)
            return None
        return SPR[item]

    def _light(self, light, sx):
        kw = dict(self.base_light)
        kw.update(light or {})
        if "rim_dir" not in kw:
            kw["rim_dir"] = (0.9 if self.sun[0] > sx else -0.9, -0.45)
        return kw

    def actors(self, items):
        """Warriors standing on the ground, far ones first, with their long shadows under all of them."""
        items = sorted(items, key=lambda a: -a["z"])
        shadow = None if self.dry else np.zeros((H // 2, W // 2), dtype=np.float32)
        ready = []
        for a in items:
            sx, sy, per = self.cam.project(a["x"], a["z"], a.get("wy", 0.0))
            size = SPRITE_TILES * per * a.get("scale", 1.0)
            if a["z"] - self.cam.z < 0.5 or sx < -size or sx > W + size:
                continue
            side = 1 if a["x"] < a.get("centre", 3.5) else -1
            light = self._light(a.get("light"), 0)
            light["rim_dir"] = a.get("rim_dir", (0.9 * side, -0.45))
            sprite = self._sprite(a["name"], a.get("pose", "idle"), a.get("idx", 0), size, light)
            ready.append((a, sprite, sx, sy, size))
            if self.dry or a.get("wy", 0.0) != 0.0 or not a.get("shadow", True):
                continue
            s = max(4, int(size / 2))
            alpha = cv2.resize(sprite[..., 3], (s, s), interpolation=cv2.INTER_AREA)
            if a.get("flip"):
                alpha = alpha[:, ::-1]
            lean = float(np.clip((sx - self.sun[0]) / 900, -1.4, 1.4))
            length = 0.62
            foot = int(s * FEET)
            M = np.array([[1, lean * length, sx / 2 - s / 2 - lean * length * foot], [0, -length, sy / 2 + foot * length]], dtype=np.float32)
            shadow = np.maximum(shadow, cv2.warpAffine(alpha, M, (W // 2, H // 2), flags=cv2.INTER_LINEAR))
        if self.dry:
            return
        shadow = cv2.resize(cv2.GaussianBlur(shadow, (0, 0), 3.0), (W, H), interpolation=cv2.INTER_LINEAR)
        self.frame *= (1 - np.clip(shadow, 0, 1) * 0.42)[..., None]
        for a, sprite, sx, sy, size in ready:
            d = a["z"] - self.cam.z
            fog = 1 - math.exp(-max(d - 1.5, 0) * self.density * 0.85)
            focus = a.get("focus", 1.9)
            blur = a.get("blur", min(11, abs(1 / d - 1 / focus) * 6))
            self._put(sprite, sx, sy, size, a.get("flip", False), fog, blur, a.get("motion"), a.get("tint"))

    def place(self, name, pose, idx, cx, feet, size, flip=False, light=None, blur=0.0, fog=0.0, motion=None, tint=None, rim_dir=None):
        """A warrior put straight on the picture, for close-ups."""
        kw = self._light(light, cx)
        if rim_dir is not None:
            kw["rim_dir"] = rim_dir
        sprite = self._sprite(name, pose, idx, size, kw)
        if not self.dry:
            self._put(sprite, cx, feet, size, flip, fog, blur, motion, tint)

    def _put(self, sprite, cx, feet, size, flip, fog, blur, motion, tint):
        s = int(max(6, round(size)))
        method = cv2.INTER_AREA if s < sprite.shape[0] else cv2.INTER_LINEAR
        small = cv2.resize(sprite, (s, s), interpolation=method)
        if flip:
            small = small[:, ::-1]
        c, a = small[..., :3], small[..., 3]
        if tint is not None:
            c = c * np.array(tint, dtype=np.float32)
        if fog > 0:
            c = c * (1 - fog) + self.fog * 0.34 * fog
        left, top = int(round(cx - s / 2)), int(round(feet - s * FEET))
        if blur > 0.3 or motion is not None:
            pad = int(blur * 4 + (max(abs(motion[0]), abs(motion[1])) if motion else 0)) + 2
            c = cv2.copyMakeBorder(c, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
            a = cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
            premult = c * a[..., None]
            if blur > 0.3:
                premult = cv2.GaussianBlur(premult, (0, 0), blur)
                a = cv2.GaussianBlur(a, (0, 0), blur)
            if motion is not None:
                length = int(max(abs(motion[0]), abs(motion[1]))) | 1
                kernel = np.zeros((length, length), dtype=np.float32)
                mid = length // 2
                cv2.line(kernel, (int(mid - motion[0] / 2), int(mid - motion[1] / 2)), (int(mid + motion[0] / 2), int(mid + motion[1] / 2)), 1.0, 1)
                kernel /= max(kernel.sum(), 1e-3)
                premult = cv2.filter2D(premult, -1, kernel)
                a = cv2.filter2D(a, -1, kernel)
            c = premult / np.maximum(a[..., None], 1e-3)
            left, top, s = left - pad, top - pad, s + pad * 2
        x0, y0 = max(left, 0), max(top, 0)
        x1, y1 = min(left + s, W), min(top + s, H)
        if x0 >= x1 or y0 >= y1:
            return
        cc = c[y0 - top:y1 - top, x0 - left:x1 - left]
        aa = a[y0 - top:y1 - top, x0 - left:x1 - left][..., None]
        self.frame[y0:y1, x0:x1] = self.frame[y0:y1, x0:x1] * (1 - aa) + cc * aa

    # ------------------------------------------------------------ air

    def smoke(self, y0, y1, amount=0.3, colour=(0.5, 0.22, 0.1), layer=0, speed=(14, -3), offset=0):
        if self.dry:
            return
        M = np.array([[1, 0, -400 + self.t * speed[0] + offset], [0, 1, -250 + self.t * speed[1]]], dtype=np.float32)
        n = cv2.warpAffine(self.bake.smoke[layer], M, (W, H), borderMode=cv2.BORDER_REFLECT)
        rows = np.arange(H, dtype=np.float32)
        shape = np.clip((rows - y0) / max(1, (y1 - y0) * 0.45), 0, 1) * np.clip((y1 - rows) / max(1, (y1 - y0) * 0.55), 0, 1)
        a = np.clip((n - 0.40) * 3.4, 0, 1) * shape[:, None] * amount
        self.frame = self.frame * (1 - a[..., None]) + np.array(colour, dtype=np.float32) * a[..., None]

    def rays(self, strength=0.5):
        if self.dry:
            return
        small = cv2.resize(self.frame, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bright = np.clip(small - 1.6, 0, 4)
        sx, sy = self.sun[0] / 4, self.sun[1] / 4
        out = np.zeros_like(bright)
        for k_i in range(24):
            k = 1 + k_i * 0.062
            M = np.array([[k, 0, sx * (1 - k)], [0, k, sy * (1 - k)]], dtype=np.float32)
            out += cv2.warpAffine(bright, M, (W // 4, H // 4)) * (0.91 ** k_i)
        out = cv2.resize(out / 24, (W, H), interpolation=cv2.INTER_LINEAR)
        self.frame += out * strength * np.array([1.0, 0.66, 0.36], dtype=np.float32)

    def grass(self, shift=0.0, darkness="#04060a", lift=0):
        if self.dry:
            return
        M = np.array([[1, 0, -200 + shift], [0, 1, lift]], dtype=np.float32)
        layer = cv2.warpAffine(self.bake.grass, M, (W, H))
        self.frame = self.frame * (1 - layer[..., None]) + srgb(darkness) * layer[..., None]

    def embers(self, amount=1.0, speed=1.0, wind=0.0):
        if self.dry:
            return
        e = self.bake.ember
        t = self.t * speed
        layer = np.zeros((H, W, 3), dtype=np.float32)
        x = (e["x"] + (e["drift"] + wind) * t + np.sin(t * 0.9 + e["phase"]) * 18) % W
        y = (e["y"] - e["v"] * t) % H
        for k in range(len(x)):
            dx, dy = (e["drift"][k] + wind) / 40, -e["v"][k] / 40
            p2 = (int(x[k] + dx * e["size"][k]), int(y[k] + dy * e["size"][k]))
            value = e["value"][k] * (0.65 + 0.35 * math.sin(t * 5 + e["phase"][k]))
            cv2.line(layer, (int(x[k]), int(y[k])), p2, tuple(float(v) * value for v in e["colour"]), 1, cv2.LINE_AA)
        soft = cv2.GaussianBlur(layer, (0, 0), 2.0)
        bokeh = np.zeros((H // 2, W // 2, 3), dtype=np.float32)
        for bx, by, r, v, sp, ph in self.bake.bokeh:
            cv2.circle(bokeh, (int(((bx + sp * t) % W) / 2), int(((by - sp * t * 1.6) % H) / 2)), int(r / 2), tuple(float(c) * v for c in e["colour"]), -1, cv2.LINE_AA)
        bokeh = cv2.resize(cv2.GaussianBlur(bokeh, (0, 0), 1.2), (W, H), interpolation=cv2.INTER_LINEAR)
        self.frame += (layer * 1.1 + soft * 1.6 + bokeh) * amount

    def rain(self, amount=0.5, angle=0.16):
        if self.dry:
            return
        rng = np.random.default_rng(self.i * 7 + 3)
        layer = np.zeros((H, W), dtype=np.float32)
        for _ in range(700):
            x, y = rng.uniform(-100, W + 100), rng.uniform(-100, H)
            length = rng.uniform(26, 90)
            cv2.line(layer, (int(x), int(y)), (int(x - angle * length), int(y + length)), float(rng.uniform(0.15, 1.0)), 1, cv2.LINE_AA)
        self.frame += cv2.GaussianBlur(layer, (0, 0), 0.7)[..., None] * np.array([0.6, 0.72, 0.95], dtype=np.float32) * amount

    def bolt(self, start, end, seed, width=3, colour=(0.72, 0.84, 1.0), amount=4.0, jag=60, branches=3):
        if self.dry or amount <= 0.01:
            return
        rng = np.random.default_rng(seed)
        layer = np.zeros((H // 1, W // 1, 3), dtype=np.float32)

        def strike(a, b, thick, jitter, level):
            steps = 14
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy) or 1
            points = []
            for k_i in range(steps + 1):
                k = k_i / steps
                off = 0 if k_i in (0, steps) else rng.normal(0, jitter) * math.sin(k * math.pi) ** 0.5
                points.append((a[0] + dx * k - dy / length * off, a[1] + dy * k + dx / length * off))
            cv2.polylines(layer, [np.array(points, dtype=np.int32)], False, tuple(float(v) * amount for v in colour), max(1, int(thick)), cv2.LINE_AA)
            if level > 0:
                for _ in range(branches):
                    k_i = rng.integers(3, steps - 2)
                    p = points[k_i]
                    far = (p[0] + rng.uniform(-0.45, 0.45) * length, p[1] + rng.uniform(0.1, 0.4) * length)
                    strike(p, far, max(1, thick * 0.5), jitter * 0.5, level - 1)

        strike(start, end, width, jag, 2)
        half = cv2.resize(layer, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        wide = cv2.GaussianBlur(half, (0, 0), 2.5) * 0.7 + cv2.GaussianBlur(half, (0, 0), 12) * 0.55 + cv2.GaussianBlur(half, (0, 0), 40) * 0.4
        self.frame += layer + cv2.resize(wide, (W, H), interpolation=cv2.INTER_LINEAR)

    def light(self, x, y, radius, colour, amount=1.0):
        if self.dry or amount <= 0:
            return
        d = np.hypot(GRID4_X - x, GRID4_Y - y)
        glow = cv2.resize(np.exp(-d / radius) * amount, (W, H), interpolation=cv2.INTER_LINEAR)
        self.frame += np.array(colour, dtype=np.float32) * glow[..., None]

    def wash(self, left, right):
        if self.dry:
            return
        k = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
        k = k * k * (3 - 2 * k)
        self.frame *= np.array(left, dtype=np.float32)[None, None] * (1 - k) + np.array(right, dtype=np.float32)[None, None] * k

    def zoom_blur(self, x, y, amount=0.05, samples=10):
        if self.dry or amount < 0.002:
            return
        out = np.zeros_like(self.frame)
        for k_i in range(samples):
            k = 1 + amount * k_i / samples
            M = np.array([[k, 0, x * (1 - k)], [0, k, y * (1 - k)]], dtype=np.float32)
            out += cv2.warpAffine(self.frame, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
        self.frame = out / samples

    def impact(self, x, y, age, seed=3, size=1.05, colour=(1.0, 0.62, 0.22)):
        """The moment two weapons meet. age counts frames since the hit."""
        if self.dry or age < 0:
            return
        rng = np.random.default_rng(seed)
        layer = np.zeros((H, W, 3), dtype=np.float32)
        speed = 26 / (1 + age * 0.45)
        travelled = sum(26 / (1 + a * 0.45) for a in range(int(age) + 1))
        for _ in range(int(150 * size)):
            angle = rng.uniform(0, 6.283)
            start = rng.uniform(4, 60) * size
            pace = rng.uniform(0.3, 1.4)
            length = rng.uniform(10, 40) * speed / 13 + 4
            value = rng.uniform(0.6, 4.5) * math.exp(-age / rng.uniform(10, 42))
            if value < 0.04:
                continue
            dist = start + travelled * pace * size
            fall = 0.018 * age * age
            a = (int(x + math.cos(angle) * dist), int(y + math.sin(angle) * dist * 0.8 + fall))
            b = (int(x + math.cos(angle) * (dist + length)), int(y + math.sin(angle) * (dist + length) * 0.8 + fall))
            cv2.line(layer, a, b, tuple(float(v) * value for v in colour), int(rng.integers(1, 4)), cv2.LINE_AA)
        self.frame += layer + cv2.GaussianBlur(layer, (0, 0), 5) * 1.2
        flash = math.exp(-age / 5.0)
        d = np.hypot(GRID4_X - x, (GRID4_Y - y) * 1.1) / size
        angle_map = np.arctan2(GRID4_Y - y, GRID4_X - x)
        spikes = 0.55 + 0.45 * np.cos(angle_map * 9 + 1.3) * np.cos(angle_map * 5 + 0.4)
        burst = np.exp(-d / (120 * spikes + 40)) * 3.2 * flash
        core = np.exp(-d / 26) * 12 * flash
        self.frame += np.array(colour, dtype=np.float32) * cv2.resize(burst, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        self.frame += np.array([1.0, 0.95, 0.85], dtype=np.float32) * cv2.resize(core, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        radius = 60 + travelled * 1.4
        ring = np.exp(-((d - radius) / (22 + age)) ** 2) * math.exp(-age / 34)
        ring = cv2.resize(ring, (W, H), interpolation=cv2.INTER_LINEAR)
        M = np.array([[1, 0, -400], [0, 1, -250]], dtype=np.float32)
        wob = cv2.warpAffine(self.bake.fire, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        a = (ring * np.clip(wob * 1.3, 0, 1) * 0.6)[..., None]
        self.frame = self.frame * (1 - a) + np.array([0.62, 0.42, 0.28], dtype=np.float32) * a

    def explosion(self, x, y, age, radius=240, seed=6):
        """A fireball, its smoke above it, and stones thrown out of it. age counts frames since it went off."""
        if self.dry or age < 0:
            return
        grow = 1 - math.exp(-age / 7.0)
        r = radius * (0.25 + 0.9 * grow)
        heat_left = math.exp(-age / 55.0)
        # Smoke rising.
        M = np.array([[1, 0, -400], [0, 1, -250 + age * 2.6]], dtype=np.float32)
        n = cv2.warpAffine(self.bake.smoke[1], M, (W, H), borderMode=cv2.BORDER_REFLECT)
        height = radius * (0.7 + age * 0.09)
        dy = np.clip((y + r * 0.3 - GRID_Y) / (height * 2.4), 0, 1)
        spread = r * (0.7 + dy * 1.3)
        column = np.exp(-((GRID_X - x - dy * 90) / spread) ** 2) * np.clip(1 - dy * 0.8, 0, 1) * (GRID_Y < y + r * 0.4) * min(1.0, age / 8.0)
        smoke = np.clip((n - 0.3) * 3.6, 0, 1) * column
        lit_smoke = srgb("#120d0d") + np.array([0.5, 0.17, 0.05], dtype=np.float32) * (np.exp(-np.maximum(y - GRID_Y, 0) / (r * 0.9)) * heat_left)[..., None]
        self.frame = self.frame * (1 - smoke[..., None] * 0.93) + lit_smoke * smoke[..., None] * 0.93
        # Fire.
        M = np.array([[1, 0, -400], [0, 1, -250 + age * 3.4]], dtype=np.float32)
        n2 = cv2.warpAffine(self.bake.fire, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        d = np.hypot(GRID_X - x, (GRID_Y - y) * 1.15) / r
        heat = np.clip((1.15 - d) + (n2 - 0.5) * 1.5, 0, 1.2) * heat_left
        fire = np.dstack([np.clip(heat * 3.6, 0, 7), np.clip((heat - 0.28) * 3.4, 0, 5), np.clip((heat - 0.72) * 3.2, 0, 3)]).astype(np.float32)
        a = np.clip(heat * 3.2, 0, 1)[..., None]
        self.frame = self.frame * (1 - a) + fire * a
        self.frame += np.array([1.0, 0.42, 0.12], dtype=np.float32) * (np.exp(-d / 1.4) * 0.8 * heat_left)[..., None]
        # Stones.
        rng = np.random.default_rng(seed + 3)
        stones = np.zeros((H, W), dtype=np.float32)
        for _ in range(70):
            angle = rng.uniform(-math.pi, 0.1)
            pace = rng.uniform(3.2, 16)
            size = rng.uniform(4, 26) * rng.random() ** 1.2 + 3
            spin = rng.uniform(-0.25, 0.25)
            slow = sum(1 / (1 + a_i * 0.05) for a_i in range(int(age)))
            cx = x + math.cos(angle) * pace * slow
            cy = y + math.sin(angle) * pace * slow * 0.85 + 0.03 * age * age
            pts = np.array([[cx + math.cos(k + spin * age) * size * rng.uniform(0.6, 1.2), cy + math.sin(k + spin * age) * size * rng.uniform(0.6, 1.2)] for k in np.linspace(0, 6.28, 6, endpoint=False)], dtype=np.int32)
            cv2.fillConvexPoly(stones, pts, 1.0, cv2.LINE_AA)
        self.frame = self.frame * (1 - stones[..., None]) + srgb("#0e0c0e") * stones[..., None]

    def footage(self, name, idx, colour=(1.12, 0.84, 0.55), pool=(900, 700), pool_size=470, pool_gain=0.5, floor=0.035, grey=0.4, zoom=1.0, anchor=540, dy=0):
        """A frame of the real game in the film's light. anchor is the row that stays put while it zooms; dy moves it out from under the black bars."""
        if self.dry:
            return
        raw = CLIPS[name][idx]
        f = (raw.astype(np.float32) / 255) ** 2.2
        if zoom != 1.0 or dy:
            M = np.array([[zoom, 0, 960 * (1 - zoom)], [0, zoom, anchor * (1 - zoom) + dy]], dtype=np.float32)
            f = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        lum = f.mean(axis=2, keepdims=True)
        f = (f * (1 - grey) + lum * grey) * np.array(colour, dtype=np.float32)
        p = np.exp(-(np.hypot((GRID4_X - pool[0]) / 1.3, GRID4_Y - pool[1]) / pool_size) ** 1.5)
        f *= cv2.resize(floor + pool_gain * p, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        self.frame = f

    def vignette(self, amount=0.55):
        if self.dry:
            return
        d = np.hypot((GRID4_X - W / 2) / (W / 2), (GRID4_Y - H / 2) / (H / 2))
        self.frame *= cv2.resize(1 - amount * np.clip(d - 0.42, 0, 1) ** 1.6 * 1.7, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]

    def finish(self, exposure=1.0, teal=0.09, fade=1.0, roll=0.0, dx=0.0, dy=0.0, zoom=1.0, grain=0.007):
        if self.dry:
            return None
        f = self.frame
        if roll or dx or dy or zoom != 1.0:
            M = cv2.getRotationMatrix2D((960, 540), roll, zoom)
            M[0, 2] += dx
            M[1, 2] += dy
            f = cv2.warpAffine(f, M.astype(np.float32), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        f = f * exposure
        small = cv2.resize(f, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        bright = np.clip(small - 1.0, 0, 8)
        bloom = cv2.GaussianBlur(bright, (0, 0), 7) * 0.5 + cv2.GaussianBlur(bright, (0, 0), 25) * 0.35
        f = f + cv2.resize(bloom, (W, H), interpolation=cv2.INTER_LINEAR)
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        f = np.clip((f * (a * f + b)) / (f * (c * f + d) + e), 0, 1)
        out = f ** (1 / 2.2)
        lum = out.mean(axis=2, keepdims=True)
        out = out + (1 - lum) ** 2 * np.array([-0.5, 0.05, 0.28], dtype=np.float32) * teal
        ox, oy = (self.i * 37) % 64, (self.i * 23) % 64
        out = out + GRAIN[oy:oy + H, ox:ox + W] * grain
        out = np.clip(out * fade, 0, 1)
        return (out * 255 + 0.5).astype(np.uint8).tobytes()


CLIPS = {}


def clip(name, frames):
    if name not in CLIPS:
        CLIPS[name] = np.memmap(CUTS + name + ".rgb", dtype=np.uint8, mode="r", shape=(frames, H, W, 3))
    return CLIPS[name]


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots.py")).read())


# ---------------------------------------------------------------- running it

_shot = None
_bake = None


def _frame(i):
    stage = Stage(_bake, i)
    return _shot["draw"](stage, i)


def prepare(name):
    global _shot, _bake, TEX
    _shot = SHOTS[name]
    _bake = Bake(**_shot.get("bake", {}))
    if TEX is None and _shot.get("ground", True):
        TEX = cv2.GaussianBlur(texture(), (0, 0), 1.2)
    for clip_name, frames in _shot.get("clips", {}).items():
        clip(clip_name, frames)
    # Find out which warrior pictures this shot needs, light any that are new, and hold them in memory for the workers.
    needs = set()
    for i in range(_shot["frames"]):
        dry = Stage(_bake, i, dry=True)
        _shot["draw"](dry, i)
        needs |= dry.needs
    os.makedirs(CACHE, exist_ok=True)
    fresh = [item for item in needs if not os.path.exists(cache_path(item))]
    if fresh:
        with mp.get_context("fork").Pool(10) as pool:
            pool.map(make_sprite, fresh, chunksize=4)
    SPR.clear()
    for item in needs:
        SPR[item] = np.load(cache_path(item)).astype(np.float32)
    print(name, "needs", len(needs), "pictures,", len(fresh), "new,", "%.1f GB" % (sum(a.nbytes for a in SPR.values()) / 1e9), flush=True)


def sample(names, count=9):
    sheet_w, cols = 640, 3
    for name in names:
        prepare(name)
        n = _shot["frames"]
        picks = [int(n * (k + 0.5) / count) for k in range(count)]
        rows = (len(picks) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * sheet_w, rows * 360), (30, 30, 30))
        with mp.get_context("fork").Pool(8) as pool:
            frames = pool.map(_frame, picks)
        for k, data in enumerate(frames):
            im = Image.frombuffer("RGB", (W, H), data, "raw", "RGB", 0, 1).resize((sheet_w - 4, 356), Image.LANCZOS)
            sheet.paste(im, ((k % cols) * sheet_w + 2, (k // cols) * 360 + 2))
        os.makedirs(SCRATCH + "/samples", exist_ok=True)
        sheet.save(SCRATCH + "/samples/%s.jpg" % name, quality=88)
        print("sampled", name, flush=True)


def render(names):
    os.makedirs(OUT, exist_ok=True)
    for name in names:
        started = time.time()
        prepare(name)
        n = _shot["frames"]
        ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                               "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "13", "-g", "15", "-bf", "0",
                               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", OUT + name + ".mp4"], stdin=subprocess.PIPE)
        with mp.get_context("fork").Pool(9) as pool:
            for k, data in enumerate(pool.imap(_frame, range(n), chunksize=2)):
                ff.stdin.write(data)
                if k % 60 == 0:
                    print(name, k, "of", n, "%.0fs" % (time.time() - started), flush=True)
        ff.stdin.close()
        code = ff.wait()
        print("rendered", name, n, "frames in %.0fs" % (time.time() - started), "ffmpeg exit", code, flush=True)


if __name__ == "__main__":
    mode = sys.argv[1]
    chosen = sys.argv[2:] or list(SHOTS)
    (sample if mode == "sample" else render)(chosen)
