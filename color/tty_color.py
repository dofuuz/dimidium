#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 15:01:59 2023

"DOF" (Depth of Field) color scheme for terminals
https://github.com/dofuuz/dotfiles

This color scheme aims enhanced readability by reducing perceptual lightness differences between
colors. In the typical terminal settings, there were issues with certain text colors (especially
blue) being poorly visible. To solve this, the lightness has been equalized using the latest color
space "CAM16".

More information about the Color appearance model, including CAM16:
https://en.wikipedia.org/wiki/Color_appearance_model

xterm's simple color scheme was chosen as the base. For readability, the lightness has been adjusted
to avoid being too bright or too dark. Hue values were set to maximize color distinction, and
saturation was adjusted to fit within the color display range.

Unlike the "helmholtz" or "kohlrausch" color schemes, this color scheme does not aim for equal
brightness. It preserves some lightness and saturation variation to keep each color's essence. In
fact, if each color were adjusted to the same lightness and saturation using CAM16, colors would
become quite "uncomfortable".
"""


import csv

import colour  # colour-science
import matplotlib.pyplot as plt
import numpy as np


def plot_lightness(jchs):
    PLOT_HEIGHT = 8

    jchs = jchs.copy()

    j_space = np.linspace(0, 100, 1000)
    jc = np.zeros([PLOT_HEIGHT, 1000])
    jc[...,:] = j_space
    chc = np.zeros_like(jc)

    xyzs = colour.CAM16UCS_to_XYZ(np.stack([jc, chc, chc], axis=-1))
    rgbs = colour.XYZ_to_sRGB(xyzs).clip(0, 1)

    plt.figure(figsize=(6.4, 1))
    ax = plt.subplot()
    ax.imshow(rgbs, extent=[j_space.min(), j_space.max(), 0, PLOT_HEIGHT])
    ax.invert_yaxis()
    ax.get_yaxis().set_visible(False)

    for jch in jchs[2:9]:  # plot colors
        jch[1] *= 0.93  # desaturate plot
        jab = colour.models.JCh_to_Jab(jch)
        xyz = colour.CAM16UCS_to_XYZ(jab)
        rgb = colour.XYZ_to_sRGB(xyz).clip(0, 1)

        ax.plot(jch[0], 0.25*PLOT_HEIGHT, marker="s", markersize=8, markeredgecolor='black', markerfacecolor=rgb)

    for jch in jchs[10:17]:  # plot bright colors
        jch[1] *= 0.93  # desaturate plot
        jab = colour.models.JCh_to_Jab(jch)
        xyz = colour.CAM16UCS_to_XYZ(jab)
        rgb = colour.XYZ_to_sRGB(xyz).clip(0, 1)

        ax.plot(jch[0], 0.75*PLOT_HEIGHT, marker="s", markersize=8, markeredgecolor='black', markerfacecolor=rgb)

    plt.show()


def plot_hue(jchs):
    AB_RANGE = 45
    jchs = jchs.copy()

    ac = np.linspace(-AB_RANGE, AB_RANGE, 1000)
    bc = np.linspace(-AB_RANGE, AB_RANGE, 1000)
    ac, bc = np.meshgrid(ac, bc)

    jc = np.ones_like(ac) * 70

    xyzs = colour.CAM16UCS_to_XYZ(np.stack([jc, ac, bc], axis=-1))
    rgbs = colour.XYZ_to_sRGB(xyzs).clip(0, 1)

    clipped = np.hypot(ac, bc) > 35
    clipped = np.stack([clipped, clipped, clipped], axis=-1)

    rgbs[clipped] = 1

    plt.figure(figsize=(4.8, 4.8))
    ax = plt.subplot()
    ax.imshow(rgbs, extent=[ac.min(), ac.max(), bc.max(), bc.min()])
    ax.invert_yaxis()
    ax.axis('off')
    ax.axis('equal')

    for jch in jchs[np.r_[2:9, 10:17]]:
        jab = colour.models.JCh_to_Jab(jch)
        xyz = colour.CAM16UCS_to_XYZ(jab)
        rgb = colour.XYZ_to_sRGB(xyz).clip(0, 1)

        ax.plot(jab[1], jab[2], marker="s", markersize=8, markeredgecolor='black', markerfacecolor=rgb)
    plt.show()


def plot_colors(jchs):
    jab = colour.models.JCh_to_Jab(jchs)
    xyzs = colour.CAM16UCS_to_XYZ(jab)
    rgbs = colour.XYZ_to_sRGB(xyzs).clip(0, 1)
    
    plt.figure()
    plt.imshow([rgbs[0:9], rgbs[8:17]])
    plt.axis('off')
    plt.show()


def get_colors_from_tsv(ref_color):
    with open('tty_color.tsv', newline='') as f:
        f.readline()
        f.readline()
        reader = csv.reader(f, delimiter='\t')
        colors = list(reader)
    
    # TTY colors
    Colour = colors[ref_color]
    color = [(0, 0, 0)]  # Background
    for c in Colour[1:]:
        color.append([int(x) for x in c.split(', ')])
    color = np.asarray(color, dtype=np.float32)

    return color


def generate_colors(ref_color=9, plot=False):
    color = get_colors_from_tsv(ref_color)
    color[0,:] = 20  # background
    color[9,:] = 85  # bright black

    # Convert to CAM16-UCS-JCh
    xyz = colour.sRGB_to_XYZ(color/255)
    jab = colour.XYZ_to_CAM16UCS(xyz)
    color_jch = colour.models.Jab_to_JCh(jab)
    
    if plot:
        plot_lightness(color_jch)
        plot_colors(color_jch)
    
    # Normalize lightness
    j = color_jch[..., 0]
    j[5] = (j[2] + j[5]) / 2  # adjust blue
    # j[13] = (j[10] + j[13]) / 2  # adjust bright blue
    
    j_mean = np.mean(j[2:8])
    j[2:9] = (j[2:9] + j_mean) / 2  # colors
    
    j_mean = np.mean(j[10:16])
    j[10:17] = (j[10:17] + j_mean) / 2  # bright colors
    
    if plot:
        plot_lightness(color_jch)
        plot_colors(color_jch)
        
        plot_hue(color_jch)
    
    # Set hue(mean delta to original is about 3)
    h = color_jch[..., 2]
    h[2:8] = (30, 150, 90, 270, 330, 210)
    h[2:8] -= 10

    h[10:16] = (30, 150, 90, 270, 330, 210)
    h[10:16] += 3

    if plot:
        plot_hue(color_jch)
        plot_colors(color_jch)


    # Normalize chroma
    c = color_jch[..., 1]
    c_min = np.min(c[2:8])
    c[2:8] = (c[2:8] + c_min) / 2

    c_min = np.min(c[10:16])
    c[10:16] = (c[10:16] + c_min) / 2

    c[0] = 0  # background
    c[8] = 0  # white
    c[9] = 0  # bright black
    c[16] = 0  # bright white
    
    # clip chroma into sRGB gamut
    for desaturate in np.arange(1, 0.1, -0.001):
        # Convert back to RGB
        color_jch_adj = np.stack([j, c*desaturate, h], axis=-1)
        jab = colour.models.JCh_to_Jab(color_jch_adj)
        xyz = colour.CAM16UCS_to_XYZ(jab)
        color_rgb = colour.XYZ_to_sRGB(xyz)
    
        if np.all(0 <= color_rgb) and np.all(color_rgb <= 1):
            color_jch = color_jch_adj
            if plot:
                print(desaturate)
            break

    if plot:
        plot_hue(color_jch)
        plot_colors(color_jch)

    if plot:
        print((color_rgb*255).round().astype('int'))
    rgbs = (color_rgb*255).round().clip(0, 255).astype('uint8')

    if plot:
        plt.figure()
        plt.imshow([rgbs[0:9], rgbs[8:17]])
        plt.axis('off')
        plt.show()

    return rgbs


if __name__ == '__main__':
    np.set_printoptions(precision=3, suppress=True)
    plt.rcParams['figure.autolayout'] = True

    rgbs = generate_colors(plot=True)
    print(rgbs)
