#!/usr/bin/env python3
"""Every still of the promo's battle look. Usage: python3 tools/plates.py [names]"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "plates") + "/"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "shots8k") + "/"   # 8K stills from promo_shots.gd
Image.MAX_IMAGE_PIXELS = None

CSE = ["compiler", "kernel", "algorithmist", "optimizer", "logic-bomber", "debugger", "stack-runner", "cloud-drone"]
EEE = ["capacitor", "transformer", "signal-processor", "circuit-engineer", "oscillator", "power-engineer", "relay-runner", "electron"]
ME = ["heavy-machine", "gearwheel-guard", "robotic-arm", "steel-rain-cannon", "mech-warrior", "gear-runner", "mini-bot", "quadcopter"]
CE = ["excavator", "road-roller", "site-engineer", "crane-operator", "seismic-crew", "surveyor", "construction-crew", "survey-drone"]

FIRE_KEY = dict(key=(0.95, 0.62, 0.40), fill=(0.06, 0.08, 0.13), rim=(1.0, 0.55, 0.22), rim_amount=3.2, key_dir=(0.5, -0.5, 0.6))
COLD_KEY = dict(key=(0.42, 0.62, 1.0), fill=(0.05, 0.08, 0.16), rim=(0.5, 0.8, 1.0), rim_amount=3.4, key_dir=(0.5, -0.5, 0.6))


def army(s, names, lanes, front, back, per, seed, focus, spread=0.7, poses=("run", "hit"), light=None):
    r = random.Random(seed)
    units = []
    for lane in lanes:
        z = back
        while z > front:
            units.append((z + r.uniform(-0.3, 0.3), lane + r.uniform(-spread, spread), r.choice(names), r.choice(poses)))
            z -= per
    for z, x, name, pose in sorted(units, reverse=True):
        s.warrior(name, x, z, pose=pose, focus=focus, light=light)


def charge():
    cam = Camera(x=3.5, z=-3.2, height=0.62, focal=1050, horizon=660)
    s = Scene(cam, sun=(1000, 628))
    s.treeline(height=26)
    s.castle("ce", 3.5, 12.4, scale=3.2)
    s.smoke(cam.hy - 46, cam.hy + 20, amount=0.34, colour=(0.5, 0.22, 0.1))
    army(s, CE, (1.5, 5.5), 1.2, 11, 1.05, 4, 1.9)
    army(s, CE, (3.5,), 3.5, 8, 1.0, 5, 1.9)
    s.smoke(cam.hy + 4, cam.hy + 120, amount=0.22, cell=340, seed=8, colour=(0.4, 0.19, 0.1))
    s.warrior("road-roller", 5.1, -0.2, pose="hit", focus=1.9, light=dict(key=(0.34, 0.3, 0.3), fill=(0.05, 0.06, 0.1)))
    s.warrior("excavator", 2.55, -1.3, pose="hit", focus=1.9, light=FIRE_KEY)
    s.rays(0.8)
    s.foreground()
    s.embers()
    s.vignette(0.6)
    s.finish(OUT + "charge.jpg", exposure=1.1)


def faceoff():
    cam = Camera(x=5.5, z=2.2, height=0.5, focal=900, horizon=610)
    s = Scene(cam, sun=(960, 575), sky=("#070b1c", "#17182c", "#a8421c", "#ffb060"), seed=3)
    s.treeline(height=24)
    s.castle("me", 5.5, 13.2, scale=2.4)
    s.smoke(cam.hy - 40, cam.hy + 16, amount=0.3, colour=(0.5, 0.22, 0.1))
    far = [(3.2, 8.4), (4.2, 8.9), (6.8, 8.9), (7.8, 8.4), (2.6, 9.4), (8.4, 9.4), (3.6, 10), (7.4, 10)]
    r = random.Random(2)
    for x, z in far:
        names = CSE if x < 5.5 else ME
        s.warrior(r.choice(names), x, z, pose="hit", focus=3.2, light=COLD_KEY if x < 5.5 else None)
    s.smoke(cam.hy - 10, cam.hy + 70, amount=0.18, cell=300, seed=9, colour=(0.42, 0.2, 0.1))
    s.bolt((960, -20), (960, 560), seed=5, width=3, colour=(0.95, 0.86, 0.7), amount=4)
    s.wash((0.48, 0.72, 1.35), (1.25, 0.82, 0.55))
    s.place("compiler", "hit", 480, 1050, 1120, light=COLD_KEY)
    s.place("heavy-machine", "hit", 1450, 1050, 1120, flip=True, light=FIRE_KEY)
    s.rays(0.5)
    s.foreground(seed=5, height=100)
    s.embers(count=60, seed=12)
    s.vignette(0.62)
    s.finish(OUT + "faceoff.jpg", exposure=1.08)


def champion():
    cam = Camera(x=3.5, z=-3, height=0.5, focal=1000, horizon=1040)
    s = Scene(cam, sun=(420, 760), sky=("#04060f", "#0d1224", "#2a3560", "#7d93d8"), fog=(0.3, 0.42, 0.8), seed=8)
    s.smoke(500, 1090, amount=0.5, colour=(0.09, 0.12, 0.22), cell=420, seed=4)
    s.bolt((1010, -20), (1180, 760), seed=11, width=3, colour=(1.0, 0.92, 0.5), amount=3.2, jag=50, branches=2)
    s.place("capacitor", "hit", 1450, 1420, 1800, light=dict(key=(0.62, 0.55, 0.36), fill=(0.03, 0.04, 0.09), rim=(0.85, 0.85, 1.0), rim_amount=3.4, key_dir=(-0.6, -0.45, 0.6), rim_dir=(-0.9, -0.4)))
    s.embers(count=70, seed=15, colour=(1.0, 0.82, 0.3), low=0.2)
    s.vignette(0.55)
    s.finish(OUT + "champion.jpg", exposure=1.05)


def clash():
    cam = Camera(x=1.5, z=3.0, height=0.5, focal=1050, horizon=540)
    s = Scene(cam, sun=(960, 480), seed=6)
    s.treeline(height=24)
    s.castle("eee", 3.5, 13, scale=2.2)
    s.smoke(cam.hy - 40, cam.hy + 24, amount=0.3, colour=(0.5, 0.22, 0.1))
    for name, x, z in (("signal-processor", 0.9, 7.4), ("relay-runner", 2.3, 7.8), ("mini-bot", 0.5, 8.6), ("robotic-arm", 2.6, 8.9)):
        s.warrior(name, x, z, pose="hit", focus=1.6)
    s.zoom_blur(960, 520, amount=0.1)
    s.place("mech-warrior", "hit", 640, 1050, 1420, light=FIRE_KEY)
    s.place("transformer", "hit", 1290, 1050, 1420, flip=True, light=dict(key=(1.0, 0.8, 0.45), fill=(0.06, 0.08, 0.13), rim=(1.0, 0.62, 0.25), rim_amount=3.2, key_dir=(-0.5, -0.5, 0.6)))
    s.impact(965, 640, seed=3, size=1.05)
    s.foreground(seed=7, height=90)
    s.embers(count=120, seed=16)
    s.vignette(0.55)
    # The whole shot tipped a little, as if the camera were knocked.
    s.frame = cv2.warpAffine(s.frame, cv2.getRotationMatrix2D((960, 540), -3.2, 1.075), (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    s.finish(OUT + "clash.jpg", exposure=1.05)


def graded(src, box, out, seed=1, action=(900, 720), colour=(1.12, 0.8, 0.5)):
    """Real game footage, kept sharp, in the film's light: a pool of firelight on the fight, night everywhere else."""
    im = Image.open(SHOTS + src + ".png").convert("RGB").crop(box).resize((W, H), Image.LANCZOS)
    s = Scene.__new__(Scene)
    s.frame = (np.asarray(im).astype(np.float32) / 255) ** 2.2
    lum = s.frame.mean(axis=2, keepdims=True)
    s.frame = (s.frame * 0.6 + lum * 0.4) * np.array(colour, dtype=np.float32)
    s.sun = (960, 540)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    pool = np.exp(-(np.hypot((xx - action[0]) / 1.3, yy - action[1]) / 470) ** 1.5)
    s.frame *= (0.035 + 0.5 * pool)[..., None]
    s.frame *= np.clip((yy - 40) / 330, 0.28, 1)[..., None]
    s.add_light(action[0], action[1] + 190, 180, (1.0, 0.38, 0.09), 0.22)
    s.smoke(680, 1120, amount=0.18, colour=(0.1, 0.05, 0.03), cell=330, seed=seed)
    s.embers(count=120, seed=seed + 3)
    s.finish(OUT + out, exposure=1.15, teal=0.16)


def gameplay():
    graded("s2300", (2760, 2680, 4920, 3895), "gameplay.jpg", seed=2)


def table():
    """Dark wooden boards in firelight, for the warriors' cards to lie on."""
    s = Scene.__new__(Scene)
    n = noise((H, W), 300, 21, octaves=6)
    grain = cv2.resize(noise((H, 240), 16, 22, octaves=4), (W, H), interpolation=cv2.INTER_CUBIC)
    wood = srgb("#6b4423") * (0.35 + 0.9 * grain[..., None]) * (0.6 + 0.8 * n[..., None])
    for x in range(-60, W, 318):
        cv2.line(wood, (x, 0), (x + 40, H), (0.004, 0.003, 0.002), 6, cv2.LINE_AA)
    s.frame = wood.astype(np.float32)
    s.sun = (960, 300)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    pool = np.exp(-np.hypot((xx - 960) / 1.5, yy - 600) / 420)
    s.frame = s.frame * (0.05 + 1.5 * pool[..., None]) * np.array([1.15, 0.8, 0.55], dtype=np.float32)
    s.embers(count=70, seed=31, low=0.1)
    s.vignette(0.8)
    s.finish(OUT + "table.jpg", exposure=1.0, teal=0.1)


def power():
    cam = Camera(x=3.5, z=-3.0, height=0.6, focal=1000, horizon=690)
    cold = dict(key=(0.2, 0.28, 0.5), fill=(0.04, 0.06, 0.13), rim=(0.55, 0.78, 1.0), rim_amount=3.4)
    s = Scene(cam, sun=(960, 650), sky=("#050814", "#10183a", "#34508f", "#a7c4ee"), fog=(0.35, 0.5, 0.9), seed=11, light=cold)
    s.treeline(height=26, colour="#080c1c")
    s.castle("cse", 3.5, 12.4, scale=3.0)
    s.smoke(cam.hy - 44, cam.hy + 20, amount=0.3, colour=(0.2, 0.3, 0.55))
    r = random.Random(9)
    mix = EEE + ME + CSE + CE
    army(s, mix, (1.4, 3.5, 5.6), 1.6, 10.5, 0.86, 7, 1.8, spread=0.8, poses=("run",))
    s.smoke(cam.hy + 8, cam.hy + 130, amount=0.2, cell=320, seed=19, colour=(0.15, 0.2, 0.36))
    s.bolt((700, -20), (985, 660), seed=21, width=3, colour=(0.72, 0.84, 1.0), amount=4)
    s.bolt((1520, -20), (1690, 720), seed=24, width=2, colour=(0.72, 0.84, 1.0), amount=3, jag=60, branches=2)
    s.bolt((130, -20), (250, 740), seed=27, width=2, colour=(0.72, 0.84, 1.0), amount=1.8, jag=50, branches=2)
    s.warrior("stack-runner", 5.0, -0.9, pose="run", focus=1.9, light=COLD_KEY)
    s.warrior("relay-runner", 1.85, -0.9, pose="run", focus=1.9, light=dict(COLD_KEY, key=(1.0, 0.9, 0.6)))
    s.rain()
    s.foreground(seed=9, height=120)
    s.vignette(0.6)
    s.finish(OUT + "power.jpg", exposure=1.15, teal=0.05)


def castle_falls():
    cam = Camera(x=3.9, z=3.6, height=0.55, focal=1200, horizon=800)
    s = Scene(cam, sun=(1180, 1400), sky=("#020409", "#08080f", "#170b09", "#351408"), fog=(0.5, 0.2, 0.08), seed=14)
    s.treeline(height=18, colour="#020307")
    s.explosion(1210, 500, radius=240)
    s.place("castle-eee", "ruin", 1210, 884, 860, light=dict(key=(0.5, 0.26, 0.14), fill=(0.03, 0.03, 0.05), rim=(1.0, 0.5, 0.16), rim_amount=4.0, rim_dir=(0.0, -1.0), radius=70, key_dir=(0.0, -0.8, 0.5)))
    s.smoke(cam.hy - 44, cam.hy + 30, amount=0.32, colour=(0.2, 0.08, 0.03), seed=14)
    for name, x, wz in (("site-engineer", 6.4, 9.2), ("surveyor", 1.7, 8.9), ("seismic-crew", 2.5, 7.9)):
        s.warrior(name, x, wz, pose="hit", focus=1.8)
    s.place("excavator", "hit", 400, 1050, 1120, light=dict(FIRE_KEY, key=(0.4, 0.25, 0.18), rim_amount=4.2, rim_dir=(0.95, -0.3)))
    s.embers(count=240, seed=41, low=0.05)
    s.foreground(seed=11, height=70)
    s.vignette(0.5)
    s.finish(OUT + "castle.jpg", exposure=1.0)


def title():
    cam = Camera(x=3.5, z=-3.0, height=0.6, focal=1000, horizon=835)
    s = Scene(cam, sun=(960, 800), sky=("#04060e", "#0f0f1a", "#6e2810", "#f09040"), seed=17)
    s.treeline(height=24, colour="#05070e")
    s.smoke(cam.hy - 70, cam.hy + 14, amount=0.28, colour=(0.4, 0.17, 0.07))
    groups = ((CSE, 250, (0.45, 0.7, 1.0)), (EEE, 725, (1.0, 0.86, 0.35)), (ME, 1195, (1.0, 0.55, 0.22)), (CE, 1670, (0.72, 0.55, 1.0)))
    r = random.Random(12)
    for names, cx, rim in groups:
        light = dict(key=(0.15, 0.16, 0.22), fill=(0.03, 0.035, 0.06), rim=rim, rim_amount=3.8, rim_dir=(0.9 if cx < 960 else -0.9, -0.5))
        for i, name in enumerate(names[4:]):
            s.place(name, "idle", cx - 172 + i * 115 + r.uniform(-6, 6), 880, 330, flip=cx > 960, light=light, blur=1.0, fog=0.22)
        for i, name in enumerate(names[:4]):
            s.place(name, "hit", cx - 165 + i * 110 + r.uniform(-6, 6), 985, 470, flip=cx > 960, light=light)
    s.rays(0.65)
    s.foreground(seed=13, height=60)
    s.embers(count=100, seed=44, low=0.1)
    s.vignette(0.6)
    s.finish(OUT + "title.jpg", exposure=1.15)


def lit_cards():
    """The warriors for the cards, lit by the fire, kept as pictures with see-through backgrounds."""
    from light import lit as light_it
    warm = dict(key=(1.0, 0.8, 0.58), fill=(0.14, 0.15, 0.22), rim=(1.0, 0.6, 0.26), rim_amount=1.8, key_dir=(-0.4, -0.6, 0.65), rim_dir=(0.9, -0.4))
    for name, pose in (("compiler", "hit"), ("logic-bomber", "idle"), ("stack-runner", "run"), ("cloud-drone", "run")):
        colour, alpha = light_it(os.path.join(HERO, "%s_%s.png" % (name, pose)), **warm)
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        f = colour * 1.15
        f = np.clip((f * (a * f + b)) / (f * (c * f + d) + e), 0, 1) ** (1 / 2.2)
        Image.fromarray((np.dstack([f, alpha]) * 255).round().astype(np.uint8)).save(OUT + "../lit/%s.png" % name)


ALL = dict(charge=charge, faceoff=faceoff, champion=champion, clash=clash, gameplay=gameplay, table=table, power=power, castle=castle_falls, title=title, cards=lit_cards)
for name in sys.argv[1:] or ALL:
    ALL[name]()
    print("made", name)
