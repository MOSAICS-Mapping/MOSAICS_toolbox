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
import glob
import subprocess
import nibabel as nib
import pandas as pd
import openpyxl
import numpy as np
from scipy import ndimage as ndi
from nipype.interfaces import fsl
import logging

import mos_skullstrip
import mos_normalize_to_mni

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(data_dict, config_dict):

    # ~~~~~~SET UP VARIABLES~~~~~~
    data_folder = data_dict['data folder']
    data_list = data_dict['data list']
    
    # save directory
    save_dir = str(data_dict['save_dir'])
    
    # # save prefix
    # save_prefix = str(data_dict['save_prefix'])
    
    # dilate variable
    dilate = int(config_dict['dilate'])
    # smooth variable
    smooth = int(config_dict['smooth'])
    # MEP threshold
    MEP_thresh = int(config_dict['MEP_threshold'])

    # # Create output directory
    # os.makedirs(os.getcwd()+'/outputs/',exist_ok=True)
    
    # Initialize a couple lists before our for loop so we can create a dataframe to
    # output for our results spreadsheet!
    results_column_names = ['Participant',
                            'Image File',
                            'Stim file',
                            'MEP Threshold',
                            'Hotspot X',
                            'Hotspot Y',
                            'Hotspot Z',
                            'Hotspot MEP',
                            'COG X',
                            'COG Y',
                            'COG Z']
    results_metrics_list = list()
    
    for subject in data_list:
        
        logging.critical(subject)
        
        # data_list constructed, and these variables determined, by mos_find_datasets.py
        tag = subject[0]
        file_t1 = subject[1]
        file_nibs_map = subject[2]
        
        logging.critical(file_t1)
        
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
    
        # ~~~~~~STRIP T1 image~~~~~~
        mos_skullstrip.main(tag, file_t1, save_dir)
    
        # ~~~~~~SAVE FILES~~~~~~
        # Stimulations: Main output, MEP amplitudes within a matrix sized to match structural image.
        #               Stimulations from experiment have been uniformaly dilated by the 'dilate' integer.
        # Heatmap:      Stimulations map with a gaussian filter applied to smooth the data
        file_grid = save_dir+'/'+tag+'_grid.nii'
        file_hotspot = save_dir+'/'+tag+'_responses.nii'
        file_heatmap = save_dir+'/'+tag+'_heatmap.nii'
        
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
    
        # Heatmap: apply brain mask to limit smoothing
        file_brainmask = save_dir+'/'+tag+'_brain_mask.nii.gz'
        mask_heatmap = fsl.ApplyMask()
        mask_heatmap.inputs.in_file = file_heatmap
        mask_heatmap.inputs.mask_file = file_brainmask
        mask_heatmap.inputs.out_file = save_dir+'/'+tag+'_heatmap_masked.nii.gz'
        mask_result = mask_heatmap.run()
    
        # Make a list of this subject's values, then append it to the overall results list
        # For variables order see line 69 above (results_column_names)
        measures_list = [tag,
                        file_t1,
                        file_nibs_map,
                        config_dict['MEP_threshold'],
                        results_hotspot[0],
                        results_hotspot[1],
                        results_hotspot[2],
                        map_samples[np.unravel_index(np.argmax(map_samples), map_samples.shape)],
                        results_center_mass[0],
                        results_center_mass[1],
                        results_center_mass[2]]
        results_metrics_list.append(measures_list)        
    
        # ~~~~~~NORMALIZE MAPS TO STANDARD SPACE~~~~~~
        # Note this has to come after saving the initial files, as warps are applied to the heatmap
        if int(config_dict['normalize']) == 1:
            mos_normalize_to_mni.main(subject, data_dict, config_dict)

    # print values to spreadsheet after the loop has completed
    metrics_dataframe = pd.DataFrame(results_metrics_list, columns=results_column_names)    
    measures_file = save_dir+'/mapping_results.xlsx'
    metrics_dataframe.to_excel(measures_file)

if __name__ == '__main__':
    main()
    logging.info('...MOSAICS analysis completed successfully!')

