# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 17:33:26 2022

Oklab, Oklch color space conversion

Oklab: https://bottosson.github.io/posts/oklab/

@author: dof
"""

import numpy as np


FLT_MAX = np.finfo(np.float32).max


def linear_srgb_to_oklab(c):
    if type(c) is not np.ndarray:
        c = np.asarray(c, dtype=np.float32)

    r = c[..., 0]
    g = c[..., 1]
    b = c[..., 2]

    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = np.cbrt(l)
    m_ = np.cbrt(m)
    s_ = np.cbrt(s)

    return np.stack([
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    ], axis=-1)


def oklab_to_linear_srgb(c):
    if type(c) is not np.ndarray:
        c = np.asarray(c, dtype=np.float32)

    L = c[..., 0]
    a = c[..., 1]
    b = c[..., 2]

    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    return np.stack([
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    ], axis=-1)


def rgb_to_oklch(rgb):
    lab = linear_srgb_to_oklab(rgb)
    L = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]

    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a)) % 360

    return np.stack([L, C, h], axis=-1)


def oklch_to_rgb(c):
    if type(c) is not np.ndarray:
        c = np.asarray(c, dtype=np.float32)

    L = c[..., 0]
    C = c[..., 1]
    h = c[..., 2]

    h_ = np.radians(h)
    Lab = np.stack([L, C * np.cos(h_), C * np.sin(h_)], axis=-1)

    return oklab_to_linear_srgb(Lab)
