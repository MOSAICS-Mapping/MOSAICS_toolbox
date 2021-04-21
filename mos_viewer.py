#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:25:09 2021

@author: Bryce

--- deSCRIPTION ---
"""

# Testing - run this from 00_Multiple_files directory

import gl
gl.resetdefaults()
gl.backcolor(0,0,0)
gl.colorbarsize(0.02)
gl.cameradistance(0.6)

# load main image
gl.loadimage('./outputs/LCT1/LCT1_brain.nii.gz')
gl.shadername('Standard')
gl.shaderadjust('surfaceColor',1)
gl.shaderadjust('brighten',5)

# load overlay 1
gl.overlayload('/Users/Bryce/Desktop/Postdoc_Scripts/GitHub/04_mosaics_data/00_Multiple_files/outputs/LCT1/LCT1_heatmap.nii.gz')
gl.overlayloadsmooth(1)
gl.minmax(1,1,50)
gl.colorname (1,"4hot")
gl.shaderadjust('overlayDepth', 0.35)

# #load overlay 2
gl.overlayload('./outputs/LCT1/LCT1_responses.nii.gz')
gl.overlayloadsmooth(1)
gl.minmax(2,0,50)
gl.colorname (2,"2green")
gl.shaderadjust('overlayDepth', 0.35)

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