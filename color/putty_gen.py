# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 13:31:12 2022

@author: dof
"""

from collections import OrderedDict

from colorspacious import cspace_convert
import matplotlib.pylab as plt
import numpy as np

# TTY colors(mostly from PuTTY)
Colour = [[]] * 22
Colour[0] = "187,187,187"   # FG
Colour[1] = "255,255,255"   # FG Bold
Colour[2] = "0,0,0"         # BG
Colour[3] = "102,102,102"   # BG Bold'
Colour[4] = "0,0,0"         # Cursor text
Colour[5] = "0,255,0"       # Cursor
Colour[6] = "0,0,0"         # Black
Colour[7] = "102,102,102"   # Black Bold'
Colour[8] = "187,0,0"       # Red
Colour[9] = "255,85,85"     # Red Bold
Colour[10] = "0,187,0"      # Green
Colour[11] = "0,255,0"      # Green Bold'
Colour[12] = "187,187,0"    # Yellow
Colour[13] = "229,229,0"    # Yellow Bold'
Colour[14] = "0,0,187"      # Blue
Colour[15] = "85,85,255"    # Blue Bold
Colour[16] = "187,0,187"    # Magenta
Colour[17] = "255,85,255"   # Magenta bold
Colour[18] = "0,187,187"    # Cyan
Colour[19] = "0,229,229"    # Cyan Bold'
Colour[20] = "187,187,187"  # White
Colour[21] = "255,255,255"  # White Bold

color = []
for c in Colour:
    color.append([int(x) for x in c.split(',')])

# plt.imshow([color])

# Convert to JCh
color_jch = cspace_convert(color, "sRGB255", "JCh")

# Normalize lightness
j_mean = (np.mean(color_jch[8:20,0]) + np.max(color_jch[8:20,0])) / 2
color_jch[8:20,0] = (color_jch[8:20,0] + j_mean) / 2

j_w_mean = np.mean(color_jch[20:22,0])
color_jch[20:22,0] = (color_jch[20:22,0] + j_w_mean) / 2

# Normalize chroma
c_min = np.min(color_jch[8:20,1])
c_mean = np.mean(color_jch[8:20,1])
color_jch[8:20,1] = (color_jch[8:20,1] + c_min) / 2 - (c_mean - c_min) / 2

# Set hue
color_jch[8:10,2] = 0
color_jch[10:12,2] = 120
color_jch[12:14,2] = 60
color_jch[14:16,2] = 240
color_jch[16:18,2] = 300
color_jch[18:20,2] = 180
color_jch[8:20,2] += 15     # avg delta = 26

# Convert back to RGB
color_rgb = cspace_convert(color_jch, "JCh", "sRGB255")
color_rgb[20,:] = np.mean(color_rgb[20,:])
color_rgb[21,:] = np.mean(color_rgb[21,:])
rgbs = color_rgb.round().clip(0, 255).astype('uint8')

# Set FG, BG
rgbs[0,:] = rgbs[20,:]  # FG
rgbs[1,:] = rgbs[21,:]  # FG Bold
rgbs[2,:] = 24          # BG
rgbs[4,:] = 24          # Cursor text
rgbs[5,:] = rgbs[11,:]  # Cursor

plt.figure()
plt.imshow([rgbs])

# Write putty.reg
REG_HEADER = '''Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions\Default%20Settings]
'''
with open('putty.reg', 'wt') as f:
    f.write(REG_HEADER)
    for idx, rgb in enumerate(rgbs):
        print('"Colour{}"="'.format(idx), end='', file=f)
        print(','.join(np.char.mod('%d', rgb)), end='', file=f)
        print('"', file=f)

# Write mintty
mintty = OrderedDict()
mintty['ForegroundColour'] = rgbs[0]
mintty['BackgroundColour'] = rgbs[2]
mintty['CursorColour'] = rgbs[5]
mintty['Black'] = rgbs[6]
mintty['BoldBlack'] = rgbs[7]
mintty['Red'] = rgbs[8]
mintty['BoldRed'] = rgbs[9]
mintty['Green'] = rgbs[10]
mintty['BoldGreen'] = rgbs[11]
mintty['Yellow'] = rgbs[12]
mintty['BoldYellow'] = rgbs[13]
mintty['Blue'] = rgbs[14]
mintty['BoldBlue'] = rgbs[15]
mintty['Magenta'] = rgbs[16]
mintty['BoldMagenta'] = rgbs[17]
mintty['Cyan'] = rgbs[18]
mintty['BoldCyan'] = rgbs[19]
mintty['White'] = rgbs[20]
mintty['BoldWhite'] = rgbs[21]

with open('mintty-dof', 'wt') as f:
    for key, rgb in mintty.items():
        print('{} = '.format(key), end='', file=f)
        print(','.join(np.char.mod('%d', rgb)), file=f)

# Simulating colorblindness
# cvd_space = {"name": "sRGB1+CVD",
#              "cvd_type": "deuteranomaly",
#              "severity": 100}
# deuteranomaly_sRGB = cspace_convert(color_rgb_clip/255, cvd_space, "sRGB255")

# plt.figure()
# plt.imshow([np.clip(deuteranomaly_sRGB, 0, 255).round().astype('uint8')])
