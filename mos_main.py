#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 4 10:15:48 2021

@author: Bryce Geeraert

MOSAICS - Mapping of sensory activation hotspots during cortical stimulation 

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

import mos_skullstrip
import mos_normalize_to_mni

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(data_dict, config_dict):

    # ~~~~~~SET UP VARIABLES~~~~~~
    data_folder = data_dict['data folder']
    data_list = data_dict['data list']
    
    # # save directory
    # save_dir = str(data_dict['save_dir'])
    save_dir_parent = str(data_dict['save_dir'])
    
    # dilate variable
    dilate = int(config_dict['dilate'])
    # smooth variable
    smooth = int(config_dict['smooth'])
    # MEP threshold
    MEP_thresh = int(config_dict['MEP_threshold'])

    # # # Create output directory
    # os.makedirs(save_dir,exist_ok=True)
    
    # Initialize a couple lists before our for loop so we can create a dataframe to
    # output for our results spreadsheet!
    results_column_names = ['Image File Name',
                            'Stim File Name',
                            'Hotspot X',
                            'Hotspot Y',
                            'Hotspot Z',
                            'Hotspot MEP (not scaled)',
                            'COM X',
                            'COM Y',
                            'COM Z',
                            'SD Hotspot X',
                            'SD Hotspot Y',
                            'SD Hotspot Z',
                            'SD COM X',
                            'SD COM Y',
                            'SD COM Z']
    results_metrics_list = list()
    
    for subject in data_list:
        # data_list constructed, and these variables determined, by mos_find_datasets.py
        # tag = subj name, stim_name = name of stimulation data, structural = nii*, stim_data = xls*
        tag = subject[0]
        stim_file = subject[1]
        #file_t1 = subject[2]
        #file_nibs_map = subject[3]
        file_t1 = os.path.join(data_folder,subject[2])
        file_nibs_map = os.path.join(data_folder,subject[3])
        file_atlas = str(config_dict['atlas'])
        
        #save directory, including sub-directory for each subject
        save_dir = str(data_dict['save_dir']+'/'+stim_file)
        
        # # Create output directory
        os.makedirs(save_dir,exist_ok=True)
        
        # establish save file names
        file_grid = os.path.join(save_dir,stim_file+'_grid.nii')
        file_stims = os.path.join(save_dir,stim_file+'_responses.nii')
        # Noscale (below) used to warp heatmap to standard space, then normalize and apply mask
        file_heatmap_noscale = os.path.join(save_dir,stim_file+'_heatmap_noscale.nii')
        # Nomask includes normalized MEP values for heatmap, and is masked by fsl.ApplyMask() on line 237
        file_heatmap_nomask = os.path.join(save_dir,stim_file+'_heatmap_unmasked.nii')
        # Below variable is used on line 236
        file_heatmap = os.path.join(save_dir,stim_file+'_heatmap.nii.gz')
        file_heatmap_warped = os.path.join(save_dir,stim_file+'_warped_heatmap.nii.gz')
                
        logging.info('...processing '+tag+', stim data: '+file_nibs_map)
    
    
        # ~~~~~~LOAD DATA~~~~~~
        # Read in a 1mm isotropic T1-weighted MRI .nii
        data_T1 = nib.load(file_t1)
        
        # Dead the Brainsight coordindates file
        # should be four columns. X, Y, Z, and the corresponding MEP amplitude for that location
        data_nibs_map = pd.read_excel(file_nibs_map,header=None)
        # data_nibs_map[0] = round(data_nibs_map[0])
        # data_nibs_map[1] = round(data_nibs_map[1])
        # data_nibs_map[2] = round(data_nibs_map[2])
        
        
        # ~~~~~~STRIP T1 image~~~~~~
        # reminder, brainmask check = 0 if user does not provide their own brainmask and
        # MOSAICS is to devise its own (we use default BET settings)
        if config_dict['brainmask check'].get() == 0:
            mos_skullstrip.main(tag, file_t1, data_folder, save_dir)
            file_brainmask = os.path.abspath(os.path.join(data_folder, tag+'_brain_mask.nii.gz'))
        elif config_dict['brainmask check'].get() == 1:
            file_brainmask = os.path.abspath(os.path.join(data_folder, tag+config_dict['brainmask suffix']))
        
        
        # ~~~~~~SET UP STIM DATA VARIABLES~~~~~~
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
        
        
        # ~~~~~~RESLICE STRUCTURAL AND STIM IMAGES~~~~~~
        # nibabel.processing.conform(data_T1) produces a 1mm isotropic, 256x256x256 image
        #   above also reorients the image to RAS which is something I guess.
        
        # ~~~~~~DILATE STIMULATION DATA (MAP_STIMS)~~~~~~
        logging.info('...dilating stimulation coordinates by '+str(config_dict['dilate'])+' voxels')
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
        if data_dict['stim_flip'].get() == 1:
            logging.info('...Flipping coordinates of stimulations along anterior-posterior axis')
            map_stims = np.flip(map_stims,1)
            map_samples = np.flip(map_samples,1)
            map_grid = np.flip(map_grid,1)
        
        
        # ~~~~~~PRODUCE HEATMAP~~~~~~
        # Smooth the hotspot map using a 3D Gaussian
        # Interestingly, FWHM = 2.355 * s.d. for Gaussian distribution, so divide smooth by 2.355 to get s.d.
        logging.info('...producing heatmap of responsive sites')
        stdev_gaussian = smooth/2.355
        map_heatmap = ndi.gaussian_filter(map_stims,stdev_gaussian,0,mode='reflect')


        # ~~~~~~NORMALIZE MEPs~~~~~~
        logging.info('...normalizing response map (by hotspot MEP)')
        
        # First, we need to calculate the max MEPs observed in samples (initial coordinates) and heatmap arrays
        # numpy.argmax to get a linear index for the max value in the samples array, then
        # numpy.unravel_index to get the 3D index (x,y,z) from that linear index
        results_ps_hotspot = np.unravel_index(np.argmax(map_heatmap), map_heatmap.shape)
        # better to use map_samples below than map_stims (dilated) because the maximum value will be observed
        # at one location instead of spread across a dilated space
        MEP_ps_max = map_samples[np.unravel_index(np.argmax(map_samples), map_samples.shape)]
        MEP_ps_smoothed = map_heatmap[results_ps_hotspot]
        
        # need to normalize both the stimulations map (stims) and dilated stimulations as well (samples)
        map_stims_normalized = (map_stims / MEP_ps_max) * 100 
        ### map_samples_normalized = (map_samples / MEP_ps_max) * 100 #i don't think is used anywhere?
        # normalizing heatmap so that all subjects will be on a scale of 0 / 100. 
        map_heatmap_ps_normal = (map_heatmap / MEP_ps_smoothed) * 100


        # ~~~~~~SAVE PATIENT SPACE FILES~~~~~~
        # Stimulations: MEP amplitudes within a matrix sized to match structural image.
        #               Stimulations from experiment have been uniformaly dilated by the 'dilate' integer.
        # Heatmap:      Stimulations map with a gaussian filter applied to smooth the data
        
        # Grid save
        nii_grid = nib.Nifti1Image(map_grid, data_T1.affine)
        if not os.path.exists(file_grid):
            logging.info('...saving stimulation grid!')
            nib.save(nii_grid, file_grid)
            
        # Stimulations save (normalized on line 209)
        # Nibabel save nifti only needs the image data and an affine, which we'll re-use from the T1 image
        nii_hotspot = nib.Nifti1Image(map_stims_normalized, data_T1.affine)
        if not os.path.exists(file_stims):
            logging.info('...saving responses map!')
            nib.save(nii_hotspot, file_stims)

        # Raw heatmap save, for use by mos_normalize_to_mni (line 239, below)
        nii_heatmap_no_scaling = nib.Nifti1Image(map_heatmap, data_T1.affine)
        if not os.path.exists(file_heatmap_noscale):
            nib.save(nii_heatmap_no_scaling, file_heatmap_noscale)

        # Normalized heatmap save
        nii_heatmap = nib.Nifti1Image(map_heatmap_ps_normal, data_T1.affine)
        if not os.path.exists(file_heatmap_nomask):
            logging.info('...saving patient-space heatmap with weighted MEPs')
            nib.save(nii_heatmap, file_heatmap_nomask)


        # ~~~~~~MASK HEATMAP MAPS IN PATIENT SPACE~~~~~~
        # Heatmap: apply brain mask to limit smoothing into skull / scalp
        # native space mask application
        logging.info('...applying brainmask to heatmap')
        file_brainmask = os.path.join(data_folder,tag+str(config_dict['brainmask suffix']))
        mask_heatmap = fsl.ApplyMask()
        mask_heatmap.inputs.in_file = file_heatmap_nomask
        mask_heatmap.inputs.mask_file = file_brainmask
        mask_heatmap.inputs.out_file = file_heatmap
        mask_result = mask_heatmap.run()
        
        
        # ~~~~~~CALCULATE METRICS (patient space)~~~~~~
        
        # load back in masked heatmap to calculate metrics
        map_heatmap_masked = nib.load(file_heatmap).get_fdata()        
        
        # HOTSPOT:
        # raw MEP from the stim data, and smoothed (post-Gaussian filter), needed to normalize patient heatmap
        results_ps_hotspot = np.unravel_index(np.argmax(map_heatmap_masked), map_heatmap_masked.shape)
        
        # CENTER OF MASS:
        # convenient method from scipy / ndimage (imported as ndi)
        results_ps_center_mass = ndi.measurements.center_of_mass(map_heatmap_masked)


        # ~~~~~~REPEAT RELEVANT STEPS IF DATA NORMALIZED~~~~~~        
        # Note this has to come after saving the initial files, as warps are applied to the heatmap
        if config_dict['normalize'].get() == 1:
            logging.info('...normalizing heatmap to standard atlas')
            
            # register and establish name of the warped map, for functions below
            mos_normalize_to_mni.main(tag, stim_file, data_folder, save_dir, file_t1, file_heatmap_nomask, file_atlas)
            #mos_normalize_to_mni.main(subject, data_dict, config_dict)
            
            # standard space mask application to heatmap
            mask_warped_heatmap = fsl.ApplyMask()
            mask_warped_heatmap.inputs.in_file = file_heatmap_warped
            #mask_normalized_heatmap.inputs.mask_file = os.path.join(data_folder,'MNI152_T1_1mm_brain_mask.nii.gz') # can delete once I check
            mask_warped_heatmap.inputs.mask_file = str(config_dict['atlas mask'])
            mask_warped_heatmap.inputs.out_file = file_heatmap_warped
            mask_warped_result = mask_warped_heatmap.run()
            
            # load in normalized heatmap to calculate some metrics
            data_heatmap_normalized = nib.load(file_heatmap_warped)
            map_heatmap_normalized = data_heatmap_normalized.get_fdata()
            
            # calculate standard space (sd) hotspot
            results_sd_hotspot = np.unravel_index(np.argmax(map_heatmap_normalized), map_heatmap_normalized.shape)
            MEP_sd_smoothed = map_heatmap_normalized[results_sd_hotspot]
            
            # calculate standard space center of gravity
            results_sd_center_mass = ndi.measurements.center_of_mass(map_heatmap_normalized)
            # Replace tuple with 
            rounded_sd_center_mass = (round(results_sd_center_mass[0]),
                                      round(results_sd_center_mass[1]),
                                      round(results_sd_center_mass[2]))
            
            # normalize MEPs / intensity values for standard space heatmap
            map_heatmap_sd_normal = (map_heatmap_normalized / MEP_sd_smoothed) * 100
            
            # Overwrite previously warped, masked heatmap with a new, weighted MEP version
            logging.info('...weighting MEPs of normalized heatmap')
            file_heatmap_sd_normal = os.path.join(save_dir,stim_file+'_warped_heatmap.nii.gz')
            nii_heatmap_sd_normal = nib.Nifti1Image(map_heatmap_sd_normal, data_heatmap_normalized.affine)
            nib.save(nii_heatmap_sd_normal, file_heatmap_sd_normal)
            
            # standard space values are added to dict below, on line 292
        else:
            # put n/a values in correct dict locations
            results_sd_hotspot = ('-','-','-')
            rounded_sd_center_mass = ('-','-','-')

    
        # ~~~~~~OUTPUT SUBJECT METRICS TO RESULTS SPREADSHEET~~~~~~
        # Make a list of this subject's values, then append it to the overall results list
        # Variable order set on line 69 above (results_column_names):
        # Participant, Image File, Stim file, MEP threshold, Hotspot X, Y, Z, Hotspot MEP, COG X, Y, Z, 
        # Standard hotspot X, Y, Z, Standard COG X, Y, Z
            
        measures_list = [tag,
                        stim_file,
                        results_ps_hotspot[0],
                        results_ps_hotspot[1],
                        results_ps_hotspot[2],
                        MEP_ps_max,
                        round(results_ps_center_mass[0]),
                        round(results_ps_center_mass[1]),
                        round(results_ps_center_mass[2]),
                        results_sd_hotspot[0],
                        results_sd_hotspot[1],
                        results_sd_hotspot[2],
                        rounded_sd_center_mass[0],
                        rounded_sd_center_mass[1],
                        rounded_sd_center_mass[2]]
        results_metrics_list.append(measures_list)        
       
        # ~~~~~~CLEAN UP UNNECESSARY FILES~~~~~~
        os.remove(file_heatmap_nomask)
        os.remove(file_heatmap_noscale)
        #os.remove(os.path.join(save_dir,tag+'_FLIRT_omat.mat'))
        if os.path.isfile(os.path.join(save_dir,stim_file+'_heatmap_flirt.mat')):
            os.remove(os.path.join(save_dir,stim_file+'_heatmap_flirt.mat'))
            # os.remove(file_heatmap_warped)

    # ~~~~~~print values to spreadsheet after the loop has completed~~~~~~
    metrics_dataframe = pd.DataFrame(results_metrics_list, columns=results_column_names)    
    measures_file = os.path.join(save_dir_parent,'mapping_results.xlsx')
    metrics_dataframe.to_excel(measures_file)

    logging.info('...MOSAICS analysis completed successfully!')

if __name__ == '__main__':
    main()
    

