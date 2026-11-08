#!/usr/bin/env python3
"""Cut the warriors out of two recordings of the same frames, one on black and one on white.

A pixel that looks the same on both grounds is solid; the more it changes, the more see-through it is.

    python3 music/matte.py <figs folder> public/figs
"""
import multiprocessing as mp
import os
import sys

import numpy as np
from PIL import Image

DEPARTMENTS = ("cse", "eee", "me", "ce")


def one(job):
    source, target, number = job
    black = np.asarray(Image.open(os.path.join(source, "black", "f%08d.png" % number)).convert("RGB"), dtype=np.float32)
    white = np.asarray(Image.open(os.path.join(source, "white", "f%08d.png" % number)).convert("RGB"), dtype=np.float32)
    alpha = np.clip(1 - (white - black).max(axis=2) / 255.0, 0, 1)
    colour = np.clip(black / np.maximum(alpha[..., None], 1e-3), 0, 255)
    rgba = np.dstack([colour, alpha * 255]).round().astype(np.uint8)
    for row, name in enumerate(DEPARTMENTS):
        Image.fromarray(rgba[row * 540:(row + 1) * 540]).save(os.path.join(target, name, "%03d.png" % number), compress_level=3)
    return number


if __name__ == "__main__":
    source, target = sys.argv[1], sys.argv[2]
    for name in DEPARTMENTS:
        os.makedirs(os.path.join(target, name), exist_ok=True)
    count = len([name for name in os.listdir(os.path.join(source, "black")) if name.endswith(".png")])
    with mp.Pool(8) as pool:
        pool.map(one, [(source, target, number) for number in range(count)])
    print(count, "frames")
