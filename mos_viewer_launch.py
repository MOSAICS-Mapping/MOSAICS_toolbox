#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:25:09 2021

@author: Bryce

--- deSCRIPTION ---
"""

import gl, sys
import subprocess

# args = sys.argv[1:]
# img_brain = args[0]
# img_heatmap = args[1]
# img_responses = args[2]

# # this goes in the mos_gui call or a separate handler script
# subprocess.call(['./include/MRIcroGL.app/Contents/MacOS/MRIcroGL','-s','./mos_launch_viewer.py',
#                  img_brain,img_responses,img_heatmap])

gl.resetdefaults()
gl.backcolor(0,0,0)
gl.colorbarsize(0.02)
gl.cameradistance(0.6)

# load main image
# gl.loadimage('./include/MNI152_T1_1mm_brain.nii.gz')
gl.loadimage('mni152')
gl.shadername('Standard')
gl.shaderadjust('surfaceColor',1)
gl.shaderadjust('brighten',5)

## ----- Commented out until I can figure out how to load custom images
#        (from a subprocess call?) ----- ##

# # load main image
# gl.loadimage(img_brain)
# gl.shadername('Standard')
# gl.shaderadjust('surfaceColor',1)
# gl.shaderadjust('brighten',5)

# # load heatmap overlay
# #gl.overlayload(img_heatmap)
# gl.overlayload('LCT1_heatmap.nii.gz')
# gl.overlayloadsmooth(1)
# gl.minmax(1,1,50)
# gl.colorname (1,"4hot")
# gl.shaderadjust('overlayDepth', 0.35)

# # #load responses overlay
# #gl.overlayload(img_responses)
# gl.overlayload('LCT1_responses.nii.gz')
# gl.overlayloadsmooth(1)
# gl.minmax(2,0,50)
# gl.colorname (2,"2green")
# gl.shaderadjust('overlayDepth', 0.35)
# ---------- #

# Testing - run this from 00_Multiple_files directory








# #open background image
# gl.loadimage('spm152')
# #open overlay: show positive regions
# gl.overlayload('spmMotor')
# gl.minmax(1, 4, 4)
# gl.opacity(1,50)
# #open overlay: show negative regions
# gl.overlayload('spmMotor')
# gl.minmax(2, -4, -4)
# gl.colorname (2,"3blue")
# #gl.orthoviewmm(37,-14,47)

# def main():

# if __name__ == "__main__":
#     main()