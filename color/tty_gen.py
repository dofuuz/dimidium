# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 13:31:12 2022

@author: dof
"""

from collections import OrderedDict
import csv

from colorio import cs
import matplotlib.pylab as plt
import numpy as np


REF_COLOR = 9   # xterm color scheme


def cspace_convert(colors, start, dest):
    colors = np.asarray(colors).T

    if start == 'JCh':
        L, C, h = colors
        h_ = np.radians(h)
        colors = np.array([L, C * np.cos(h_), C * np.sin(h_)])
        start = 'Oklab'

    cc = cs.ColorCoordinates(colors, start)
    if dest == 'JCh':
        cc.convert('Oklab')
    else:
        cc.convert(dest, mode='clip')
    ret = cc.data

    if dest == 'JCh':
        L, a, b = ret
        C = np.hypot(a, b)
        h = np.degrees(np.arctan2(b, a)) % 360
        ret = np.array([L, C, h])

    return ret.T


with open('tty_color.tsv', newline='') as f:
    f.readline()
    f.readline()
    reader = csv.reader(f, delimiter='\t')
    colors = list(reader)


# TTY colors
Colour = colors[REF_COLOR]

color = [(24, 24, 24)]  # Background
for c in Colour[1:]:
    color.append([int(x) for x in c.split(', ')])

# plt.imshow([color])

# Convert to JCh
color_jch = cspace_convert(color, "sRGB255", "JCh")

# Normalize lightness
j_mean = np.mean(color_jch[2:17,0])
color_jch[2:9,0] = (color_jch[2:9,0] + j_mean) / 2
color_jch[10:16,0] = (color_jch[10:16,0] + j_mean) / 2

j_w_mean = np.mean([color_jch[8,0], color_jch[16,0]])
color_jch[8,0] = (color_jch[8,0] + j_w_mean) / 2
color_jch[16,0] = (color_jch[16,0] + j_w_mean) / 2

# Normalize chroma
c_min = np.min([color_jch[2:8,1], color_jch[10:16,1]])
color_jch[2:8,1] = (color_jch[2:8,1] + c_min + c_min) / 3

c_min = np.min(color_jch[10:16,1])
color_jch[10:16,1] = (color_jch[10:16,1] + c_min) / 2

# Set hue(avg delta to original is about 26)
color_jch[2:8,2] = (0, 120, 60, 240, 300, 180)
color_jch[2:8,2] += 15

color_jch[10:16,2] = (0, 120, 60, 240, 300, 180)
color_jch[10:16,2] += 25

# Convert back to RGB
color_rgb = cspace_convert(color_jch, "JCh", "sRGB255")
color_rgb[8,:] = np.mean(color_rgb[8,:])
color_rgb[16,:] = np.mean(color_rgb[16,:])
rgbs = color_rgb.round().clip(0, 255).astype('uint8')

plt.figure()
plt.imshow([rgbs])


# Write putty.reg
putty = np.zeros([22, 3])
for pdx, rdx in enumerate([8, 16, 0, 9, 0, 11, 1, 9, 2, 10, 3, 11, 4, 12, 5, 13, 6, 14, 7, 15, 8, 16]):
    putty[pdx] = rgbs[rdx]

REG_HEADER = '''Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions\Default%20Settings]
'''
with open('putty.reg', 'wt') as f:
    f.write(REG_HEADER)
    for idx, rgb in enumerate(putty):
        print('"Colour{}"="'.format(idx), end='', file=f)
        print(','.join(np.char.mod('%d', rgb)), end='', file=f)
        print('"', file=f)

# Write mintty
mintty = OrderedDict()
mintty['ForegroundColour'] = rgbs[8]
mintty['BackgroundColour'] = rgbs[0]
mintty['CursorColour'] = rgbs[11]
mintty['Black'] = rgbs[1]
mintty['BoldBlack'] = rgbs[9]
mintty['Red'] = rgbs[2]
mintty['BoldRed'] = rgbs[10]
mintty['Green'] = rgbs[3]
mintty['BoldGreen'] = rgbs[11]
mintty['Yellow'] = rgbs[4]
mintty['BoldYellow'] = rgbs[12]
mintty['Blue'] = rgbs[5]
mintty['BoldBlue'] = rgbs[13]
mintty['Magenta'] = rgbs[6]
mintty['BoldMagenta'] = rgbs[14]
mintty['Cyan'] = rgbs[7]
mintty['BoldCyan'] = rgbs[15]
mintty['White'] = rgbs[8]
mintty['BoldWhite'] = rgbs[16]

with open('mintty-dof', 'wt') as f:
    for key, rgb in mintty.items():
        print('{} = '.format(key), end='', file=f)
        print(','.join(np.char.mod('%d', rgb)), file=f)


# Generate preveiw
h = OrderedDict()
for key, rgb in mintty.items():
    h[key] = ''.join(np.char.mod('%02x', rgb))

d = OrderedDict()
d['"color:white; background-color:black"'] = '"color:#{}; background-color:#{}"'.format(h['ForegroundColour'], h['BackgroundColour'])
d['background-color:black;'] = 'background-color:#{};'.format(h['Black'])
d['background-color:red;'] = 'background-color:#{};'.format(h['Red'])
d['background-color:lime;'] = 'background-color:#{};'.format(h['Green'])
d['background-color:yellow;'] = 'background-color:#{};'.format(h['Yellow'])
d['background-color:#3333FF;'] = 'background-color:#{};'.format(h['Blue'])
d['background-color:fuchsia;'] = 'background-color:#{};'.format(h['Magenta'])
d['background-color:aqua;'] = 'background-color:#{};'.format(h['Cyan'])
d['background-color:white;'] = 'background-color:#{};'.format(h['White'])
d['font-weight:bold;color:dimgray;'] = 'font-weight:bold;color:#{};'.format(h['BoldBlack'])
d['font-weight:bold;color:red;'] = 'font-weight:bold;color:#{};'.format(h['BoldRed'])
d['font-weight:bold;color:lime;'] = 'font-weight:bold;color:#{};'.format(h['BoldGreen'])
d['font-weight:bold;color:yellow;'] = 'font-weight:bold;color:#{};'.format(h['BoldYellow'])
d['font-weight:bold;color:#3333FF;'] = 'font-weight:bold;color:#{};'.format(h['BoldBlue'])
d['font-weight:bold;color:fuchsia;'] = 'font-weight:bold;color:#{};'.format(h['BoldMagenta'])
d['font-weight:bold;color:aqua;'] = 'font-weight:bold;color:#{};'.format(h['BoldCyan'])
d['font-weight:bold;color:white;'] = 'font-weight:bold;color:#{};'.format(h['BoldWhite'])
d['color:dimgray;'] = 'color:#{};'.format(h['Black'])
d['color:red;'] = 'color:#{};'.format(h['Red'])
d['color:lime;'] = 'color:#{};'.format(h['Green'])
d['color:yellow;'] = 'color:#{};'.format(h['Yellow'])
d['color:#3333FF;'] = 'color:#{};'.format(h['Blue'])
d['color:fuchsia;'] = 'color:#{};'.format(h['Magenta'])
d['color:aqua;'] = 'color:#{};'.format(h['Cyan'])
d['color:white;'] = 'color:#{};'.format(h['White'])
d['"font-weight:bold;"'] = '"font-weight:bold;color:#{};"'.format(h['BoldWhite'])
d['"font-weight:bold;background-color:'] = '"font-weight:bold;color:#{};background-color:'.format(h['BoldWhite'])

with open(r'.tty-template.html') as f:
    html = f.read()

for k, v in d.items():
    html = html.replace(k, v)

with open(r'tty-preview.html', 'wt') as f:
    f.write(html)

# html = html.replace('font-weight:bold;', '')
# with open(r'tty-preview-nobold.html', 'wt') as f:
#     f.write(html)
