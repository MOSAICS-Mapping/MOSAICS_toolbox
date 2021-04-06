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
import os
import logging
from nipype.interfaces import fsl
parent_logger = logging.getLogger('main')

def main(tag, file_t1, data_folder, save_dir):
    
    bet_output =  os.path.join(save_dir,tag+'_brain_mask.nii.gz')
    bet_doublecheck = os.path.join(data_folder,tag+'_brain_mask.nii.gz')
    if not os.path.isfile(bet_output):
        if not os.path.isfile(bet_doublecheck):
            bet = fsl.BET()
            bet.inputs.in_file = file_t1
            bet.inputs.frac = 0.5 #default for bet, set here for consistency
            bet.inputs.mask = True
            bet.inputs.out_file = bet_output
            t1_stripped = bet.run()
            brainmask = os.path.join(save_dir,tag+'_brain_mask.nii.gz')
        else:
            parent_logger.info('... '+tag+'_brain_mask.nii.gz found in the data folder, we''ll use that.')
            brainmask = bet_doublecheck            
    else:
       brainmask = bet_output
            
    return brainmask

if __name__ == '__main__':
    main()