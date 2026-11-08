#!/usr/bin/env python3
"""Cut every warrior card out of a 4K still of the Meet the warriors screen.

    python3 music/cut_cards.py <stills folder> public/cards
"""
import os
import sys

from PIL import Image

X, Y, WIDTH, HEIGHT, STEP_X, STEP_Y = 100, 346, 870, 734, 918, 780

for department in ("cse", "eee", "me", "ce"):
    sheet = Image.open(os.path.join(sys.argv[1], "warriors_%s.png" % department)).convert("RGB")
    for number in range(8):
        left = X + (number % 4) * STEP_X
        top = Y + (number // 4) * STEP_Y
        sheet.crop((left, top, left + WIDTH, top + HEIGHT)).save(os.path.join(sys.argv[2], "%s_%d.png" % (department, number)), compress_level=4)
