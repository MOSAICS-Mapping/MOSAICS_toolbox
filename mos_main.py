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
from nibabel.affines import apply_affine
import pandas as pd
import numpy as np
from scipy import ndimage as ndi
from nipype.interfaces import fsl
import logging

import mos_skullstrip
import mos_warp_to_mni

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(data_dict, config_dict):

    print()
    # ~~~~~~ SET UP GLOBAL VARIABLES ~~~~~~
    data_folder = data_dict['data folder']
    data_list = data_dict['data list']

    if len(data_list) != 0:
    
        logging.info('...MOSAICS analysis beginning.')    
        
        # # save directory
        save_dir_parent = str(data_dict['save_dir'])
        
        # dilate variable
        dilate = int(config_dict['dilate'])
        # smooth variable
        smooth = int(config_dict['smooth'])
        # MEP threshold
        MEP_thresh = int(config_dict['MEP_threshold'])
        
        file_atlas = str(config_dict['atlas'])
        
        # Initialize a list before our for loop so we can create a dataframe to
        # output for our results spreadsheet!
        results_column_names = ['Image File Name',
                                'Stim File Name',
                                'Hotspot X',
                                'Hotspot Y',
                                'Hotspot Z',
                                'Max MEP',
                                'COM X',
                                'COM Y',
                                'COM Z',
                                'SD Hotspot X',
                                'SD Hotspot Y',
                                'SD Hotspot Z',
                                'SD COM X',
                                'SD COM Y',
                                'SD COM Z',
                                'Coordinates Used',
                                'Dilation (mm)',
                                'Smoothing kernel (mm)',
                                'MEP threshold (%)']
        results_metrics_list = list()
        
        for subject in data_list:
            
            # ~~~~~~SET UP SUBJECT-SPECIFIC VARIABLES~~~~~~
            
            # data_list constructed, and these variables determined, by mos_find_datasets.py
            # tag = subj name, stim_name = name of stimulation data (everything before .xls(x) extension),
            # structural = nii*, stim_data = xls*
            tag = subject[0]
            stim_file = subject[1]
    
            file_t1 = os.path.join(data_folder,subject[2])
            file_nibs_map = os.path.join(data_folder,subject[3])
            
            #save directory, including sub-directory for each subject
            save_dir = str(data_dict['save_dir']+'/'+stim_file)
            
            # # Create output directory
            os.makedirs(save_dir,exist_ok=True)
            
            # establish save file names
            file_grid = os.path.join(save_dir,stim_file+'_grid.nii.gz')
            file_responses = os.path.join(save_dir,stim_file+'_responses.nii.gz')
            # Noscale (below) is the initial heatmap, gets warped to standard space used
            file_heatmap_ps_initial = os.path.join(save_dir,stim_file+'_heatmap_initial.nii')
            # Nomask includes weighted MEP values for heatmap, and is masked by fsl.ApplyMask() on line ~237
            file_heatmap_ps_weighted = os.path.join(save_dir,stim_file+'_heatmap_weighted.nii')
            # Below variable is used on line 236
            file_heatmap_ps_final = os.path.join(save_dir,stim_file+'_heatmap.nii.gz')
            file_heatmap_sd = os.path.join(save_dir,stim_file+'_warped_heatmap.nii.gz')
                    
        # ~~~~~~ VARIABLE ASSIGNMENT WRAPS UP HERE ~~~~~~
            
            logging.info('...processing '+tag+', stim data: '+file_nibs_map)
        
            # ~~~~~~LOAD DATA~~~~~~
            # Read in a 1mm isotropic T1-weighted MRI .nii
            data_T1 = nib.load(file_t1)
            
            # Dead the Brainsight coordindates file
            # should be four columns. X, Y, Z, and the corresponding MEP amplitude for that location
            data_nibs_map = pd.read_excel(file_nibs_map,header=None)
            
            
            # ~~~~~~STRIP T1 image~~~~~~
            # reminder, brainmask check = 0 if user does not provide their own brainmask and
            # MOSAICS is to devise its own (we use default BET settings)
            
            if config_dict['brainmask check'].get() == 0:
                logging.info('...performing BET skull stripping')
                ps_brainmask = mos_skullstrip.main(tag, file_t1, data_folder, save_dir)
            elif config_dict['brainmask check'].get() == 1:
                ps_brainmask = os.path.abspath(os.path.join(data_folder, tag+config_dict['brainmask suffix']))
            
            
            # ~~~~~~SET UP STIM DATA ARRAYS~~~~~~
            # Create an array of zeroes equal to size of T1 image, to initialize our output images
            
            # What are these maps (below)?
            #     - map_responses = MEP amplitude overlayed in an array the same size as the T1 image, dilated across 5 voxels
            #       (so 5mm isotropic) in the script
            #     - map_samples = the same as responses, but no dilation, so... 1mm isotropic?
            #     - map_grid = 'binary' mask, 0 or 99, which points had a stim? Originally 
            #       also points orthogonally adjacent to each stim point are 1 instead of 99.
            
            map_outputs = initialize_stim_arrays(data_T1, data_nibs_map, MEP_thresh)
            map_grid = map_outputs['grid']
            map_samples = map_outputs['samples']
            map_responses = map_outputs['responses']
            
    
            # ~~~~~~SAVE RESPONSE MAP SO WE CAN DILATE~~~~~~
            save_map(file_responses, map_responses, data_T1)
    
            """
            --- DEV NOTE ---
            Need to ensure that borders between MEPs are maintained, no values are overwritten if dilation is too large
                - if user inputs resolution in configure GUI, we can check if dilation is too large for the voxel size?
            """
            
            # ~~~~~~RESLICE STRUCTURAL AND STIM IMAGES~~~~~~
            # nibabel.processing.conform(data_T1) produces a 1mm isotropic, 256x256x256 image
            #   above also reorients the image to RAS which is something I guess.
            
            #   - Not implemented yet. Helen has notes in Slack I have not read yet.
            
            
            # ~~~~~~DILATE STIMULATION DATA (MAP_RESPONSES)~~~~~~
            logging.info('...dilating stimulation coordinates by '+str(config_dict['dilate'])+' voxels')
            
            map_responses_dilate = fsl.DilateImage()
            map_responses_dilate.inputs.in_file = file_responses
            map_responses_dilate.inputs.operation = 'max'
            map_responses_dilate.inputs.kernel_shape = 'sphere'
            map_responses_dilate.inputs.kernel_size = dilate
            map_responses_dilate.inputs.out_file = file_responses
            map_responses_temp = map_responses_dilate.run()
            
    
            # ~~~~~~FLIP MAPS ANTERIOR/POSTERIOR IF BRAINSIGHT COORDINATES USED~~~~~~   
            # Rotate matrices in the y dimension (AP) to convert from RPS (Brainsight) to RAS (Nifti)
            # RPS = +x is right, +y is posterior, +z is superior
            # RAS = +x is right, +y is anterior, +z is superior
            if data_dict['stim_coords'].get() == "Brainsight":
                logging.info('...flipping coordinates of stimulations along anterior-posterior axis')
                map_responses = np.flip(map_responses,1)
                map_samples = np.flip(map_samples,1)
                map_grid = np.flip(map_grid,1)
            
            
            # ~~~~~~PRODUCE HEATMAP~~~~~~
            # Smooth the hotspot map using a 3D Gaussian
            # Interestingly, FWHM = 2.355 * s.d. for Gaussian distribution, so divide smooth by 2.355 to get s.d.
            logging.info('...producing heatmap of responsive sites')
            stdev_gaussian = smooth/2.355
            map_heatmap_ps_initial = ndi.gaussian_filter(map_responses,stdev_gaussian,0,mode='reflect')
    
    
            # ~~~~~~WEIGHT MEPs~~~~~~
            logging.info('...normalizing response map (by hotspot MEP)')
            
            MEP_ps_max, map_responses_weighted, map_heatmap_ps_weighted =\
                normalize_ps_heatmap(map_heatmap_ps_initial, map_samples, map_responses)
    
    
            # ~~~~~~SAVE PATIENT SPACE FILES~~~~~~
            # Stimulations: MEP amplitudes within a matrix sized to match structural image.
            #               Stimulations from experiment have been uniformaly dilated by the 'dilate' integer.
            # Heatmap:      Stimulations map with a gaussian filter applied to smooth the data
            
            logging.info('...saving stimulation sites (grid), responsive sites (responses), and heatmap (heatmap)')
            save_map(file_grid, map_grid, data_T1)
            save_map(file_responses, map_responses_weighted, data_T1)
            save_map(file_heatmap_ps_initial, map_heatmap_ps_initial, data_T1)
            save_map(file_heatmap_ps_weighted, map_heatmap_ps_weighted, data_T1)
    
    
            # ~~~~~~MASK HEATMAP MAPS IN PATIENT SPACE~~~~~~
            # Heatmap: apply brain mask to limit smoothing into skull / scalp
            # native space mask application
            logging.info('...applying brainmask to patient-space heatmap')
            mask_heatmap(file_heatmap_ps_weighted, ps_brainmask, file_heatmap_ps_final)
            
            
            # ~~~~~~CALCULATE METRICS (patient space)~~~~~~
            
            # load back in masked heatmap to calculate metrics
            map_heatmap_masked = nib.load(file_heatmap_ps_final).get_fdata()        
            
            # HOTSPOT:
            # raw MEP from the stim data, and smoothed (post-Gaussian filter), needed to normalize patient heatmap
            results_ps_hotspot = np.unravel_index(np.argmax(map_heatmap_masked), map_heatmap_masked.shape)
            
            # CENTER OF MASS:
            # convenient method from scipy / ndimage (imported as ndi)
            results_ps_center_mass = ndi.measurements.center_of_mass(map_heatmap_masked)
    
    
            # ~~~~~~REPEAT RELEVANT STEPS IF DATA NORMALIZED~~~~~~        
            # Note this has to come after saving the initial files, as warps are applied to the heatmap
            if config_dict['normalize'].get() == 1:
                
                logging.info('...normalizing heatmap to standard space (SD)')
                
                # -- register and establish name of the warped map, for functions below
                logging.info('...atlas chosen: '+file_atlas)
                mos_warp_to_mni.main(tag, stim_file, data_folder, save_dir, file_t1, file_heatmap_ps_weighted, file_atlas)
                
                # -- standard space mask application to heatmap
                logging.info('...applying brainmask to standard-space heatmap')
                mask_heatmap(file_heatmap_sd, str(config_dict['atlas mask']), file_heatmap_sd)
                
                # -- load in normalized heatmap to calculate some metrics
                data_heatmap_warped = nib.load(file_heatmap_sd)
                map_heatmap_warped = data_heatmap_warped.get_fdata()
                
                # -- calculate standard space (sd) hotspot
                results_sd_hotspot = np.unravel_index(np.argmax(map_heatmap_warped), map_heatmap_warped.shape)
                MEP_sd_smoothed = map_heatmap_warped[results_sd_hotspot]
                
                # -- calculate standard space center of gravity
                results_sd_center_mass = ndi.measurements.center_of_mass(map_heatmap_warped)
                # Replace tuple with 
                ## Probably don't need this unrounded tuple bit, no changes made
                # rounded_sd_center_mass = (results_sd_center_mass[0],
                #                           results_sd_center_mass[1],
                #                           results_sd_center_mass[2])
                
                # results_sd_center_mass = (round(results_sd_center_mass[0]),
                #                           round(results_sd_center_mass[1]),
                #                           round(results_sd_center_mass[2]))
                
                # -- Convert standard space hotspot / COM from voxel coordinates to SD anatomical coords (mm)
                atlas_affine = nib.load(file_atlas)
                atlas_affine = atlas_affine.affine
                ## Hotspot
                results_sd_hotspot = apply_affine(atlas_affine, results_sd_hotspot)
                ## COM
                results_sd_center_mass = apply_affine(atlas_affine, results_sd_center_mass)
                
                # normalize MEPs / intensity values for standard space heatmap
                map_heatmap_sd_normal = (map_heatmap_warped / MEP_sd_smoothed) * 100
                
                # Overwrite previously warped, masked heatmap with a new, weighted MEP version
                # logging.info('...weighting MEPs of standard-space heatmap')
                file_heatmap_sd_normal = os.path.join(save_dir,stim_file+'_warped_heatmap.nii.gz')
                nii_heatmap_sd_normal = nib.Nifti1Image(map_heatmap_sd_normal, data_heatmap_warped.affine)
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
                            results_sd_center_mass[0],
                            results_sd_center_mass[1],
                            results_sd_center_mass[2],
                            data_dict['stim_coords_list'],
                            str(dilate),
                            str(smooth),
                            str(MEP_thresh)]
            results_metrics_list.append(measures_list)        
            
            #clean up files, put into a separate function, see if that helps track everything
            file_cleanup(file_heatmap_ps_initial, file_heatmap_ps_weighted, save_dir, stim_file)
            
            logging.info('...analysis completed for '+tag)
            print()
    
        # ~~~~~~print values to spreadsheet after the loop has completed~~~~~~
        metrics_dataframe = pd.DataFrame(results_metrics_list, columns=results_column_names)    
        measures_file = os.path.join(save_dir_parent,'mapping_results.xlsx')
        metrics_dataframe.to_excel(measures_file)
    
        logging.info('...MOSAICS analysis completed successfully!')
        
    else:
        
        logging.error('...No subjects found for processing, MOSAICS processing not run')

# SUB-FUNCTIONS USED IN MAIN (SEPARATED FOR READABILITY / CLEANLINESS)
def initialize_stim_arrays(data_T1, data_nibs_map, MEP_thresh):

    map_responses = np.zeros(data_T1.shape)
    map_samples = np.zeros(data_T1.shape)
    map_grid = np.zeros(data_T1.shape)
    
    # Put all MEP values in to the arrays of zeroes at their corresponding x,y,z coordinates
    # index variable has a name (eg. 134) and dtype (eg. float64)
    # row variable has all variables in the row, 0 = x, 1 = y, 2 = z, 3 = mep amplitude
    for index, row in data_nibs_map.iterrows():
        if row[3] >= MEP_thresh:
            map_responses[int(row[0]),int(row[1]),int(row[2])] = row[3]
            map_samples[int(row[0]),int(row[1]),int(row[2])] = row[3]
            map_grid[int(row[0])-1,int(row[1])-1,int(row[2])-1] = 1
    
    outputs_dict = dict()
    outputs_dict['grid'] = map_grid
    outputs_dict['samples'] = map_samples
    outputs_dict['responses'] = map_responses
    
    return outputs_dict

def normalize_ps_heatmap(map_heatmap_ps_initial, map_samples, map_responses):
    
    # First, we need to calculate the max MEPs observed in samples (initial coordinates) and heatmap arrays
    # numpy.argmax to get a linear index for the max value in the samples array, then
    # numpy.unravel_index to get the 3D index (x,y,z) from that linear index
    results_ps_hotspot = np.unravel_index(np.argmax(map_heatmap_ps_initial), map_heatmap_ps_initial.shape)
    
    # better to use map_samples below than map_responses (dilated) because the maximum value will be observed
    # at one location instead of spread across a dilated space
    MEP_ps_max = map_samples[np.unravel_index(np.argmax(map_samples), map_samples.shape)]
    MEP_ps_smoothed = map_heatmap_ps_initial[results_ps_hotspot]
    
    # need to normalize both the stimulations map (responses) and dilated stimulations as well (samples)
    map_responses_weighted = (map_responses / MEP_ps_max) * 100 
    ### map_samples_normalized = (map_samples / MEP_ps_max) * 100 #i don't think is used anywhere?
    # normalizing heatmap so that all subjects will be on a scale of 0 / 100. 
    map_heatmap_ps_weighted = (map_heatmap_ps_initial / MEP_ps_smoothed) * 100
    
    return MEP_ps_max, map_responses_weighted, map_heatmap_ps_weighted

def save_map(filename, map, structural_data):
    
    nifti = nib.Nifti1Image(map, structural_data.affine)
    # if not os.path.exists(filename):
    # logging.info('...saving :'+filename)
    nib.save(nifti, filename)

def mask_heatmap(input_map, brainmask, output_file):
    # requires image map to mask, full path to brainmask, and the name of the output file to save
    apply_mask = fsl.ApplyMask()
    apply_mask.inputs.in_file = input_map
    apply_mask.inputs.mask_file = brainmask
    apply_mask.inputs.out_file = output_file
    mask_result = apply_mask.run()
    
def file_cleanup(file_heatmap_ps_initial, file_heatmap_ps_weighted, save_dir, stim_file):
    # ~~~~~~CLEAN UP UNNECESSARY FILES~~~~~~
    os.remove(file_heatmap_ps_initial)
    os.remove(file_heatmap_ps_weighted)
    #os.remove(os.path.join(save_dir,tag+'_FLIRT_omat.mat'))
    if os.path.isfile(os.path.join(save_dir,stim_file+'_heatmap_flirt.mat')):
        os.remove(os.path.join(save_dir,stim_file+'_heatmap_flirt.mat'))
        # os.remove(file_heatmap_sd)

if __name__ == '__main__':
    main()
    

