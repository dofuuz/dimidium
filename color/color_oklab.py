# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 17:33:26 2022

Oklab, Oklch color space conversion

Oklab: https://bottosson.github.io/posts/oklab/
sRGB gamut clipping: https://bottosson.github.io/posts/gamutclipping/

@author: dof
"""

import numpy as np


FLT_MAX = np.finfo(np.float32).max

RGB_TO_LMS = np.asarray([
    [0.4122214708, 0.5363325363, 0.0514459929],
    [0.2119034982, 0.6806995451, 0.1073969566],
    [0.0883024619, 0.2817188376, 0.6299787005],
], dtype=np.float32)

LMS_TO_OKLAB = np.asarray([
    [0.2104542553, +0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, +0.4505937099],
    [0.0259040371, +0.7827717662, -0.8086757660],
], dtype=np.float32)

OKLAB_TO_LMS = np.asarray([
    [1.0, +0.3963377774, +0.2158037573],
    [1.0, -0.1055613458, -0.0638541728],
    [1.0, -0.0894841775, -1.2914855480],
], dtype=np.float32)

LMS_TO_RGB = np.asarray([
    [+4.0767416621, -3.3077115913, +0.2309699292],
    [-1.2684380046, +2.6097574011, -0.3413193965],
    [-0.0041960863, -0.7034186147, +1.7076147010],
], dtype=np.float32)


def linear_srgb_to_oklab(c):
    c = np.asarray(c, dtype=np.float32)

    lms = np.inner(c, RGB_TO_LMS)
    lms_ = np.cbrt(lms)
    return np.inner(lms_, LMS_TO_OKLAB)


def oklab_to_linear_srgb(c):
    c = np.asarray(c, dtype=np.float32)

    lms_ = np.inner(c, OKLAB_TO_LMS)
    lms = lms_ * lms_ * lms_
    return np.inner(lms, LMS_TO_RGB)


def linear_srgb_to_oklch(rgb):
    lab = linear_srgb_to_oklab(rgb)
    L = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]

    C = np.hypot(a, b)
    h = np.degrees(np.arctan2(b, a)) % 360

    return np.stack([L, C, h], axis=-1)


def oklch_to_linear_srgb(c):
    c = np.asarray(c, dtype=np.float32)

    L = c[..., 0]
    C = c[..., 1]
    h = c[..., 2]

    h_ = np.radians(h)
    Lab = np.stack([L, C * np.cos(h_), C * np.sin(h_)], axis=-1)

    return oklab_to_linear_srgb(Lab)


# Finds the maximum saturation possible for a given hue that fits in sRGB
# Saturation here is defined as S = C/L
# a and b must be normalized so a^2 + b^2 == 1
def compute_max_saturation(a, b):
    if a == 0 and b == 0:
        return 0.

    # Max saturation will be when one of r, g or b goes below zero.

    # Select different coefficients depending on which component goes below zero first
    if (-1.88170328* a - 0.80936493* b > 1):
        # Red component
        k0 = +1.19086277
        k1 = +1.76576728
        k2 = +0.59662641
        k3 = +0.75515197
        k4 = +0.56771245
        wl = +4.0767416621
        wm = -3.3077115913
        ws = +0.2309699292
    elif (1.81444104* a - 1.19445276* b > 1):
        # Green component
        k0 = +0.73956515
        k1 = -0.45954404
        k2 = +0.08285427
        k3 = +0.12541070
        k4 = +0.14503204
        wl = -1.2684380046
        wm = +2.6097574011
        ws = -0.3413193965
    else:
        # Blue component
        k0 = +1.35733652
        k1 = -0.00915799
        k2 = -1.15130210
        k3 = -0.50559606
        k4 = +0.00692167
        wl = -0.0041960863
        wm = -0.7034186147
        ws = +1.7076147010

    # Approximate max saturation using a polynomial:
    S = k0 + k1 * a + k2 * b + k3 * a * a + k4 * a * b

    # Do one step Halley's method to get closer
    # this gives an error less than 10e6, except for some blue hues where the dS/dh is close to infinite
    # this should be sufficient for most applications, otherwise do two/three steps 

    k_l = +0.3963377774* a + 0.2158037573* b
    k_m = -0.1055613458* a - 0.0638541728* b
    k_s = -0.0894841775* a - 1.2914855480* b

    l_ = 1.+ S * k_l
    m_ = 1.+ S * k_m
    s_ = 1.+ S * k_s

    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    l_dS = 3.* k_l * l_ * l_
    m_dS = 3.* k_m * m_ * m_
    s_dS = 3.* k_s * s_ * s_

    l_dS2 = 6.* k_l * k_l * l_
    m_dS2 = 6.* k_m * k_m * m_
    s_dS2 = 6.* k_s * k_s * s_

    f = wl * l     + wm * m     + ws * s
    f1 = wl * l_dS  + wm * m_dS  + ws * s_dS
    f2 = wl * l_dS2 + wm * m_dS2 + ws * s_dS2

    S = S - f * f1 / (f1*f1 - 0.5* f * f2)

    return S


# finds L_cusp and C_cusp for a given hue
# a and b must be normalized so a^2 + b^2 == 1
def find_cusp(a, b):
    # First, find the maximum saturation (saturation S = C/L)
    S_cusp = np.vectorize(compute_max_saturation)(a, b)

    # Convert to linear sRGB to find the first point where at least one of r,g or b >= 1:
    lab = np.stack([np.ones_like(a), S_cusp * a, S_cusp * b], axis=-1)
    rgb_at_max = oklab_to_linear_srgb(lab)

    L_cusp = np.cbrt(1. / np.max(rgb_at_max, axis=-1))
    C_cusp = L_cusp * S_cusp

    return L_cusp , C_cusp


# Finds intersection of the line defined by
# L = L0 * (1 - t) + t * L1
# C = t * C1
# a and b must be normalized so a^2 + b^2 == 1
def find_gamut_intersection(a, b, L1, C1, L0):
    # Find the cusp of the gamut triangle
    cusp_L, cusp_C = find_cusp(a, b)

    # Find the intersection for upper and lower half seprately
    lower_mask = (L1 - L0) * cusp_C - (cusp_L - L0) * C1 <= 0.

    # Lower half
    lower_half = cusp_C * L0 / (C1 * cusp_L + cusp_C * (L0 - L1))

    # Upper half

    # First intersect with triangle
    t = cusp_C * (L0 - 1.) / (C1 * (cusp_L - 1.) + cusp_C * (L0 - L1))

    # Then one step Halley's method
    dL = L1 - L0
    dC = C1

    k_l = +0.3963377774* a + 0.2158037573* b
    k_m = -0.1055613458* a - 0.0638541728* b
    k_s = -0.0894841775* a - 1.2914855480* b

    l_dt = dL + dC * k_l
    m_dt = dL + dC * k_m
    s_dt = dL + dC * k_s

        
    # If higher accuracy is required, 2 or 3 iterations of the following block can be used:
    L = L0 * (1.- t) + t * L1
    C = t * C1

    l_ = L + C * k_l
    m_ = L + C * k_m
    s_ = L + C * k_s

    l = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    ldt = 3 * l_dt * l_ * l_
    mdt = 3 * m_dt * m_ * m_
    sdt = 3 * s_dt * s_ * s_

    ldt2 = 6 * l_dt * l_dt * l_
    mdt2 = 6 * m_dt * m_dt * m_
    sdt2 = 6 * s_dt * s_dt * s_

    r = 4.0767416621* l - 3.3077115913* m + 0.2309699292* s - 1
    r1 = 4.0767416621* ldt - 3.3077115913* mdt + 0.2309699292* sdt
    r2 = 4.0767416621* ldt2 - 3.3077115913* mdt2 + 0.2309699292* sdt2

    u_r = r1 / (r1 * r1 - 0.5* r * r2)
    t_r = -r * u_r

    g = -1.2684380046* l + 2.6097574011* m - 0.3413193965* s - 1
    g1 = -1.2684380046* ldt + 2.6097574011* mdt - 0.3413193965* sdt
    g2 = -1.2684380046* ldt2 + 2.6097574011* mdt2 - 0.3413193965* sdt2

    u_g = g1 / (g1 * g1 - 0.5* g * g2)
    t_g = -g * u_g

    b = -0.0041960863* l - 0.7034186147* m + 1.7076147010* s - 1
    b1 = -0.0041960863* ldt - 0.7034186147* mdt + 1.7076147010* sdt
    b2 = -0.0041960863* ldt2 - 0.7034186147* mdt2 + 1.7076147010* sdt2

    u_b = b1 / (b1 * b1 - 0.5* b * b2)
    t_b = -b * u_b

    t_r[u_r<0] = FLT_MAX
    t_g[u_g<0] = FLT_MAX
    t_b[u_b<0] = FLT_MAX

    t += np.amin([t_r, t_g, t_b], axis=0)

    np.putmask(t, lower_mask, lower_half)
    return t


def gamut_clip_preserve_chroma(rgb):
    rgb = np.asarray(rgb, dtype=np.float32)

    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    not_clip = np.all([r < 1, g < 1, b < 1, r >= 0, g >= 0, b >= 0], axis=0)
    not_clip = np.stack([not_clip, not_clip, not_clip], axis=-1)

    lab = linear_srgb_to_oklab(rgb)

    L = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]

    eps = 0.00001
    C = np.maximum(eps, np.sqrt(a * a + b * b))
    a_ = a / C
    b_ = b / C

    L0 = np.clip(L, 0, 1)

    t = find_gamut_intersection(a_, b_, L, C, L0)
    L_clipped = L0 * (1 - t) + t * L
    C_clipped = t * C

    clipped = np.stack([L_clipped, C_clipped * a_, C_clipped * b_], axis=-1)
    ret = oklab_to_linear_srgb(clipped)
    np.putmask(ret, not_clip, rgb)

    return ret


def gamut_clip_adaptive_L0_0_5(rgb, alpha=0.05):
    rgb = np.asarray(rgb, dtype=np.float32)

    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]
    not_clip = np.all([r < 1, g < 1, b < 1, r >= 0, g >= 0, b >= 0], axis=0)
    not_clip = np.stack([not_clip, not_clip, not_clip], axis=-1)

    lab = linear_srgb_to_oklab(rgb)

    L = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]

    eps = 0.00001
    C = np.maximum(eps, np.sqrt(a * a + b * b))
    a_ = a / C
    b_ = b / C

    Ld = L - 0.5
    e1 = 0.5 + np.abs(Ld) + alpha * C
    L0 = 0.5*(1. + np.sign(Ld)*(e1 - np.sqrt(e1*e1 - 2.*np.abs(Ld))))

    t = find_gamut_intersection(a_, b_, L, C, L0)
    L_clipped = L0 * (1. - t) + t * L
    C_clipped = t * C

    clipped = np.stack([L_clipped, C_clipped * a_, C_clipped * b_], axis=-1)
    ret = oklab_to_linear_srgb(clipped)
    np.putmask(ret, not_clip, rgb)

    return ret


if __name__ == "__main__":
    res = gamut_clip_adaptive_L0_0_5([[0, 0, 0], [-0.12, 0, 0.5], [1, 1, 1.2], [0.11, 0.32, 0.9]])
    print(res)
