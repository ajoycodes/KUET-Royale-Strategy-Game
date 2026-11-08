# The film, shot by shot. Read by film.py. One bar is 60 frames, 2 seconds.
import random


def march(names, lanes, seed, step=1.05):
    r = random.Random(seed)
    units = []
    for lane, far, near in lanes:
        z = far
        while z > near:
            units.append(dict(name=r.choice(names), x=lane + r.uniform(-0.7, 0.7), z=z + r.uniform(-0.3, 0.3), phase=r.random(), pose="run"))
            z -= step
    return units


CE_ARMY = march(CE, ((1.5, 16.0, 6.6), (5.5, 16.0, 6.6), (3.5, 15.5, 8.6)), 4)
CSE_ARMY = march(CSE, ((1.5, 2.2, -3.4), (5.5, 2.2, -3.4)), 9, step=0.8)
STORM_ARMY = march(EEE + ME + CSE + CE, ((1.4, 22, 8), (3.5, 22, 9), (5.6, 22, 8)), 7, step=0.9)


def run_frame(t, rate=1.2, phase=0.0):
    return int((t * rate + phase) * RUN) % RUN


def stand_frame(t, phase=0.0, step=1):
    return (int((t * 0.5 + phase) * STAND) // step * step) % STAND


def hit_frame(age):
    """The attack, slower at its peak. age in frames since it began."""
    return int(np.clip(age, 0, HIT - 1))


def shake(age, size=7.0, decay=6.0):
    if age < 0:
        return 0.0, 0.0, 0.0
    k = math.exp(-age / decay)
    return math.sin(age * 2.3) * size * k, math.cos(age * 3.1) * size * k, math.sin(age * 1.7) * size * 0.07 * k


# ---------------------------------------------------------------- 0:00 to 0:14, one long take

def battlefield(s, i):
    t = i / FPS
    push = ss(0, 300, i)
    crane = ss(300, 405, i)
    z = lerp(lerp(0.6, 2.6, push), -7.2, crane)
    h = lerp(lerp(0.56, 0.62, push), 7.6, crane)
    hy = lerp(660, 130, crane)
    cam = Camera(x=3.5, z=z, height=h, focal=lerp(1050, 900, crane), horizon=hy)
    s.world(cam, (1000, hy - 32), ambient=lerp(0.035, 0.42, crane), gain=lerp(0.62, 0.5, crane), reach=lerp(300, 1400, crane), cloud_shift=t * 14, density=lerp(0.05, 0.012, crane))
    s.treeline(scale=0.8)
    s.smoke(hy - 46, hy + 20, amount=0.34 * (1 - crane * 0.7))
    fort = dict(radius=60)
    far = [dict(name="castle-ce", pose="whole", x=3.5, z=12.4, scale=2.3, light=fort, shadow=False, focus=1.9)]
    for u in CE_ARMY:
        far.append(dict(u, z=u["z"] + (10 - t) * 0.5, idx=run_frame(t, 1.15, u["phase"]), focus=1.9))
    s.actors(far)
    s.smoke(hy + 4, hy + 120, amount=0.22 * (1 - crane * 0.8), layer=1, colour=(0.4, 0.19, 0.1), speed=(-10, -2))
    near = [dict(name="castle-cse", pose="whole", x=3.5, z=0.7, scale=2.3, light=fort, shadow=False, blur=0)]
    for u in CSE_ARMY:
        near.append(dict(u, z=u["z"] + max(0, t - 10) * 0.5, idx=run_frame(t, 1.15, u["phase"]), blur=0, light=dict(rim=(0.5, 0.75, 1.0), rim_amount=3.0)))
    # The two who step into the frame.
    roller_in = eout(170, 210, i)
    roller_age = i - 210
    near.append(dict(name="road-roller", x=lerp(8.6, 5.1, roller_in), z=5.6, pose="run" if i < 210 else ("hit" if roller_age < HIT else "idle"),
                     idx=run_frame(t, 1.2) if i < 210 else (hit_frame(roller_age) if roller_age < HIT else stand_frame(t)), focus=1.9,
                     light=dict(key=(0.34, 0.3, 0.3), fill=(0.05, 0.06, 0.1)), rim_dir=(-0.9, -0.45)))
    digger_in = eout(200, 240, i)
    digger_age = i - 240
    near.append(dict(name="excavator", x=lerp(-1.6, 2.55, digger_in), z=4.5, pose="run" if i < 240 else ("hit" if digger_age < HIT else "idle"),
                     idx=run_frame(t, 1.6) if i < 240 else (hit_frame(digger_age) if digger_age < HIT else stand_frame(t)), focus=1.9, light=FIRE_KEY, rim_dir=(0.9, -0.45), tint=(0.8, 0.8, 1.04)))
    s.actors(near)
    s.rays(0.8 * (1 - crane))
    s.grass(shift=t * 3, lift=crane * 220)
    if not s.dry:
        s.frame *= ss(40, 115, i)
    s.embers()
    s.vignette(lerp(0.6, 0.72, crane))
    a, b, c = shake(digger_age, 8)
    a2, b2, c2 = shake(roller_age, 4)
    return s.finish(exposure=1.1, dx=a + a2, dy=b + b2, roll=c + c2, zoom=1.012)


# ---------------------------------------------------------------- 0:14 to 0:22

FACE_FAR = [(3.2, 8.4, "algorithmist"), (4.2, 8.9, "optimizer"), (6.8, 8.9, "robotic-arm"), (7.8, 8.4, "mech-warrior"), (2.6, 9.4, "debugger"), (8.4, 9.4, "mini-bot"), (3.6, 10, "kernel"), (7.4, 10, "gearwheel-guard")]


def faceoff(s, i):
    t = i / FPS
    cam = Camera(x=5.5, z=lerp(1.8, 2.5, i / 240), height=0.5, focal=900, horizon=610)
    s.world(cam, (960, 575), stops=("#070b1c", "#17182c", "#a8421c", "#ffb060"), cloud_shift=t * 16)
    s.treeline(scale=0.8)
    s.smoke(564, 626, amount=0.3)
    far = [dict(name="castle-me", pose="whole", x=5.5, z=13.2, scale=2.4, light=dict(radius=60), shadow=False, focus=3.2)]
    for x, z, name in FACE_FAR:
        far.append(dict(name=name, x=x, z=z, pose="idle", idx=stand_frame(t, x, 2), focus=3.2, light=COLD_KEY if x < 5.5 else None, centre=5.5))
    s.actors(far)
    s.smoke(600, 680, amount=0.18, layer=1, colour=(0.42, 0.2, 0.1), speed=(-12, -2))
    strike = i - 180
    second = i - 225
    flick = (5.0 if 0 <= strike < 5 else 2.4 if 7 <= strike < 10 else 1.2 if 13 <= strike < 15 else 0.0) + (3.0 if 0 <= second < 3 else 1.4 if 5 <= second < 7 else 0.0) + (1.3 if i in (140, 141, 143) else 0.0)
    s.bolt((960, -20), (960, 560), seed=5 + (0 if i < 200 else 1), colour=(0.95, 0.86, 0.7), amount=flick)
    s.wash((0.48, 0.72, 1.35), (1.25, 0.82, 0.55))
    swell = lerp(1120, 1190, i / 240)
    blue_in = eout(15, 45, i)
    orange_in = eout(90, 120, i)
    if i >= 15:
        walking = i < 45
        pose = "run" if walking else ("hit" if 0 <= strike < HIT else "idle")
        s.place("compiler", pose, run_frame(t, 1.1) if walking else (hit_frame(strike) if 0 <= strike < HIT else stand_frame(t)), lerp(-420, 470, blue_in), 1125, swell, light=COLD_KEY, rim_dir=(0.9, -0.45))
    if i >= 90:
        walking = i < 120
        pose = "run" if walking else ("hit" if 0 <= strike < HIT else "idle")
        s.place("heavy-machine", pose, run_frame(t, 0.9) if walking else (hit_frame(strike) if 0 <= strike < HIT else stand_frame(t)), lerp(2340, 1460, orange_in), 1125, swell, flip=True, light=FIRE_KEY, rim_dir=(0.9, -0.45))
    s.rays(0.5)
    s.grass(shift=t * 3)
    s.embers(amount=0.9)
    s.vignette(0.62)
    a, b, c = shake(strike, 9, 7)
    a2, b2, c2 = shake(i - 120, 6, 5)
    a3, b3, c3 = shake(i - 45, 5, 5)
    return s.finish(exposure=1.08 * (1 + (0.9 * math.exp(-strike / 5.0) if strike >= 0 else 0)), dx=a + a2 + a3, dy=b + b2 + b3, roll=c, zoom=1.012, fade=ss(-1, 8, i))


# ---------------------------------------------------------------- 0:22 to 0:26

def champion(s, i):
    t = i / FPS
    cam = Camera(x=3.5, z=-3, height=0.5, focal=1000, horizon=1040)
    s.world(cam, (250, 1500), stops=("#04060f", "#0a0f20", "#1c2748", "#3f5392"), fog=(0.3, 0.42, 0.8), cloud_shift=t * 26, ground=False)
    s.smoke(500, 1090, amount=0.5, colour=(0.09, 0.12, 0.22), layer=1, speed=(26, -5))
    flick = 3.2 if i in (0, 1, 3, 60, 62, 105, 106, 108) else 1.4 if i in (2, 5, 64, 110) else 0.0
    s.bolt((1010, -20), (1180, 760), seed=11 + i // 50, colour=(1.0, 0.92, 0.5), amount=flick, jag=50, branches=2)
    size = lerp(1760, 1880, i / 120)
    s.place("capacitor", "idle", stand_frame(t), 1450, lerp(1395, 1450, i / 120), size, rim_dir=(-0.9, -0.4),
            light=dict(key=(0.62, 0.55, 0.36), fill=(0.03, 0.04, 0.09), rim=(0.85, 0.85, 1.0), rim_amount=3.4, key_dir=(-0.6, -0.45, 0.6)))
    s.light(1230, 900, 170, (1.0, 0.85, 0.3), 0.1 + 0.05 * math.sin(t * 7))
    s.embers(amount=0.8, speed=1.0)
    s.vignette(0.55)
    return s.finish(exposure=1.05 * (1.35 if flick > 2 else 1.0), fade=ss(-1, 6, i))


# ---------------------------------------------------------------- 0:26 to 0:30, the hit lands on 0:28

def clash(s, i):
    t = i / FPS
    age = i - 60
    cam = Camera(x=1.5, z=lerp(3.0, 3.3, i / 120), height=0.5, focal=1050, horizon=540)
    s.world(cam, (960, 480), cloud_shift=t * 22)
    s.treeline(scale=0.8)
    s.smoke(500, 564, amount=0.3)
    far = [dict(name="castle-eee", pose="whole", x=3.5, z=13, scale=2.2, light=dict(radius=60), shadow=False, focus=1.6)]
    for name, x, z in (("signal-processor", 0.9, 7.4), ("relay-runner", 2.3, 7.8), ("mini-bot", 0.5, 8.6), ("robotic-arm", 2.6, 8.9)):
        far.append(dict(name=name, x=x, z=z, pose="idle", idx=stand_frame(t, x, 2), focus=1.6, centre=1.5))
    s.actors(far)
    if age >= 0:
        s.zoom_blur(960, 520, amount=0.12 * math.exp(-age / 9.0) + 0.012)
    else:
        s.zoom_blur(960, 520, amount=0.012 + 0.03 * ss(30, 60, i))
    run_in = eout(0, 60, i) ** 1.5
    recoil = (1 - math.exp(-max(age, 0) / 8.0)) * 34
    left_x = lerp(-520, 640, run_in) - recoil
    right_x = lerp(2440, 1290, run_in) + recoil
    if i < 50:
        pose, idx = "run", run_frame(t, 2.2)
    else:
        pose, idx = "hit", hit_frame((i - 50) * 0.45 if age < 0 else 4.5 + age * 0.12)
    streak = 22
    motion = (streak, 0) if i < 50 else None
    s.place("mech-warrior", pose, idx, left_x, 1050, 1420, light=FIRE_KEY, rim_dir=(0.9, -0.45), motion=motion)
    s.place("transformer", pose, idx, right_x, 1050, 1420, flip=True, rim_dir=(-0.9, -0.45), motion=motion,
            light=dict(key=(1.0, 0.8, 0.45), fill=(0.06, 0.08, 0.13), rim=(1.0, 0.62, 0.25), rim_amount=3.2, key_dir=(-0.5, -0.5, 0.6)))
    s.impact(965, 640, age)
    s.grass(shift=t * 4)
    s.embers(amount=1.2, wind=30 if age > 0 else 0)
    s.vignette(0.55)
    a, b, c = shake(age, 16, 8)
    return s.finish(exposure=1.05 * (1 + (1.4 * math.exp(-age / 3.0) if age >= 0 else 0)), roll=-3.2 + c, zoom=1.075 + (0.05 * math.exp(-age / 10.0) if age >= 0 else 0), dx=a, dy=b, fade=ss(-1, 5, i))


# ---------------------------------------------------------------- 0:30 to 0:34, the real game

def siege(s, i):
    s.footage("siege", min(i, 120), colour=(1.22, 0.8, 0.46), grey=0.42, pool=(880, 700), pool_size=430, pool_gain=0.46, floor=0.03, zoom=lerp(1.0, 1.07, i / 120), anchor=1076, dy=-96)
    s.light(880, 900, 170, (1.0, 0.36, 0.08), 0.16 + 0.04 * math.sin(i * 0.5))
    s.smoke(680, 1120, amount=0.18, colour=(0.1, 0.05, 0.03))
    s.embers(amount=1.1)
    return s.finish(exposure=1.1, teal=0.1, fade=ss(-1, 5, i))


# ---------------------------------------------------------------- 0:34 to 0:38, the cards

WOOD = {}


def wood():
    if "floor" not in WOOD:
        n = noise((H, W), 300, 21, octaves=6)
        grain = cv2.resize(noise((H, 240), 16, 22, octaves=4), (W, H), interpolation=cv2.INTER_CUBIC)
        floor = srgb("#6b4423") * (0.35 + 0.9 * grain[..., None]) * (0.6 + 0.8 * n[..., None])
        for x in range(-60, W, 318):
            cv2.line(floor, (x, 0), (x + 40, H), (0.004, 0.003, 0.002), 6, cv2.LINE_AA)
        WOOD["floor"] = floor.astype(np.float32)
    return WOOD["floor"]


def cards_table(s, i):
    floor = wood()
    if s.dry:
        return None
    t = i / FPS
    flame = 1 + 0.1 * math.sin(t * 7.1) + 0.06 * math.sin(t * 13.7 + 1) + 0.04 * math.sin(t * 23)
    pool = np.exp(-np.hypot((GRID4_X - 960 - 26 * math.sin(t * 2)) / 1.5, GRID4_Y - 600) / (420 * flame))
    s.frame = floor * cv2.resize(0.05 + 1.5 * pool * flame, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * np.array([1.15, 0.8, 0.55], dtype=np.float32)
    s.embers(amount=0.9, speed=0.8)
    s.vignette(0.8)
    return s.finish(exposure=1.0, teal=0.1, zoom=lerp(1.0, 1.05, i / 120), fade=ss(-1, 6, i))


# ---------------------------------------------------------------- 0:38 to 0:50, power mode

def storm(s, i):
    t = i / FPS
    hit = i - 60
    cam = Camera(x=3.5, z=lerp(0.4, 1.3, i / 120), height=0.6, focal=1000, horizon=690)
    s.base_light = dict(COLD_BACK)
    s.world(cam, (960, 650), stops=COLD_SKY["stops"], fog=COLD_SKY["fog"], cloud_shift=t * 40)
    s.treeline(colour="#080c1c", scale=0.8)
    s.smoke(646, 710, amount=0.3, colour=(0.2, 0.3, 0.55))
    far = [dict(name="castle-cse", pose="whole", x=3.5, z=12.4, scale=2.5, light=dict(radius=60), shadow=False, focus=1.8)]
    for u in STORM_ARMY:
        z = u["z"] - t * 1.5
        far.append(dict(u, z=z, idx=run_frame(t, 2.0, u["phase"]), focus=1.8))
    s.actors(far)
    s.smoke(698, 820, amount=0.2, layer=1, colour=(0.15, 0.2, 0.36), speed=(-40, -2))
    flick = (1.6 if i in (10, 11, 13) else 0) + (2.6 if i in (34, 35, 37) else 0)
    s.bolt((1520, -20), (1690, 720), seed=24, colour=(0.72, 0.84, 1.0), amount=flick, jag=60, branches=2)
    big = 5.5 if 0 <= hit < 5 else 2.8 if 7 <= hit < 11 else 1.2 if 14 <= hit < 16 else 0.0
    s.bolt((700, -20), (985, 660), seed=21, width=3, colour=(0.72, 0.84, 1.0), amount=big)
    s.bolt((130, -20), (250, 740), seed=27, width=2, colour=(0.72, 0.84, 1.0), amount=2.4 if 90 <= i < 94 else 0.0, jag=50, branches=2)
    runners = []
    if i > 60:
        lead = eout(60, 118, i)
        runners.append(dict(name="stack-runner", x=5.0, z=lerp(11, cam.z + 2.0, lead), idx=run_frame(t, 2.6), pose="run", focus=1.9, light=COLD_KEY, rim_dir=(-0.9, -0.45)))
        runners.append(dict(name="relay-runner", x=1.85, z=lerp(12, cam.z + 2.0, lead), idx=run_frame(t, 2.6, 0.4), pose="run", focus=1.9, rim_dir=(0.9, -0.45), light=dict(COLD_KEY, key=(1.0, 0.9, 0.6))))
    s.actors(runners)
    s.rain()
    s.grass(shift=t * 40, darkness="#03050b")
    s.vignette(0.6)
    a, b, c = shake(hit, 14, 7)
    dim = lerp(0.55, 1.15, ss(58, 61, i))
    return s.finish(exposure=dim * (1 + (1.6 * math.exp(-hit / 3.0) if hit >= 0 else 0) + (0.5 if flick else 0)), teal=0.05, dx=a, dy=b, roll=c, zoom=1.012, fade=ss(-1, 6, i))


def real_cold(name):
    def draw(s, i):
        s.footage(name, min(i, 60), colour=(0.5, 0.72, 1.3), grey=0.5, pool=(960, 600), pool_size=520, pool_gain=0.38, floor=0.024, zoom=lerp(1.0, 1.08, i / 60), anchor=96 if name == "upper" else 540, dy=70 if name == "upper" else 0)
        s.rain(amount=0.4)
        flash = 2.4 * math.exp(-i / 2.5)
        return s.finish(exposure=1.1 * (1 + flash), teal=0.03)
    return draw


def rush(s, i):
    t = i / FPS
    cam = Camera(x=1.5, z=2.2, height=0.42, focal=1000, horizon=640)
    s.base_light = dict(COLD_BACK)
    s.world(cam, (1100, 600), stops=COLD_SKY["stops"], fog=COLD_SKY["fog"], cloud_shift=t * 50)
    s.treeline(colour="#080c1c", scale=0.8)
    pack = []
    for k, (name, x, delay, rate) in enumerate((("stack-runner", 1.25, 0, 11.0), ("gear-runner", 1.85, 10, 10.0), ("relay-runner", 1.1, 20, 12.0), ("construction-crew", 2.0, 28, 11.0))):
        age = i - delay
        z = 12.5 - rate * (age / FPS)
        d = z - cam.z
        if d > 0.55:
            blur_len = min(70, 6 / max(d, 0.5) ** 1.8)
            pack.append(dict(name=name, x=x, z=z, pose="run", idx=run_frame(t, 3.0, k * 0.3), blur=0.0, light=COLD_KEY, rim_dir=(0.9 if x < 1.5 else -0.9, -0.45), motion=(0, blur_len) if blur_len > 3 else None, centre=1.5))
    far = []
    for u in STORM_ARMY[:20]:
        far.append(dict(u, x=u["x"] - 2.0, z=u["z"] * 0.7 - t * 2.0, idx=run_frame(t, 2.0, u["phase"]), focus=2.0, centre=1.5))
    s.actors(far)
    s.smoke(600, 730, amount=0.26, colour=(0.15, 0.22, 0.4), speed=(-60, -2))
    s.bolt((1500, -20), (1360, 650), seed=33, colour=(0.72, 0.84, 1.0), amount=4.0 if i in (2, 3, 5) else 1.8 if i in (8, 9) else 0.0, jag=50, branches=2)
    s.actors(pack)
    s.rain(amount=0.6, angle=0.05)
    s.vignette(0.6)
    return s.finish(exposure=1.15 * (1 + 1.0 * math.exp(-i / 2.5)), teal=0.05, roll=math.sin(i * 0.4) * 0.6, zoom=1.02)


def last_blow(s, i):
    s.footage("last", min(i, 60), colour=(1.22, 0.78, 0.44), grey=0.4, pool=(960, 720), pool_size=470, pool_gain=0.44, floor=0.03, zoom=lerp(1.0, 1.1, i / 60), anchor=1076, dy=-96)
    s.light(960, 900, 190, (1.0, 0.36, 0.08), 0.2)
    s.embers(amount=1.4)
    return s.finish(exposure=1.1 * (1 + 2.0 * math.exp(-i / 2.5)), teal=0.1)


# ---------------------------------------------------------------- 0:50 to 0:54, the bang is on 0:51

def castle_falls(s, i):
    t = i / FPS
    age = i - 30
    cam = Camera(x=3.9, z=3.6, height=0.55, focal=1200, horizon=800)
    s.world(cam, (1180, 1400), stops=("#020409", "#08080f", "#170b09", "#351408"), fog=(0.5, 0.2, 0.08), cloud_shift=t * 20)
    s.treeline(colour="#020307", haze=0.1, scale=0.7)
    if age >= 0:
        s.explosion(1210, 500, age)
    fort = dict(key=(0.5, 0.26, 0.14), fill=(0.03, 0.03, 0.05), rim=(1.0, 0.5, 0.16), rim_amount=4.0, radius=70, key_dir=(0.0, -0.8, 0.5))
    if age < 0:
        s.place("castle-eee", "whole", 0, 1210, 884, 860, light=fort, rim_dir=(0.0, -1.0))
        for at, x, y in ((0, 1120, 620), (15, 1310, 560)):
            s.impact(x, y, i - at, seed=at, size=0.55, colour=(1.0, 0.55, 0.18))
    else:
        s.place("castle-eee", "ruin", 0, 1210, 884, 860, light=fort, rim_dir=(0.0, -1.0))
    s.smoke(756, 830, amount=0.32, colour=(0.2, 0.08, 0.03), speed=(18, -4))
    s.actors([dict(name=name, x=x, z=z, pose="idle", idx=stand_frame(t, x, 2), focus=1.8, centre=3.9) for name, x, z in (("site-engineer", 6.4, 9.2), ("surveyor", 1.7, 8.9), ("seismic-crew", 2.5, 7.9))])
    s.place("excavator", "hit" if age < HIT and age >= 0 else "idle", hit_frame(age) if 0 <= age < HIT else stand_frame(t), 400, 1050, lerp(1120, 1190, i / 120), rim_dir=(0.95, -0.3),
            light=dict(FIRE_KEY, key=(0.4, 0.25, 0.18), rim_amount=4.2), tint=(0.8, 0.8, 1.04))
    s.embers(amount=lerp(1.0, 2.4, ss(30, 50, i)), wind=26 if age > 0 else 0)
    s.grass(shift=t * 3)
    s.vignette(0.5)
    a, b, c = shake(age, 24, 11)
    return s.finish(exposure=1.0 * (1 + (1.8 * math.exp(-age / 3.5) if age >= 0 else 0)), dx=a, dy=b, roll=c, zoom=1.02, fade=ss(-1, 4, i))


# ---------------------------------------------------------------- 0:54 to 1:00, the title

TITLE_ROWS = [(CSE, 250, (0.45, 0.7, 1.0)), (EEE, 725, (1.0, 0.86, 0.35)), (ME, 1195, (1.0, 0.55, 0.22)), (CE, 1670, (0.72, 0.55, 1.0))]


def title(s, i):
    t = i / FPS
    rise = ss(0, 180, i)
    hy = lerp(862, 835, rise)
    cam = Camera(x=3.5, z=-3.0, height=0.6, focal=1000, horizon=hy)
    s.world(cam, (960, hy - 35), stops=("#04060e", "#0f0f1a", "#6e2810", "#f09040"), cloud_shift=t * 10)
    s.treeline(colour="#05070e", scale=0.8)
    s.smoke(hy - 70, hy + 14, amount=0.28, colour=(0.4, 0.17, 0.07), speed=(10, -2))
    lift = hy - 835
    r = random.Random(12)
    for names, cx, rim in TITLE_ROWS:
        light = dict(key=(0.15, 0.16, 0.22), fill=(0.03, 0.035, 0.06), rim=rim, rim_amount=3.8)
        rim_dir = (0.9 if cx < 960 else -0.9, -0.5)
        for k, name in enumerate(names[4:]):
            s.place(name, "idle", stand_frame(t, k * 0.2 + cx, 2), cx - 172 + k * 115 + r.uniform(-6, 6), 880 + lift * 0.7, 330, flip=cx > 960, light=light, blur=1.0, fog=0.22, rim_dir=rim_dir)
        for k, name in enumerate(names[:4]):
            # The front ranks raise their weapons when the title lands, and on every bar after it.
            age = (i - 30 - k * 2) % BAR if i >= 30 else 99
            cheer = age < HIT
            s.place(name, "hit" if cheer else "idle", hit_frame(age) if cheer else stand_frame(t, k * 0.3 + cx, 2), cx - 165 + k * 110 + r.uniform(-6, 6), 985 + lift, 470, flip=cx > 960, light=light, rim_dir=rim_dir)
    # Dust from the fall of the castle, settling.
    dust = 0.75 * (1 - ss(0, 70, i))
    s.smoke(100, 1100, amount=dust, colour=(0.2, 0.1, 0.05), layer=1, speed=(12, 6))
    s.rays(0.65)
    s.grass(shift=t * 2, lift=12)
    s.embers(amount=0.9, speed=0.7)
    s.vignette(0.6)
    return s.finish(exposure=1.15, fade=ss(0, 18, i) * (1 - ss(158, 178, i)))


SHOTS = dict(
    a_battlefield=dict(draw=battlefield, frames=420, bake=dict(seed=1)),
    b_faceoff=dict(draw=faceoff, frames=240, bake=dict(seed=3)),
    c_champion=dict(draw=champion, frames=120, bake=dict(seed=8, under=(0.32, 0.46, 1.0), ember_colour=(1.0, 0.82, 0.3), low=0.2)),
    d_clash=dict(draw=clash, frames=120, bake=dict(seed=6, embers=140)),
    e_siege=dict(draw=siege, frames=120, bake=dict(seed=2, embers=110), clips=dict(siege=121)),
    f_cards=dict(draw=cards_table, frames=120, bake=dict(seed=31, low=0.1)),
    g_storm=dict(draw=storm, frames=120, bake=dict(seed=11, under=(0.32, 0.46, 1.0), embers=4)),
    h_real1=dict(draw=real_cold("bridge"), frames=60, bake=dict(seed=12, embers=4), clips=dict(bridge=61)),
    i_rush=dict(draw=rush, frames=60, bake=dict(seed=13, under=(0.32, 0.46, 1.0), embers=4)),
    j_real2=dict(draw=real_cold("upper"), frames=60, bake=dict(seed=14, embers=4), clips=dict(upper=61)),
    k_lastblow=dict(draw=last_blow, frames=60, bake=dict(seed=15, embers=120), clips=dict(last=61)),
    l_castle=dict(draw=castle_falls, frames=120, bake=dict(seed=14, embers=240, low=0.05)),
    m_title=dict(draw=title, frames=180, bake=dict(seed=17, embers=100, low=0.1)),
)
