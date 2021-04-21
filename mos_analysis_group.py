#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:25:09 2021

@author: Bryce

--- deSCRIPTION ---

1. Get a list of all the people to process              - CHECK
2. Fslmaths to mean all heatmaps (in standard space)    - CHECK
    - Heatmaps have to be in standard space             - CHECK
3. Calculate hotspot and COM                            - CHECK
4. Calculate distance to hotspot for each individual    - CHECK
5. Save this information                                - 
    - put it in a 'group' subfolder within '/outputs'

"""

import os, logging
import numpy as np
from scipy import ndimage as ndi
from nipype.interfaces import fsl
import nibabel as nib
from nibabel.affines import apply_affine
from scipy.spatial import distance
import pandas as pd

parent_logger = logging.getLogger('main')

def main(data_dict, config_dict):
    
    save_dir_parent = data_dict['save_dir']
    file_atlas = str(config_dict['atlas'])
    
    # heatmap list = a list of all subjects who have '_warped_heatmap' in their outputs folder
    heatmap_data = construct_heatmap_list(data_dict)
    heatmap_list = heatmap_data[0]
    heatmap_tags = heatmap_data[1]
    
    if len(heatmap_list) <= 1:
        parent_logger.error('...0 or 1 heatmaps found in standard space, cannot perform group-wide analysis')
    else:
        
        parent_logger.info('...MOSAICS group-wide analysis beginning, please wait.')
        
        # First, make a subfolder to save our group analysis results in
        save_dir_group = save_dir_parent+'/Group_analysis/'
        os.makedirs(save_dir_group,exist_ok=True)
        
        heatmap_concatenated = os.path.join(save_dir_group, 'group_heatmaps_concatenated.nii.gz')
        heatmap_group_average = os.path.join(save_dir_group,'group_heatmaps_averaged.nii.gz')
        
        # creates the two images listed directly above using Nipype FSL commands
        parent_logger.info('...concatenating standard space heatmaps, and creating the group average map')
        merge_and_mean(heatmap_list, heatmap_concatenated, heatmap_group_average)

        #simple, load in averaged heatmap and use numpy / scipy methods to calculate these metrics
        parent_logger.info('...calculating average map hotspot and center of mass')
        averaged_metrics = calculate_group_average_metrics(heatmap_group_average, file_atlas)
        average_hotspot = averaged_metrics[0]
        average_com = averaged_metrics[1]
        
        # # distance between each subject and average hotspot

        # parent_logger.info('...hotspot located at x: '+hotspot[0]+', y: '+hotspot[1]+', z: '+hotspot[2])
        # parent_logger.fino('... center of mass located at x: '+com[0]+', y: '+com[1]+', z: '+com[2])    
    
        # Calculate distance from each heatmap to group average heatmap hotspot + COM
        parent_logger.info('...calculating distance from patient hotspot/COM to group average hotspot/COM')
        distance_metrics = distance_to_average(heatmap_list, average_hotspot, average_com, file_atlas)
        
        # Save these values to an excel sheet?
        parent_logger.info('...saving results spreadsheet in Group_analysis subfolder')
        save_info(heatmap_list, heatmap_tags, distance_metrics, average_hotspot, average_com, save_dir_group)

        parent_logger.info('...MOSAICS group analysis completed!')

def construct_heatmap_list(data_dict):
    
    heatmap_list = list()
    heatmap_tags = list()
    
    # data_list is a list of subejcts with nifti and xls files in a data directory
    data_list = data_dict['data list']
    
    for subject in data_list:
        
        # tag = subject[0]
        stim_file = subject[1]
        #save directory, including sub-directory for each subject
        save_dir = str(data_dict['save_dir']+'/'+stim_file)
        
        file_heatmap_sd = os.path.join(save_dir,stim_file+'_warped_heatmap.nii.gz')
        if os.path.exists(file_heatmap_sd):
            heatmap_list.append(file_heatmap_sd)
            heatmap_tags.append(stim_file)
            
    return heatmap_list, heatmap_tags
    
def merge_and_mean(heatmap_list, heatmap_concatenated, heatmap_group_average):

    merge_heatmaps = fsl.Merge()
    merge_heatmaps.inputs.in_files = heatmap_list
    merge_heatmaps.inputs.dimension = 't'
    merge_heatmaps.inputs.merged_file = heatmap_concatenated
    merge_heatmaps.inputs.output_type = 'NIFTI_GZ'
    # parent_logger.critical(merge_heatmaps.cmdline)
    merge_results = merge_heatmaps.run()
    
    mean_heatmap = fsl.MeanImage()
    mean_heatmap.inputs.in_file = heatmap_concatenated
    mean_heatmap.inputs.dimension = 'T'
    mean_heatmap.inputs.out_file = heatmap_group_average
    mean_heatmap.inputs.output_type = 'NIFTI_GZ'
    # parent_logger.critical(mean_heatmap.cmdline)
    mean_result = mean_heatmap.run()

def calculate_group_average_metrics(heatmap_group_average, file_atlas):
    
    # ~~~~~~CALCULATE METRICS (group average map)~~~~~~
    
    # load back in masked heatmap to calculate metrics
    averaged_heatmap = nib.load(heatmap_group_average).get_fdata()        
    
    # HOTSPOT:
    # raw MEP from the stim data, and smoothed (post-Gaussian filter), needed to normalize patient heatmap
    average_hotspot = np.unravel_index(np.argmax(averaged_heatmap), averaged_heatmap.shape)
    
    # CENTER OF MASS:
    # convenient method from scipy / ndimage (imported as ndi)
    average_center_mass = ndi.measurements.center_of_mass(averaged_heatmap)
    
    # -- Convert standard space hotspot / COM from voxel coordinates to SD anatomical coords (mm)
    atlas_affine = nib.load(file_atlas)
    atlas_affine = atlas_affine.affine
    ## Hotspot
    average_hotspot = apply_affine(atlas_affine, average_hotspot)
    ## COM
    average_center_mass = apply_affine(atlas_affine, average_center_mass)

    return average_hotspot, average_center_mass

def distance_to_average(heatmap_list, average_hotspot, average_com, file_atlas):
    
    distance_metrics = list()
    
    atlas_affine = nib.load(file_atlas)
    atlas_affine = atlas_affine.affine
    
    for index in range(0,len(heatmap_list)):
        
        subject_heatmap = nib.load(heatmap_list[index]).get_fdata()
        # calculate subject hotspot
        subject_hotspot = np.unravel_index(np.argmax(subject_heatmap), subject_heatmap.shape)
        
        # calculate subject com
        subject_com = ndi.measurements.center_of_mass(subject_heatmap)
        
        # -- Convert standard space hotspot / COM from voxel coordinates to SD anatomical coords (mm)
        ## Hotspot
        subject_hotspot = apply_affine(atlas_affine, subject_hotspot)
        ## COM
        subject_com = apply_affine(atlas_affine, subject_com)
        
        # convert subject hotspot and com to arrays of the right dimensions for use by scipy
        subject_hotspot_array = np.asarray(subject_hotspot)
        subject_hotspot_array.shape = (1,3)
        subject_com_array = np.asarray(subject_com)
        subject_com_array.shape = (1,3)
        
        # do the same for average hotspot and com
        average_hotspot_array = np.asarray(average_hotspot)
        average_hotspot_array.shape = (1,3)
        average_com_array = np.asarray(average_com)
        average_com_array.shape = (1,3)
        
        # calculate hotspot distance
        # [0][0] added below to pull the value itself out of the array it's in
        hotspot_distance = distance.cdist(average_hotspot_array, subject_hotspot_array)[0][0]
        
        # calculate com distance
        com_distance = distance.cdist(average_com_array, subject_com_array)[0][0]
        
        # append these two values to a list or tuple
        distance_metrics.append([subject_hotspot, subject_com, hotspot_distance, com_distance])
        
    # return the tuple
    return distance_metrics

def save_info(heatmap_list, heatmap_tags, distance_metrics, average_hotspot, average_com, save_dir_group):
    
    results_column_names = ['Subject tag',
                            'Hotspot X',
                            'Hotspot Y',
                            'Hotspot Z',
                            'COM X',
                            'COM Y',
                            'COM Z',
                            'Dist. to group hotspot',
                            'Dist. to group COM']
    
    results_metrics_list = list()
    results_metrics_list.append(['Mean group map',
                                round(average_hotspot[0][0],0),
                                round(average_hotspot[0][1],0),
                                round(average_hotspot[0][2],0),
                                round(average_com[0][0],2),
                                round(average_com[0][1],2),
                                round(average_com[0][2],2),
                                0,
                                0])
    
    for index in range(0,len(heatmap_list)):
        
        measures_list = [heatmap_tags[index],
                         distance_metrics[index][0][0][0],
                         distance_metrics[index][0][0][1],
                         distance_metrics[index][0][0][2],
                         round(distance_metrics[index][1][0][0],2),
                         round(distance_metrics[index][1][0][1],2),
                         round(distance_metrics[index][1][0][2],2),                         
                         round(distance_metrics[index][2],2),
                         round(distance_metrics[index][3],2)]
        results_metrics_list.append(measures_list)

    # ~~~~~~print values to spreadsheet after the loop has completed~~~~~~
    metrics_dataframe = pd.DataFrame(results_metrics_list, columns=results_column_names)    
    measures_file = os.path.join(save_dir_group,'cohort_mapping_results.xlsx')
    metrics_dataframe.to_excel(measures_file)

if __name__ == "__main__":
    main()