#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 11:12:45 2021

@author: Bryce

deSCRIPTion:
    - strips skull from raw T1 image using fsl BET
    - saves brain mask and skull-stripped image for user quality checking
"""

# Imports:
import logging
from nipype.interfaces import fsl
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(tag, file_t1, save_dir):
    
    logging.info('...performing BET skull stripping')
    
    # # raw t1 file (picked in mos_gui.py, guiSelect class)
    # file_t1 = str(data_dict['data'])
    # # save directory
    # save_dir = str(data_dict['save_dir'])
    # # save prefix
    # save_prefix = str(data_dict['save_prefix'])
    
    bet = fsl.BET()
    bet.inputs.in_file = file_t1
    bet.inputs.frac = 0.5 #default for bet, set here for consistency
    bet.inputs.mask = True
    bet.inputs.out_file = save_dir+'/'+tag+'_brain.nii.gz'
    t1_stripped = bet.run()

if __name__ == '__main__':
    main()