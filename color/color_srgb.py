# -*- coding: utf-8 -*-
"""
Created on 2023-07-22

sRGB, linear sRGB conversion EOTF

https://en.wikipedia.org/wiki/SRGB

@author: dof
"""

import numpy as np


def lin_srgb_to_srgb(lin):
    abs_lin = np.abs(lin)
    abs_gam = np.where(
        abs_lin <= 0.0031308,
        12.92 * abs_lin,
        1.055 * np.power(abs_lin, 1/2.4) - 0.055
    )
    return np.sign(lin) * abs_gam


def srgb_to_lin_srgb(gam):
    abs_gam = np.abs(gam)
    abs_lin = np.where(
        abs_gam <= 0.040449936,
        abs_gam / 12.92,
        np.power((abs_gam + 0.055) / 1.055, 2.4)
    )
    return np.sign(gam) * abs_lin
