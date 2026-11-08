#!/usr/bin/env python3
"""Give a flat warrior picture depth and film lighting.

Each shape between the dark outlines is puffed up like a pillow, which gives it a surface that light can fall on.
A key light, a low fill, a shine and a rim of light from behind then make it look modelled.
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

INK = np.array([13, 34, 56]) / 255
EMISSIVE = [np.array(c) / 255 for c in ((111, 233, 255), (255, 242, 122), (255, 74, 61), (125, 255, 107))]


def lit(path, key=(1.0, 0.86, 0.68), key_dir=(-0.55, -0.65, 0.55), fill=(0.20, 0.27, 0.42), rim=(1.0, 0.62, 0.30), rim_dir=(0.8, -0.5), rim_amount=1.5, gain=1.0, radius=46, outline_rim=1.1, size=None):
    """Returns (colour, alpha) as floats in linear light."""
    picture = Image.open(path).convert("RGBA")
    if size and size != picture.size[0]:
        picture = picture.resize((size, size), Image.LANCZOS)
    a = np.asarray(picture).astype(np.float32) / 255
    rgb, alpha = a[..., :3], a[..., 3]
    # Every distance below was chosen for a 1500-pixel picture.
    k = a.shape[0] / 1500
    radius = radius * k
    outline = (np.linalg.norm(rgb - INK, axis=2) < 0.2) & (alpha > 0.5)
    parts = (alpha > 0.6) & ~outline
    dist = ndi.distance_transform_edt(parts)
    t = np.minimum(dist, radius) / radius
    height = np.sqrt(t * (2 - t)) * radius
    height = ndi.gaussian_filter(height, 2.2 * k)
    gy, gx = np.gradient(height)
    nz = np.full_like(gx, 1.15)
    length = np.sqrt(gx * gx + gy * gy + nz * nz)
    nx, ny, nz = -gx / length, -gy / length, nz / length
    L = np.array(key_dir, dtype=np.float32)
    L /= np.linalg.norm(L)
    diffuse = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    H = L + np.array([0, 0, 1], dtype=np.float32)
    H /= np.linalg.norm(H)
    shine = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1) ** 26
    R = np.array(rim_dir, dtype=np.float32)
    R /= np.linalg.norm(R)
    rim_light = (1 - nz) ** 1.5 * np.clip(nx * R[0] + ny * R[1], 0, 1)
    linear = rgb ** 2.2
    out = linear * (np.array(fill) + np.array(key) * diffuse[..., None] * 1.25) * gain
    out += np.array(key) * shine[..., None] * 0.22 * parts[..., None]
    out += np.array(rim) * rim_light[..., None] * rim_amount * parts[..., None]
    # A thin line of rim light on the outline, only on the side the light comes from.
    solid = alpha > 0.5
    inside = ndi.gaussian_filter(solid.astype(np.float32), 9 * k)
    egy, egx = np.gradient(inside)
    towards = -(egx * R[0] + egy * R[1]) * k
    outer = np.clip((towards - 0.012) * 90, 0, 1) * np.clip(1 - inside * 1.25, 0, 1) * 2 * outline
    out += np.array(rim) * outer[..., None] * outline_rim
    # Glowing eyes and sparks keep their light in the dark.
    for glow in EMISSIVE:
        near = np.linalg.norm(rgb - glow, axis=2) < 0.16
        out[near] = linear[near] * 2.4
    return out, alpha


def bright_sprite(path, **kw):
    return lit(path, **kw)
