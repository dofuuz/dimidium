# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 13:31:12 2022

@author: dof
"""

from colorspacious import cspace_convert
import matplotlib.pylab as plt
import numpy as np

# Default PuTTY color
Colour = [[]] * 22
Colour[0] = "187,187,187"   # FG
Colour[1] = "255,255,255"   # FG Bold
Colour[2] = "0,0,0"         # BG
Colour[3] = "85,85,85"      # BG Bold
Colour[4] = "0,0,0"         # Cursor text
Colour[5] = "0,255,0"       # Cursor
Colour[6] = "0,0,0"         # Black
Colour[7] = "85,85,85"      # Black Bold
Colour[8] = "187,0,0"       # Red
Colour[9] = "255,85,85"     # Red Bold
Colour[10] = "0,187,0"      # Green
Colour[11] = "85,255,85"    # Green Bold
Colour[12] = "187,187,0"    # Yellow
Colour[13] = "255,255,85"   # Yellow Bold
Colour[14] = "0,0,187"      # Blue
Colour[15] = "85,85,255"    # Blue Bold
Colour[16] = "187,0,187"    # Magenta
Colour[17] = "255,85,255"   # Magenta bold
Colour[18] = "0,187,187"    # Cyan
Colour[19] = "85,255,255"   # Cyan Bold
Colour[20] = "187,187,187"  # White
Colour[21] = "255,255,255"  # White Bold

Colour = [s.split(',') for s in Colour]

color = []
for c in Colour:
    color.append([int(x) for x in c])

plt.imshow([color])

# Convert to JCh
color_jch = cspace_convert([color], "sRGB255", "JCh")

# Normalize lightness
j_mean = (np.mean(color_jch[:,8:22,0]) + np.max(color_jch[:,8:22,0])) / 2
color_jch[:,8:22,0] = (color_jch[:,8:22,0] + j_mean) / 2

# Normalize chroma
c_min = np.min(color_jch[:,8:20,1])
color_jch[:,8:20,1] = c_min

# Little alt hue
color_jch[:,8:20,2] = color_jch[:,8:20,2] - 10

color_jch[:,0,0] = color_jch[:,20,0]    # FG
color_jch[:,1,0] = color_jch[:,21,0]    # FG Bold
color_jch[:,5,:] = color_jch[:,11,:]    # Cursor

# Convert back to RGB
color_rgb = cspace_convert(color_jch, "JCh", "sRGB255")
color_rgb_clip = np.clip(color_rgb, 0, 255).round().astype('uint8')

color_rgb_clip[:,2,:] = 24  # BG
color_rgb_clip[:,4,:] = 24  # Cursor text
color_rgb_clip[:,6,:] = 24  # Black

plt.figure()
plt.imshow(color_rgb_clip)

for idx, rgb in enumerate(color_rgb_clip[0]):
    print('"Colour{}"="'.format(idx), end='')
    print(','.join(np.char.mod('%d', rgb)), end='')
    print('"')
