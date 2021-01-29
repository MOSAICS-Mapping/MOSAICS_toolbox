# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 1:52:00 2020

@author: Bryce

----- Usage ------

Imported by MOSAICS gui.py, main() called to run MOSAICS analysis!

----- Outputs -----

1. Folder with name determined by SID string
     - <SID>_DotMap.nii
     - <SID>_Grid.xlsx
     - <SID>_GridLoc.nii
     - <SID>_Heatmap.nii
     - <SID>_Hotspots.nii
     - <SID>_Results.xlsx
     - <SID>_Samples.nii
     - <SID>.nii

----- Versions -----

- v1: initial version of the script, run manually as a standalone
- v2: adapted to work within the MOSAICS gui.py script, code is now wrapped in the main() function.

----- Development Notes -----

 - python working dir = where matlab script is located
 - matlab script must exist in MATLAB WORKING DIRECTORY for matlab.engine to run right
 - python working directory does not matter

"""

import matlab.engine as mat
import os, sys

def main(nii_location, coord_location, subject_ID):

    # --- ACTUAL RUN ---
    # Start matlab
    print('starting matlab')
    eng = mat.start_matlab()
    
    # Lines 56 and 58 below can be uncommented if we need to account for the MOSAICS matlab scripts being located in a different location to the 
    # matlab_script_dir = os.getcwd()
    # # matlab workdir = location of the mosaics_python.m script
    # eng.cd(matlab_script_dir)
    
    print('running test command')
    eng.mosaics_python(subject_ID, nii_location, coord_location, nargout=0)

