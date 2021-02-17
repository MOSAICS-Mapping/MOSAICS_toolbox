#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 4 10:15:48 2021

@author: Bryce Geeraert

MOSAICS - Mapping of sensory activation hotspots during cortical stimulation 

??? Consider bringing in some of Helen's comments here once we know how this python script operates
??? There's a slight spatial mismatch between Matlab's MOSAICS output and this python script. Perhaps
this is due to differences in how SPM imports and exports nfiti data? Not sure. I'm leaving this
alone for now, it's a feature to polish.

"""

"""
extra functions list, outsource to their own scripts hey?
    skullstrip
"""

##### Script initialization section #####

# set FSLDIR in Spyder, this should be taken care of during installation I guess?
# FSLDIR=/usr/share/fsl
# . ${FSLDIR}/etc/fslconf/fsl.sh
# PATH=${FSLDIR}/bin:${PATH}
# export FSLDIR PATH
    
import os
import nibabel as nib
import pandas as pd
import numpy as np
from scipy import ndimage as ndi
from nipype.interfaces import fsl
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(data_dict, config_dict):

    # ~~~~~~SET UP VARIABLES~~~~~~
    # structural file
    file_t1 = str(data_dict['image'])
    # stimulation spreadsheet
    file_nibs_map = str(data_dict['stim'])
    # save directory
    save_dir = str(data_dict['save_dir'])
    # save prefix
    save_prefix = str(data_dict['save_prefix'])
    
    # dilate variable
    dilate = int(config_dict['dilate'])
    # smooth variable
    smooth = int(config_dict['smooth'])
    # MEP threshold
    MEP_thresh = int(config_dict['MEP_threshold'])
    # standard space reference
    if int(config_dict['normalize']) == 1:
        file_atlas = str(config_dict['atlas'])

    # # Create output directory
    # os.makedirs(os.getcwd()+'/outputs/',exist_ok=True)
    
    
    # ~~~~~~LOAD DATA~~~~~~
    # Read in a 1mm isotropic T1-weighted MRI .nii
    data_T1 = nib.load(file_t1)
    # Dead the Brainsight coordindates file
    # should be four columns. X, Y, Z, and the corresponding MEP amplitude for that location
    data_nibs_map = pd.read_excel(file_nibs_map,header=None)
    data_nibs_map[0] = round(data_nibs_map[0])
    data_nibs_map[1] = round(data_nibs_map[1])
    data_nibs_map[2] = round(data_nibs_map[2])
    #num_locs = number of stimulation sites
    #num_locs = data_nibs_map[0].shape[0] <--- [] Think I don't need this
    
    
    # ~~~~~~PROCESSING BEGINS~~~~~~
    # Create an array of zeroes equal to size of T1 image, to initialize our output images
    map_stims = np.zeros(data_T1.shape)
    map_samples = np.zeros(data_T1.shape)
    map_grid = np.zeros(data_T1.shape)
    
    # Put all MEP values in to the arrays of zeroes at their corresponding x,y,z coordinates
    # index variable has a name (eg. 134) and dtype (eg. float64)
    # row variable has all variables in the row, 0 = x, 1 = y, 2 = z, 3 = mep amplitude
    for index, row in data_nibs_map.iterrows():
        map_stims[int(row[0]),int(row[1]),int(row[2])] = row[3]
        map_samples[int(row[0]),int(row[1]),int(row[2])] = row[3]
        map_grid[int(row[0])-1,int(row[1])-1,int(row[2])-1] = 1
    
    # What are these maps (above)?
    #     - map_stims = MEP amplitude overlayed in an array the same size as the T1 image, dilated across 5 voxels
    #       (so 5mm isotropic) in the script
    #     - map_samples = the same as stims, but no dilation, so... 1mm isotropic?
    #     - map_grid = 'binary' mask, 0 or 99, which points had a stim? Originally 
    #       also points orthogonally adjacent to each stim point are 1 instead of 99.
    
    # Dilate voxels of TMS stimulation to cover more of the T1 image, so instead
    # of a TMS MEP overlayed over a 1mm voxel, it's dilated to cover 5x5x5mm of voxels
    """
    --- DEV NOTE ---
    Need to ensure that borders between MEPs are maintained, no values are overwritten if dilation is too large
        - if user inputs resolution in configure GUI, we can check if dilation is too large for the voxel size?
    """
    dilate_offset = (dilate-1)/2
    # for all rows with nonzero MEPs, duplicate their values over the neighbouring region, the number
    # of times the value is replicated is determined by the dilate variable, which must be odd.
    for row in np.where(data_nibs_map[3] > MEP_thresh)[0]:
        x_lower = int(data_nibs_map[0][row]) - int(dilate_offset) - 1
        x_higher = int(data_nibs_map[0][row]) + int(dilate_offset)
        y_lower = int(data_nibs_map[1][row]) - int(dilate_offset) - 1
        y_higher = int(data_nibs_map[1][row]) + int(dilate_offset)
        z_lower = int(data_nibs_map[2][row]) - int(dilate_offset) - 1
        z_higher = int(data_nibs_map[2][row]) + int(dilate_offset)
        map_stims[x_lower:x_higher,y_lower:y_higher,z_lower:z_higher] = data_nibs_map[3][row]
                
    # Rotate matrices in the y dimension (AP) to convert from RPS (Brainsight) to RAS (Nifti)
    # RPS = +x is right, +y is posterior, +z is superior
    # RAS = +x is right, +y is anterior, +z is superior
    if data_dict['stim_flip'] == 1:
        logging.info('stim_flip == 1 check succeeded, flipping.')
        map_stims = np.flip(map_stims,1)
        map_samples = np.flip(map_samples,1)
        map_grid = np.flip(map_grid,1)
    else:
        logging.info('stim_flip type is '+str(type(data_dict['stim_flip'])))
    
    
    # ~~~~~~CALCULATE METRICS~~~~~~
    # MAP HOTSPOT:
    # numpy.argmax to get a linear index for the max value in the samples array, then
    # numpy.unravel_index to get the 3D index (x,y,z) from that linear index
    results_hotspot = np.unravel_index(np.argmax(map_samples), map_samples.shape)
    
    # MAP CENTER OF GRAVITY
    # convenient method from scipy / ndimage (imported as ndi)
    results_center_mass = ndi.measurements.center_of_mass(map_samples)


    # ~~~~~~SAVE FILES~~~~~~
    # Stimulations: Main output, MEP amplitudes within a matrix sized to match structural image.
    #               Stimulations from experiment have been uniformaly dilated by the 'dilate' integer.
    # Heatmap:      Stimulations map with a gaussian filter applied to smooth the data
    file_grid = save_dir+'/'+save_prefix+'_grid.nii'
    file_hotspot = save_dir+'/'+save_prefix+'_responses.nii'
    file_heatmap = save_dir+'/'+save_prefix+'_heatmap.nii'
    
    # Grid save
    nii_grid = nib.Nifti1Image(map_grid, data_T1.affine)
    if not os.path.exists(file_grid):
        logging.info('...saving stimulation grid!')
        nib.save(nii_grid, file_grid)
    
    # Stimulations save
    # Nibabel save nifti only needs the image data and an affine, which we'll re-use from the T1 image
    nii_hotspot = nib.Nifti1Image(map_stims, data_T1.affine)
    if not os.path.exists(file_hotspot):
        logging.info('...saving hotspots!')
        nib.save(nii_hotspot, file_hotspot)
    
    # Heatmap save
    # Smooth the hotspot map using a 3D Gaussian
    # Interestingly, FWHM = 2.355 * s.d. for Gaussian distribution, so divide smooth by 2.355 to get s.d.
    stdev_gaussian = smooth/2.355
    map_heatmap = ndi.gaussian_filter(map_stims,stdev_gaussian,0,mode='reflect')
    nii_heatmap = nib.Nifti1Image(map_heatmap, data_T1.affine)
    if not os.path.exists(file_heatmap):
        logging.info('...saving heatmap!')
        nib.save(nii_heatmap, file_heatmap)

    # Make and save spreadsheet of values! Courtesy of pandas DataFrame.to_excel method.
    measures_dict = {'Participant':data_dict['save_prefix'],
                    'Image File':data_dict['image'],
                    'Stim file':data_dict['stim'],
                    'MEP Threshold':config_dict['MEP_threshold'],
                    'Hotspot X':results_hotspot[0],
                    'Hotspot Y':results_hotspot[1],
                    'Hotspot Z':results_hotspot[2],
                    'Hotspot MEP':map_samples[np.unravel_index(np.argmax(map_samples), map_samples.shape)],
                    'COG X':results_center_mass[0],
                    'COG Y':results_center_mass[1],
                    'COG Z':results_center_mass[2]}
    measures_dataframe = pd.DataFrame(measures_dict, index=[0])
    measures_file = save_dir+'/'+save_prefix+'_results.xlsx'
    measures_dataframe.to_excel(measures_file)
    
    
    # ~~~~~~NORMALIZE MAPS TO STANDARD SPACE~~~~~~
    # Note this has to come after saving the initial files, as warps are applied to the heatmap
    if int(config_dict['normalize']) == 1:
        logging.info('Normalization to standard atlas beginning!')
        logging.info('Atlas chosen: '+file_atlas)
        # FLIRT section:
        # Register T1 image to MNI_152 template using FLIRT and FNIRT
        t1_flirt_mni = fsl.FLIRT()
        t1_flirt_mni.inputs.in_file = file_t1
        t1_flirt_mni.inputs.reference = file_atlas
        t1_flirt_mni.inputs.out_file = save_dir+'/T1_mni_FLIRT_out.nii.gz'
        t1_flirt_mni.inputs.out_matrix_file = save_dir+'/T1_mni_FLIRT_omat.mat'
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
        # heatmap or other measure map
        heatmap_applyxfm.inputs.in_file = save_dir+'/'+save_prefix+'_heatmap.nii'
        heatmap_applyxfm.inputs.in_matrix_file = save_dir+'/T1_mni_FLIRT_omat.mat'
        heatmap_applyxfm.inputs.out_file = save_dir+'/'+save_prefix+'_normalized_heatmap.nii.gz'
        heatmap_applyxfm.inputs.reference = file_atlas
        heatmap_applyxfm.inputs.apply_xfm = True
        result = heatmap_applyxfm.run()
    
    """
        DEV NOTE
        - addon: skullstrip
            - uses mos_segment_job.m
    """

if __name__ == '__main__':
    main()

