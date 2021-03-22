#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 11:12:45 2021

@author: Bryce
"""

# Imports:
import os
import logging
from nipype.interfaces import fsl
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')    

def main(tag, stim_data, data_dir, save_dir, file_t1, file_heatmap_nomask, file_atlas):
#subject, data_dict, config_dict):
    
    # ~~~~~~SET UP VARIABLES~~~~~~

    # FLIRT section:
    # Register T1 image to MNI_152 template using FLIRT and FNIRT
    warped_t1 = os.path.join(save_dir,tag+'_warped.nii.gz')
    if not os.path.isfile(warped_t1):
        t1_flirt_mni = fsl.FLIRT()
        t1_flirt_mni.inputs.in_file = file_t1
        t1_flirt_mni.inputs.reference = file_atlas
        t1_flirt_mni.inputs.out_file = warped_t1
        t1_flirt_mni.inputs.out_matrix_file = os.path.join(save_dir,tag+'_warped_omat.mat')
        t1_flirt_mni.inputs.output_type = 'NIFTI_GZ'
        flirt_result = t1_flirt_mni.run()
    
    # I'm going to leave FNIRT out for now because... non-linear 
    # # 2. FNIRT t1 to MNI:
    # t1_fnirt_mni = fsl.FNIRT()
    # t1_fnirt_mni.inputs.affine_file = sample_data_dir+'T1_mni_FLIRT_omat.mat'
    # t1_fnirt_mni.inputs.in_file = file_t1
    # t1_fnirt_mni.inputs.ref_file = sample_data_dir+'MNI152_T1_1mm.nii.gz'
    # fnirt_result = t1_fnirt_mni.run()
    
    # # 3. FLIRT measure maps to MNI with our warps of choice (just flirt for now):
    heatmap_applyxfm = fsl.preprocess.ApplyXFM()
    # heatmap, using unmasked because then we're only masking based on standard space atlas mask,
    # rather than that and a BET mask
    heatmap_applyxfm.inputs.in_file = file_heatmap_nomask
    heatmap_applyxfm.inputs.in_matrix_file = os.path.join(save_dir,tag+'_warped_omat.mat')
    heatmap_applyxfm.inputs.out_file = os.path.join(save_dir,stim_data+'_warped_heatmap.nii.gz')
    heatmap_applyxfm.inputs.out_matrix_file = os.path.join(save_dir,stim_data+'_heatmap_flirt.mat')
    heatmap_applyxfm.inputs.reference = file_atlas
    heatmap_applyxfm.inputs.apply_xfm = True
    result = heatmap_applyxfm.run()

if __name__ == '__main__':
    main()