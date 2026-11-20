#!/usr/bin/env python3
"""The promo's soundtrack, made entirely from code: 60.0 seconds at 100 beats a minute (25 bars of 2.4 s).

    python3 music/make_music.py public/music.wav

Bars   0-4   pad alone, opening words and title
Bars   4-9   arpeggio joins, picking and dropping
Bars   9-16  kick and bass, the warriors
Bars  16-19  drums drop out, the AIs think, a riser
Bars  19-23  Power mode, everything at once, chords change every bar
Bars  23-25  one last chord and its tail
"""
import sys

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

RATE = 48000
BEAT = 0.6
BAR = BEAT * 4
LENGTH = 60.0
SAMPLES = int(RATE * LENGTH)
rng = np.random.default_rng(100)


# A person's taps on screen, in seconds of the finished film.
TAPS = [(9.98, "tap"), (10.74, "tap"), (11.51, "tap"), (12.28, "tap"),
        (13.70, "tap"), (14.95, "tap"), (15.20, "land"),
        (50.60, "tap"), (51.42, "tap")]


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def at(seconds):
    return int(round(seconds * RATE))


def lowpass(signal, cutoff, order=2):
    return sosfilt(butter(order, min(cutoff, RATE * 0.45), "low", fs=RATE, output="sos"), signal, axis=0)


def highpass(signal, cutoff, order=2):
    return sosfilt(butter(order, cutoff, "high", fs=RATE, output="sos"), signal, axis=0)


def bandpass(signal, low, high):
    return sosfilt(butter(2, [low, high], "band", fs=RATE, output="sos"), signal, axis=0)


def add(track, start, sound, gain=1.0):
    begin = at(start)
    if begin >= SAMPLES:
        return
    end = min(SAMPLES, begin + len(sound))
    track[begin:end] += sound[:end - begin] * gain


def stereo(mono, pan=0.0):
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([mono * left, mono * right], axis=1)


CHORDS = {
    "Bm": (35, [62, 66, 69, 73]),
    "G": (31, [62, 66, 69, 71]),
    "D": (38, [62, 66, 69, 76]),
    "A": (33, [64, 69, 73, 76]),
}
# One entry per bar.
SONG = ["Bm", "Bm", "G", "G", "D", "D", "A", "A", "Bm", "Bm", "G", "G", "D", "D", "A", "A",
        "Bm", "Bm", "G", "Bm", "G", "D", "A", "D", "D"]


def pad_voice(note, seconds, cutoff):
    count = at(seconds)
    time = np.arange(count) / RATE
    voice = np.zeros(count)
    for detune in (-0.07, -0.02, 0.03, 0.08):
        phase = rng.random()
        voice += 2 * ((time * hz(note + detune) + phase) % 1.0) - 1
    voice = lowpass(voice / 4, cutoff, 4)
    attack = np.minimum(time / 0.5, 1.0) ** 1.5
    release = np.minimum((seconds - time) / 0.9, 1.0) ** 1.5
    return voice * attack * release


def pad(chord, start, seconds, cutoff, gain):
    _, notes = CHORDS[chord]
    bus = np.zeros((SAMPLES, 2))
    for place, note in enumerate(notes):
        add(bus, start, stereo(pad_voice(note, seconds + 0.9, cutoff), (-0.5, 0.25, -0.2, 0.5)[place]), gain)
    return bus


def bell(note, decay=0.55, bright=2.0):
    seconds = decay * 4
    time = np.arange(at(seconds)) / RATE
    index = bright * np.exp(-time / (decay * 0.3))
    tone = np.sin(2 * np.pi * hz(note) * time + index * np.sin(2 * np.pi * hz(note) * 2.0 * time))
    tone = tone * np.exp(-time / decay) * np.minimum(time / 0.004, 1.0)
    return tone


def bass(note, seconds, drive=0.15):
    time = np.arange(at(seconds)) / RATE
    tone = np.sin(2 * np.pi * hz(note) * time) + drive * np.sin(2 * np.pi * hz(note) * 2 * time) + drive * 0.5 * np.sin(2 * np.pi * hz(note) * 3 * time)
    return tone * np.minimum(time / 0.008, 1.0) * np.minimum((seconds - time) / 0.03, 1.0)


def kick():
    time = np.arange(at(0.42)) / RATE
    sweep = 44 + 90 * np.exp(-time / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(sweep) / RATE) * np.exp(-time / 0.14)
    click = rng.standard_normal(len(time)) * np.exp(-time / 0.0025) * 0.14
    return np.tanh((body + lowpass(click, 5000)) * 1.3)


def hat(decay=0.02):
    time = np.arange(at(0.12)) / RATE
    return highpass(rng.standard_normal(len(time)), 8000) * np.exp(-time / decay)


def clap():
    time = np.arange(at(0.35)) / RATE
    shape = np.zeros(len(time))
    for offset in (0.0, 0.011, 0.023):
        shape += np.exp(-np.maximum(time - offset, 0) / 0.012) * (time >= offset)
    shape += 0.5 * np.exp(-time / 0.11)
    return bandpass(rng.standard_normal(len(time)), 900, 4200) * shape


def impact(seconds=3.5, gain=1.0):
    time = np.arange(at(seconds)) / RATE
    sub = np.sin(2 * np.pi * np.cumsum(30 + 34 * np.exp(-time / 0.2)) / RATE) * np.exp(-time / 0.9)
    air = lowpass(rng.standard_normal(len(time)), 1800) * np.exp(-time / 0.5) * 0.28
    return (sub + air) * gain


def tap():
    """A soft touch on glass."""
    time = np.arange(at(0.09)) / RATE
    return (np.sin(2 * np.pi * 1750 * time) * 0.6 + np.sin(2 * np.pi * 3100 * time) * 0.3) * np.exp(-time / 0.012)


def land():
    """A warrior arriving on the arena."""
    time = np.arange(at(0.26)) / RATE
    return np.sin(2 * np.pi * np.cumsum(70 + 90 * np.exp(-time / 0.03)) / RATE) * np.exp(-time / 0.06)


def riser(seconds):
    count = at(seconds)
    time = np.arange(count) / RATE
    noise = rng.standard_normal((count, 2))
    low = lowpass(noise, 500)
    high = highpass(lowpass(noise, 9000), 1400)
    amount = (time / seconds)[:, None] ** 2.2
    return (low * (1 - amount) + high * amount) * amount * 0.9


def main(path):
    pads = np.zeros((SAMPLES, 2))
    arp = np.zeros((SAMPLES, 2))
    bassline = np.zeros(SAMPLES)
    drums = np.zeros((SAMPLES, 2))
    fx = np.zeros((SAMPLES, 2))

    # Pads: one stretch per run of the same chord.
    bar = 0
    while bar < 23:
        run = bar
        while run < 23 and SONG[run] == SONG[bar]:
            run += 1
        cutoff = 900 if bar < 4 else 1500 if bar < 9 else 2200 if bar < 16 else 1100 if bar < 19 else 3400
        gain = 0.34 if bar < 4 else 0.3 if bar < 16 else 0.26 if bar < 19 else 0.22
        pads += pad(SONG[bar], bar * BAR, (run - bar) * BAR, cutoff, gain)
        bar = run
    pads += pad("D", 23 * BAR, 2 * BAR - 0.9, 2600, 0.42)

    # Arpeggio: sixteenth notes through the chord.
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    for sixteenth in range(23 * 16):
        bar = sixteenth // 16
        start = sixteenth * BEAT / 4
        if bar < 2:
            continue
        if bar < 4 and sixteenth % 8 != 0:
            continue
        if 4 <= bar < 9 and sixteenth % 2 != 0:
            continue
        _, notes = CHORDS[SONG[bar]]
        note = notes[pattern[sixteenth % len(pattern)]]
        if bar >= 19:
            note += 12 if sixteenth % 16 >= 8 else 0
        level = 0.12 if bar < 4 else 0.1 if bar < 9 else 0.09 if bar < 16 else 0.075 if bar < 19 else 0.1
        bright = 1.2 if bar < 16 else 1.6 if bar < 19 else 2.6
        add(arp, start, stereo(bell(note, 0.42 if bar < 19 else 0.3, bright), -0.45 if sixteenth % 2 else 0.45), level)
    # A long bell on the first bars and on the last chord.
    for start, note, level in ((0.0, 66, 0.16), (2.4, 69, 0.14), (4.8, 74, 0.2), (23 * BAR, 74, 0.26), (23 * BAR, 81, 0.15), (23 * BAR + 0.6, 78, 0.12), (23 * BAR + 1.2, 76, 0.1)):
        add(arp, start, stereo(bell(note, 1.5, 1.4)), level)

    # Bass.
    for bar in range(9, 23):
        root = CHORDS[SONG[bar]][0]
        if 16 <= bar < 19:
            add(bassline, bar * BAR, bass(root + 12, BAR * 0.9), 0.14)
        elif bar < 19:
            for beat in (0, 1.5, 2, 3.5):
                add(bassline, (bar + beat / 4) * BAR, bass(root + 12, BEAT * 0.45), 0.3)
        else:
            for eighth in range(8):
                add(bassline, bar * BAR + eighth * BEAT / 2, bass(root + 12, BEAT * 0.42, 0.3), 0.32)
    add(bassline, 23 * BAR, bass(38, BAR * 1.6), 0.3)

    # Drums.
    kicks = []
    for bar in range(7, 23):
        if 16 <= bar < 19:
            continue
        for beat in range(4):
            if bar < 9 and beat % 2:
                continue
            start = (bar + beat / 4) * BAR
            kicks.append(start)
            add(drums, start, stereo(kick()), 0.42 if bar < 19 else 0.55)
    for bar in range(9, 23):
        if 16 <= bar < 19:
            continue
        for beat in range(4):
            add(drums, (bar + (beat + 0.5) / 4) * BAR, stereo(hat(0.018), 0.2), 0.05 if bar < 19 else 0.075)
        if bar >= 19:
            for beat in (1, 3):
                add(drums, (bar + beat / 4) * BAR, stereo(clap()), 0.16)
            for sixteenth in range(16):
                add(drums, bar * BAR + sixteenth * BEAT / 4, stereo(hat(0.008), -0.25), 0.03)

    # Big moments.
    add(fx, 2 * BAR, stereo(impact(3.5)), 0.5)
    add(fx, 19 * BAR, stereo(impact(2.5)), 0.5)
    add(fx, 23 * BAR, stereo(impact(4.5)), 0.6)
    add(fx, 16 * BAR + BAR / 2 + BAR * 1.5, riser(BAR), 0.13)
    add(fx, 22 * BAR, riser(BAR), 0.08)

    # Duck the pads and bass under each kick.
    duck = np.ones(SAMPLES)
    shape = 1 - 0.55 * np.exp(-np.arange(at(0.32)) / RATE / 0.09)
    for start in kicks:
        begin = at(start)
        end = min(SAMPLES, begin + len(shape))
        duck[begin:end] = np.minimum(duck[begin:end], shape[:end - begin])

    # A plate-like reverb from a burst of decaying noise.
    length = at(2.8)
    time = np.arange(length) / RATE
    impulse = lowpass(rng.standard_normal((length, 2)), 5200) * np.exp(-time / 0.72)[:, None]
    impulse /= np.sqrt(np.sum(impulse ** 2, axis=0))
    wet_in = pads * 0.6 + arp
    wet = np.stack([fftconvolve(wet_in[:, side], impulse[:, side])[:SAMPLES] for side in (0, 1)], axis=1)

    # A dotted-eighth echo on the arpeggio.
    echo = np.zeros((SAMPLES, 2))
    gap = at(BEAT * 0.75)
    for repeat, side in ((1, 1), (2, 0), (3, 1)):
        echo[gap * repeat:, side] += arp[:-gap * repeat, side] * 0.32 ** repeat

    # The arc of the whole film: quiet words, a slow build, a held breath, then Power mode.
    arc = np.interp(np.arange(SAMPLES) / RATE, [bar * BAR for bar in (0, 2, 4, 9, 16, 18.5, 19, 23, 25)],
                    [0.5, 0.62, 0.72, 0.85, 0.72, 0.8, 1.0, 1.0, 1.0])

    music = ((pads + arp + echo) * duck[:, None] + wet * 0.34 * duck[:, None]) * arc[:, None]
    mix = music + stereo(bassline * duck) + drums + fx
    for start, kind in TAPS:
        add(mix, start, stereo(tap() if kind == "tap" else land()), 0.2 if kind == "tap" else 0.34)
    mix = highpass(mix, 28)

    # Master: soft clip, fade the tail so that it ends exactly at 60.0 s.
    mix = mix / np.max(np.abs(mix)) * 1.15
    mix = np.tanh(mix) * 0.86
    fade = np.ones(SAMPLES)
    fade[at(58.2):] = np.linspace(1, 0, SAMPLES - at(58.2)) ** 1.6
    fade[:at(0.05)] = np.linspace(0, 1, at(0.05))
    mix *= fade[:, None]
    data = (mix * 32767).astype(np.int16)

    import wave
    with wave.open(path, "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(data.tobytes())


if __name__ == "__main__":
    main(sys.argv[1])
