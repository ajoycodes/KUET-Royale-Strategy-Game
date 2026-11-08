#!/usr/bin/env python3
"""The film's score and sound effects, made entirely from code: 60.0 seconds at 120 beats a minute.

    python3 tools/battle_music.py public/battle.wav

Every hit below is timed to something on screen. Times are seconds in the finished film.
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

RATE = 48000
BEAT = 0.5
BAR = 2.0
LENGTH = 60.0
N = int(RATE * LENGTH)
rng = np.random.default_rng(120)


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def at(seconds):
    return int(round(seconds * RATE))


def low(x, cut, order=2):
    return sosfilt(butter(order, min(cut, RATE * 0.45), "low", fs=RATE, output="sos"), x, axis=0)


def high(x, cut, order=2):
    return sosfilt(butter(order, cut, "high", fs=RATE, output="sos"), x, axis=0)


def band(x, a, b, order=2):
    return sosfilt(butter(order, [a, min(b, RATE * 0.45)], "band", fs=RATE, output="sos"), x, axis=0)


def put(track, start, sound, gain=1.0):
    begin = at(start)
    if begin >= N or begin < 0:
        return
    end = min(N, begin + len(sound))
    track[begin:end] += sound[:end - begin] * gain


def st(mono, pan=0.0):
    a = (pan + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)], axis=1)


def noise(seconds):
    return rng.standard_normal(at(seconds))


def saws(note, seconds, voices=5, spread=0.14):
    """Several slightly detuned saw waves: the body of strings, brass and choir."""
    t = np.arange(at(seconds)) / RATE
    out = np.zeros_like(t)
    for k in range(voices):
        detune = spread * (k / max(voices - 1, 1) * 2 - 1)
        out += 2 * ((t * hz(note + detune) + rng.random()) % 1.0) - 1
    return out / voices


# ---------------------------------------------------------------- instruments

def taiko(note=38, seconds=0.75, skin=0.25):
    t = np.arange(at(seconds)) / RATE
    sweep = hz(note) * (1 + 1.6 * np.exp(-t / 0.018))
    body = np.sin(2 * np.pi * np.cumsum(sweep) / RATE) * np.exp(-t / 0.2)
    body += 0.45 * np.sin(2 * np.pi * np.cumsum(sweep * 1.52) / RATE) * np.exp(-t / 0.1)
    hit = band(noise(seconds), 90, 1100) * np.exp(-t / 0.024) * skin * 4
    return np.tanh((body + hit) * 1.5)


def frame_drum(seconds=0.22):
    t = np.arange(at(seconds)) / RATE
    return band(noise(seconds), 220, 2800) * np.exp(-t / 0.05) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)


def strings_hit(note, seconds):
    """A short bowed note for the running figure."""
    t = np.arange(at(seconds)) / RATE
    x = saws(note, seconds, 3, 0.1) + 0.5 * saws(note + 12, seconds, 3, 0.1)
    return low(x, 2100, 2) * np.minimum(t / 0.006, 1) * np.exp(-t / (seconds * 0.55))


def brass(note, seconds, bright=2600, level=1.0):
    t = np.arange(at(seconds)) / RATE
    x = saws(note, seconds, 5, 0.09) + 0.6 * saws(note - 12, seconds, 3, 0.07)
    # The filter opens as the note speaks, as a real horn does.
    cut = 480 + (bright - 480) * np.minimum(t / 0.16, 1) ** 0.7
    blocks = []
    size = 512
    state = None
    from scipy.signal import sosfilt_zi
    for k in range(0, len(x), size):
        sos = butter(2, min(cut[min(k, len(cut) - 1)], RATE * 0.45), "low", fs=RATE, output="sos")
        if state is None:
            state = sosfilt_zi(sos) * x[0]
        part, state = sosfilt(sos, x[k:k + size], zi=state)
        blocks.append(part)
    x = np.concatenate(blocks)
    env = np.minimum(t / 0.035, 1) * np.minimum((seconds - t) / 0.09, 1)
    return np.tanh(x * env * 1.5) * level


def choir(notes, seconds, gain=1.0):
    """An 'ah': saw waves through the three formants of the vowel."""
    t = np.arange(at(seconds)) / RATE
    x = np.zeros_like(t)
    for note in notes:
        x += saws(note, seconds, 7, 0.16)
    x /= len(notes)
    voice = band(x, 620, 880) * 1.0 + band(x, 1000, 1300) * 0.55 + band(x, 2400, 2900) * 0.3
    env = np.minimum(t / 0.55, 1) ** 1.5 * np.minimum((seconds - t) / 0.9, 1) ** 1.2
    return voice * env * gain * 3.2


def drone(notes, seconds, cut=420):
    t = np.arange(at(seconds)) / RATE
    x = np.zeros_like(t)
    for note in notes:
        x += saws(note, seconds, 5, 0.12)
    x = low(x / len(notes), cut, 2)
    return x * np.minimum(t / 1.1, 1) ** 1.3 * np.minimum((seconds - t) / 1.1, 1) ** 1.2


def braam(seconds=3.2, root=26):
    """The huge low brass hit of a film trailer."""
    t = np.arange(at(seconds)) / RATE
    x = saws(root, seconds, 7, 0.2) + saws(root + 12, seconds, 7, 0.2) + 0.7 * saws(root + 19, seconds, 5, 0.18) + 0.45 * saws(root + 24, seconds, 5, 0.18)
    cut = 300 + 3400 * np.exp(-t / 0.5)
    blocks = []
    size = 512
    from scipy.signal import sosfilt_zi
    state = None
    for k in range(0, len(x), size):
        sos = butter(2, cut[min(k, len(cut) - 1)], "low", fs=RATE, output="sos")
        if state is None:
            state = sosfilt_zi(sos) * 0
        part, state = sosfilt(sos, x[k:k + size], zi=state)
        blocks.append(part)
    x = np.tanh(np.concatenate(blocks) * 1.2)
    return x * np.minimum(t / 0.02, 1) * np.exp(-t / (seconds * 0.42))


def boom(seconds=2.8, start=78, end=30, gain=1.0):
    t = np.arange(at(seconds)) / RATE
    sweep = end + (start - end) * np.exp(-t / 0.13)
    sub = np.sin(2 * np.pi * np.cumsum(sweep) / RATE) * np.exp(-t / (seconds * 0.34))
    air = low(noise(seconds), 2400) * np.exp(-t / 0.17) * 0.5
    return np.tanh((sub + air) * 1.5) * gain


def clang(seconds=2.4, base=1.0):
    """Metal on metal: partials that do not fit any note."""
    t = np.arange(at(seconds)) / RATE
    out = np.zeros_like(t)
    for ratio, decay, level in ((523, 0.75, 1.0), (1231, 0.55, 0.9), (2113, 0.42, 0.7), (3170, 0.3, 0.55), (4389, 0.2, 0.42), (5621, 0.13, 0.3), (7103, 0.09, 0.2)):
        out += np.sin(2 * np.pi * ratio * base * t + rng.random() * 6) * np.exp(-t / decay) * level
    out += high(noise(seconds), 2500) * np.exp(-t / 0.012) * 1.6
    return out / 2.2


def thunder(seconds=5.0, crack=1.0):
    t = np.arange(at(seconds)) / RATE
    sharp = high(noise(seconds), 900) * np.exp(-t / 0.05) * crack
    grain = low(noise(seconds), 2400) * np.exp(-t / 0.28) * crack * 0.9
    wobble = low(np.abs(noise(seconds)), 7, 1)
    wobble = wobble / np.max(wobble)
    roll = low(noise(seconds), 240, 2) * wobble * np.exp(-t / (seconds * 0.34)) * 3.6
    return (sharp + grain + roll) * np.minimum(t / 0.002, 1)


def explosion(seconds=6.0):
    t = np.arange(at(seconds)) / RATE
    blast = low(noise(seconds), 1700, 2) * np.exp(-t / 0.5) * 2.2
    top = high(noise(seconds), 1400) * np.exp(-t / 0.1) * 1.4
    sub = np.sin(2 * np.pi * np.cumsum(26 + 74 * np.exp(-t / 0.2)) / RATE) * np.exp(-t / 1.7) * 2.2
    out = np.tanh(blast + top + sub)
    # Stones falling after it.
    for _ in range(90):
        when = 0.25 + rng.random() ** 0.7 * 3.2
        s = at(when)
        length = at(0.04)
        tick = band(rng.standard_normal(length), 500, 3800) * np.exp(-np.arange(length) / RATE / 0.012) * rng.uniform(0.04, 0.3) * np.exp(-when / 2.0)
        out[s:s + length] += tick
    return out


def riser(seconds, top=7000):
    t = np.arange(at(seconds)) / RATE
    k = t / seconds
    x = high(noise(seconds), 300)
    cut = 300 * (top / 300) ** k
    blocks = []
    size = 512
    from scipy.signal import sosfilt_zi
    state = None
    for j in range(0, len(x), size):
        sos = butter(2, cut[min(j, len(cut) - 1)], "low", fs=RATE, output="sos")
        if state is None:
            state = sosfilt_zi(sos) * 0
        part, state = sosfilt(sos, x[j:j + size], zi=state)
        blocks.append(part)
    return np.concatenate(blocks) * k ** 2.4


def fire_crackle(seconds, density=26):
    out = low(noise(seconds), 620) * 0.14
    for _ in range(int(seconds * density)):
        s = at(rng.random() * (seconds - 0.05))
        length = at(0.012)
        out[s:s + length] += high(rng.standard_normal(length), 1800) * np.exp(-np.arange(length) / RATE / 0.003) * rng.uniform(0.1, 0.9)
    return out


# ---------------------------------------------------------------- the score

CHORDS = {
    "Dm": (38, [62, 65, 69]), "Bb": (34, [62, 65, 70]), "F": (41, [60, 65, 69]), "C": (36, [60, 64, 67]),
    "Gm": (43, [62, 67, 70]), "A": (33, [61, 64, 69]), "D": (38, [62, 66, 69]),
}
# One entry per bar: 30 bars of 2 seconds.
SONG = ["Dm", "Dm", "Dm", "Dm", "Dm", "Bb", "C", "Dm", "Dm", "Bb", "A", "Dm", "F", "Gm", "A", "Dm", "Bb", "Gm", "A", "A",
        "Dm", "Bb", "F", "C", "A", "A", "Dm", "Dm", "Dm", "Dm"]
RUNNING = [0, 0, 12, 0, 7, 0, 12, 7, 0, 0, 12, 0, 10, 7, 12, 10]      # the string figure, in semitones over the root
MOTIF = [(0, 62, 1.5), (1.5, 62, 0.25), (1.75, 65, 0.25), (2, 69, 1), (3, 67, 0.5), (3.5, 65, 0.5), (4, 64, 1), (5, 60, 1), (6, 62, 2)]    # beats x 0.5, in 8 beats... in bars


def main(path):
    drums = np.zeros((N, 2))
    strings = np.zeros((N, 2))
    horns = np.zeros((N, 2))
    voices = np.zeros((N, 2))
    low_end = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    air = np.zeros((N, 2))

    # The ground: a low drone under everything except the two held breaths.
    runs = [(0, 7, "Dm"), (7, 11, "Dm"), (11, 13, "Dm"), (13, 15, "Gm"), (15, 17, "Dm"), (17, 19, "Gm"), (19, 20, "A"), (20, 25, "Dm"), (25, 30, "Dm")]
    for a, b, name in runs:
        root = CHORDS[name][0]
        put(low_end, a * BAR, st(drone([root, root + 7], (b - a) * BAR + 1.0, 300 if a < 20 else 520)), 0.3)

    # The running strings.
    def running(start_bar, end_bar, level, step=0.125):
        for b in range(start_bar, end_bar):
            root = CHORDS[SONG[b]][0] + 12
            for k in range(int(BAR / step)):
                note = root + RUNNING[k % len(RUNNING)]
                put(strings, b * BAR + k * step, st(strings_hit(note, step * 1.4), -0.35 if k % 2 else 0.35), level)

    running(2, 7, 0.13)         # creeping in under the first words
    running(7, 11, 0.12)
    running(13, 15, 0.16)       # the charge to the clash
    running(15, 17, 0.2)        # the real game
    running(20, 25, 0.24)       # power mode
    running(27, 29, 0.1)

    # The war drums.
    def groove(start_bar, end_bar, level, busy):
        for b in range(start_bar, end_bar):
            t0 = b * BAR
            put(drums, t0, st(taiko(36)), level)
            put(drums, t0 + 1.0, st(taiko(40), 0.1), level * 0.8)
            if busy >= 1:
                put(drums, t0 + 0.75, st(taiko(45, 0.45), -0.3), level * 0.55)
                put(drums, t0 + 1.5, st(taiko(40), -0.1), level * 0.75)
            if busy >= 2:
                for k in range(8):
                    put(drums, t0 + k * 0.25, st(frame_drum(), 0.35 if k % 2 else -0.35), level * (0.24 if k % 4 else 0.38))
                put(drums, t0 + 1.75, st(taiko(45, 0.45), 0.3), level * 0.55)
            if busy >= 3:
                for k in range(16):
                    put(drums, t0 + k * 0.125, st(frame_drum(0.1), -0.2 if k % 2 else 0.2), level * 0.14)

    for t0 in (4.0, 6.0):
        put(drums, t0, st(taiko(33, 1.0)), 0.5)
    groove(4, 7, 0.34, 0)
    groove(7, 11, 0.42, 1)
    groove(15, 17, 0.62, 2)
    groove(20, 25, 0.72, 3)

    # A roll that climbs into the clash on 28.0.
    for k in range(32):
        when = 26.0 + k * (2.0 / 32)
        put(drums, when, st(frame_drum(0.16), -0.25 if k % 2 else 0.25), 0.1 + 0.42 * (k / 32) ** 2)
    for k in range(8):
        put(drums, 27.0 + k * 0.125, st(taiko(44 + k // 2, 0.4)), 0.22 + 0.06 * k)

    # Horns: the tune.
    def tune(start, level, octave=0, bright=2600):
        for beat, note, length in ((0, 62, 3), (3, 62, 0.5), (3.5, 65, 0.5), (4, 69, 2), (6, 67, 1), (7, 65, 1), (8, 64, 2), (10, 60, 2), (12, 62, 4)):
            put(horns, start + beat * BEAT, st(brass(note + octave, length * BEAT + 0.08, bright), 0.08), level)

    tune(22.0, 0.15, -12, 1300)                        # one horn, for the champion
    tune(40.0, 0.24, 0, 3000)                          # everyone, for power mode
    for beat, note, length in ((0, 69, 3), (3, 69, 0.5), (3.5, 72, 0.5), (4, 74, 4)):
        put(horns, 48.0 + beat * BEAT, st(brass(note - 12, length * BEAT + 0.08, 3200)), 0.2)
    # Chord stabs behind the tune.
    for b in range(20, 25):
        _, notes = CHORDS[SONG[b]]
        for when in (0.0, 0.75, 1.5):
            for note in notes:
                put(horns, b * BAR + when, st(brass(note - 12, 0.3, 2000), -0.3), 0.07)

    # Voices.
    for start, seconds, notes, level in ((10.0, 4.4, (62, 69, 74), 0.1), (20.0, 2.4, (61, 64, 69), 0.09), (22.0, 4.2, (62, 65, 69), 0.1), (28.0, 2.4, (57, 64, 69), 0.09),
                                         (40.0, 10.4, (62, 69, 74), 0.13), (51.0, 3.3, (50, 57, 62), 0.13), (55.0, 5.2, (62, 69, 74, 81), 0.17)):
        put(voices, start, st(choir(notes, seconds)), level)

    # ------------------------------------------------------------ what happens on screen

    put(air, 0.0, st(low(noise(14.0), 560, 2) * np.minimum(np.arange(at(14.0)) / RATE / 2.0, 1) * np.minimum((14.0 - np.arange(at(14.0)) / RATE) / 3.0, 1)), 0.1)
    put(fx, 1.0, st(riser(3.0, 2600)), 0.07)
    put(fx, 4.0, st(boom(3.0, 66, 28)), 0.5)                    # FOUR ARMIES.
    put(fx, 4.0, st(braam(3.0)), 0.16)
    put(fx, 7.0, st(boom(1.6, 80, 32)), 0.34)                   # the roller lands
    put(fx, 8.0, st(boom(1.8, 74, 30)), 0.42)                   # the excavator lands
    put(fx, 8.0, st(clang(1.4, 0.7), -0.4), 0.05)
    # An army's rumble, growing until the camera rises.
    rumble = low(noise(11.0), 170, 2) * np.minimum(np.arange(at(11.0)) / RATE / 7.0, 1) ** 1.4
    put(air, 3.0, st(rumble), 0.42)
    put(fx, 8.5, st(riser(2.5, 5200)), 0.1)
    put(fx, 11.0, st(braam(3.2)), 0.34)                         # ONE BATTLEFIELD.
    put(fx, 11.0, st(boom(3.0)), 0.5)
    put(fx, 11.0, st(thunder(3.4, 0.2)), 0.08)

    put(fx, 15.5, st(boom(1.6, 82, 34), -0.2), 0.42)            # CSE arrives
    put(fx, 15.5, st(clang(1.1, 0.85), -0.5), 0.05)
    put(fx, 18.0, st(boom(1.9, 66, 28), 0.2), 0.5)              # ME arrives
    put(fx, 18.0, st(clang(1.1, 0.6), 0.5), 0.05)
    put(fx, 18.5, st(riser(1.5, 6000)), 0.12)
    put(fx, 20.0, st(thunder(4.6, 1.0)), 0.3)                   # VS
    put(fx, 20.0, st(braam(3.2, 25)), 0.42)
    put(fx, 20.0, st(boom(3.0)), 0.55)
    put(fx, 21.5, st(thunder(3.0, 0.5), 0.3), 0.16)

    put(fx, 22.0, st(thunder(3.6, 0.8), -0.2), 0.2)             # the champion's lightning
    put(fx, 24.0, st(thunder(2.6, 0.55), 0.2), 0.15)
    put(fx, 25.5, st(thunder(1.8, 0.6), -0.1), 0.15)

    put(fx, 26.0, st(riser(2.0, 9000)), 0.2)                    # into the clash
    put(fx, 28.0, st(clang(2.6), 0.0), 0.3)
    put(fx, 28.0, st(boom(2.8, 92, 30)), 0.62)
    put(fx, 28.0, st(braam(2.4, 27)), 0.34)

    for when in (30.0, 31.0, 32.0, 33.0):
        put(fx, when + 0.03, st(clang(0.5, rng.uniform(0.8, 1.3)), rng.uniform(-0.5, 0.5)), 0.05)

    for when, note in ((34.5, 62), (35.0, 65), (35.5, 69), (36.0, 74)):                # the cards land
        put(fx, when, st(boom(0.7, 110, 46)), 0.38)
        put(fx, when, st(high(noise(0.08), 1400) * np.exp(-np.arange(at(0.08)) / RATE / 0.012)), 0.12)
        put(horns, when, st(brass(note - 12, 0.46, 2400)), 0.17)
    put(fx, 34.0, st(fire_crackle(4.0)), 0.13)
    put(voices, 36.0, st(choir((62, 69), 2.2)), 0.07)

    # The storm.
    length = 14.0
    env = np.minimum(np.arange(at(length)) / RATE / 0.9, 1) * np.minimum((length - np.arange(at(length)) / RATE) / 2.0, 1)
    put(air, 38.0, np.stack([band(noise(length), 1800, 9500) * env, band(noise(length), 1800, 9500) * env], axis=1), 0.05)
    put(fx, 38.33, st(thunder(1.6, 0.25), -0.5), 0.1)
    put(fx, 39.13, st(thunder(1.0, 0.4), 0.5), 0.1)
    put(fx, 38.0, st(riser(2.0, 8000)), 0.2)
    put(fx, 40.0, st(thunder(5.0, 1.2)), 0.34)                  # POWER MODE
    put(fx, 40.0, st(braam(3.6, 25)), 0.5)
    put(fx, 40.0, st(boom(3.2)), 0.62)
    for when in (42.0, 44.0, 46.0, 48.0):                       # every cut lands
        put(fx, when, st(boom(1.0, 88, 36)), 0.32)
        put(fx, when, st(thunder(1.2, 0.5), rng.uniform(-0.4, 0.4)), 0.11)
    put(fx, 48.5, st(riser(1.5, 8000)), 0.16)

    put(fx, 50.0, st(boom(0.7, 96, 40)), 0.5)                   # two hits on the castle
    put(fx, 50.0, st(clang(0.7, 0.55)), 0.09)
    put(fx, 50.5, st(boom(0.7, 96, 40)), 0.55)
    put(fx, 50.5, st(clang(0.7, 0.5)), 0.1)
    put(fx, 51.0, st(explosion(6.0)), 0.78)                     # CASTLE DOWN.
    put(fx, 51.0, st(braam(3.4, 25)), 0.4)
    put(fx, 51.3, st(fire_crackle(8.0, 34)), 0.15)

    put(fx, 54.0, st(riser(1.0, 3000)), 0.09)
    put(fx, 55.0, st(braam(5.0, 26)), 0.55)                     # KUET ROYALE
    put(fx, 55.0, st(boom(4.2, 72, 27)), 0.7)
    put(fx, 55.0, st(clang(3.4, 0.6)), 0.07)
    for when, level in ((55.0, 0.7), (57.0, 0.5), (59.0, 0.26)):     # the armies raise their weapons
        put(drums, when, st(taiko(33, 1.2)), level)
    for note in (62, 69, 74):
        put(horns, 55.0, st(brass(note - 12, 4.6, 2200)), 0.1)

    # ------------------------------------------------------------ the mix

    # Everything ducks a little under the big hits, so that they feel bigger.
    hits = np.abs(fx).max(axis=1)
    level = low(hits, 12, 1)
    duck = 1 / (1 + 1.5 * np.clip(level, 0, 1))
    music = strings + horns + voices
    # A big room.
    length = at(3.2)
    t = np.arange(length) / RATE
    impulse = np.stack([low(rng.standard_normal(length), 5200) * np.exp(-t / 0.82), low(rng.standard_normal(length), 5200) * np.exp(-t / 0.82)], axis=1)
    impulse[:at(0.02)] = 0
    impulse /= np.sqrt(np.sum(impulse ** 2, axis=0))
    send = music * 0.85 + drums * 0.26 + fx * 0.2
    wet = np.stack([fftconvolve(send[:, k], impulse[:, k])[:N] for k in (0, 1)], axis=1)
    mix = (music + low_end) * duck[:, None] + drums + fx + air + wet * 0.3
    mix = high(mix, 26)

    mix = mix / np.max(np.abs(mix)) * 1.5
    mix = np.tanh(mix)
    fade = np.ones(N)
    fade[at(58.6):] = np.linspace(1, 0, N - at(58.6)) ** 1.5
    fade[:at(0.08)] = np.linspace(0, 1, at(0.08))
    mix *= fade[:, None]
    mix *= 0.89 / np.max(np.abs(mix))
    with wave.open(path, "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes((mix * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    main(sys.argv[1])
