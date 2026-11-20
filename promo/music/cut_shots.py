#!/usr/bin/env python3
"""Cut each shot of the film out of the 4K recordings: only the frames it plays and the part of the screen it shows.

    python3 music/cut_shots.py <folder of recordings> public/shots
"""
import json
import os
import subprocess
import sys

source, target = sys.argv[1], sys.argv[2]
os.makedirs(target, exist_ok=True)
with open("src/shots.json") as handle:
    shots = json.load(handle)
for name, shot in shots.items():
    x, y, w, h = shot["crop"]
    scale = 3  # the recordings have three pixels to one pixel of the 1280 x 720 screen
    width, height = 2 * round(w * shot["px"] / 2), 2 * round(h * shot["px"] / 2)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "%.4f" % (shot["from"] / 60), "-i", os.path.join(source, shot["clip"] + ".mp4"),
                    "-frames:v", str(shot["frames"]), "-vf", "crop=%d:%d:%d:%d,scale=%d:%d:flags=lanczos" % (w * scale, h * scale, x * scale, y * scale, width, height),
                    "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", "-g", "15", "-bf", "0",
                    os.path.join(target, name + ".mp4")], check=True)
    print(name, width, height, os.path.getsize(os.path.join(target, name + ".mp4")) // 1024, "KB")
