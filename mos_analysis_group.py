#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:25:09 2021

@author: Bryce

--- deSCRIPTION ---


"""

import os, logging
import numpy as np
from scipy import ndimage as ndi
from nipype.interfaces import fsl
import nibabel as nib
from nibabel.affines import apply_affine
from scipy.spatial import distance
import pandas as pd

import mos_load_data_multi_muscle

parent_logger = logging.getLogger('main')

def main(data_dict, config_dict):
    
    file_atlas = str(config_dict['atlas'])
    save_dir_parent = data_dict['save_dir']
    save_dir_group = save_dir_parent+'/Group_analysis/'
    os.makedirs(save_dir_group,exist_ok=True)
    
    # heatmap list = a list of all subjects who have muscle+'_warped_heatmap' in their outputs folder
    muscle_heatmap_dict = construct_heatmap_list(data_dict, save_dir_parent)
    output_spreadsheet = list()
    #heatmap_list = heatmap_data[0]
    
    for key in muscle_heatmap_dict: # heatmap_dict has keys for each muscle name found in the stim spreadsheet
                                    # and each key points to a list of all subject heatmaps for that muscle
                                    # [0] = subject tag, [1] = path to subject's muscle heatmap
        
        if len(muscle_heatmap_dict[key]) <= 1:
            parent_logger.error('0 or 1 heatmaps found in standard space, cannot produce an averaged heatmap.')
        else:
            parent_logger.info('Producing mean heatmap for '+key+', '+str(len(muscle_heatmap_dict[key]))+' heatmaps found in subject output directories.')
        
            # key is the muscle name.
            heatmap_concatenated = os.path.join(save_dir_group, key+'_heatmaps_concatenated.nii.gz')
            heatmap_group_average = os.path.join(save_dir_group, key+'_heatmaps_averaged.nii.gz')
        
            if not os.path.isfile(heatmap_concatenated) and not os.path.isfile(heatmap_group_average):
                parent_logger.info('Concatenating warped maps and producing an average '+key+' map')
                merge_and_mean(muscle_heatmap_dict[key], heatmap_concatenated, heatmap_group_average)
            else:
                parent_logger.info('Concatenated and averaged heatmaps for '+key+' already produced')

            #simple, load in averaged heatmap and use numpy / scipy methods to calculate these metrics
            parent_logger.info('Calculating average '+key+' map hotspot and center of mass')
            averaged_metrics = calculate_group_average_metrics(heatmap_group_average, file_atlas)
            average_hotspot = averaged_metrics[0]
            average_com = averaged_metrics[1]
        
        # # distance between each subject and average hotspot
        # parent_logger.debug('hotspot located at x: '+average_hotspot[0]+', y: '+average_hotspot[1]+', z: '+average_hotspot[2])
        # parent_logger.debug(' center of mass located at x: '+average_com[0]+', y: '+average_com[1]+', z: '+average_com[2])    

            # Calculate distance from each heatmap to group average heatmap hotspot + COM
            parent_logger.info('Calculating euclidean distance from patient '+key+' hotspot/COM to group average '+key+' hotspot/COM')
            distance_metrics = distance_to_average(muscle_heatmap_dict[key], average_hotspot, average_com, file_atlas)

            # Save these values to an excel sheet?
            store_info(key, muscle_heatmap_dict[key], distance_metrics, average_hotspot, average_com, output_spreadsheet)

    parent_logger.info('Saving groupwise results in Group_analysis subfolder')
    print_spreadsheet(save_dir_group, output_spreadsheet)
    parent_logger.info('MOSAICS group analysis completed!')

def construct_heatmap_list(data_dict, save_dir_parent):
       
    # data_list is a list of subjects with nifti and xls files in a data directory
    data_list = data_dict['data list']
    
    muscle_heatmap_dict = dict()
    
    for subject in data_list:
        
        tag = subject[0]
        file_nibs_map = os.path.join(data_dict['data folder'],subject[2]) #subject[2] is stim file name (in data folder)
        
        save_dir = save_dir_parent+'/'+tag
        
        stim_dict = mos_load_data_multi_muscle.main(file_nibs_map)
        muscles_dict = stim_dict['muscles']

        for muscle in muscles_dict:
            # if the list for this muscle's heatmap doesn't exist yet, create the list
            try:
                muscle_heatmap_dict[muscle]
            except KeyError:
                muscle_heatmap_dict[muscle] = list()

            file_heatmap_sd = os.path.join(save_dir,tag+'_'+muscle+'_warped_heatmap.nii.gz')
            if os.path.exists(file_heatmap_sd):
                muscle_heatmap_dict[muscle].append([tag, file_heatmap_sd])
            
    return muscle_heatmap_dict
    
def merge_and_mean(muscle_heatmaps, heatmap_concatenated, heatmap_group_average):

    heatmap_list = list()
    # heatmap_list is a list with two values per entry, first is the tag and
    # second is the location of a warped heatmap for the muscle for that subject
    for list_entry in muscle_heatmaps:
        heatmap_list.append(list_entry[1])
        
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

def distance_to_average(muscle_heatmaps, average_hotspot, average_com, file_atlas):
    
    heatmap_list = list()
    # heatmap_list is a list with two values per entry, first is the tag and
    # second is the location of a warped heatmap for the muscle for that subject
    for list_entry in muscle_heatmaps:
        heatmap_list.append(list_entry[1])
    
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

def store_info(muscle, muscle_heatmaps, distance_metrics, average_hotspot, average_com, output_spreadsheet):
    
    heatmap_list = list()
    heatmap_tags = list()
    # heatmap_list is a list with two values per entry, first is the tag and
    # second is the location of a warped heatmap for the muscle for that subject
    for list_entry in muscle_heatmaps:
        heatmap_tags.append(list_entry[0])
        heatmap_list.append(list_entry[1])
        
    # ADDING DATA TO A DATAFRAME FOR LATER EXPORT TO SPREADSHEET
    # For column order, see print_spreadsheet function below   
    
    # If this is the first time we're adding to the list or first time adding
    # data for a muscle, add the group-average data also
    if output_spreadsheet == [] or output_spreadsheet[-1][0] != muscle:
        output_spreadsheet.append([muscle,
                                   'Mean group map',
                                    round(average_hotspot[0][0],0),
                                    round(average_hotspot[0][1],0),
                                    round(average_hotspot[0][2],0),
                                    round(average_com[0][0],2),
                                    round(average_com[0][1],2),
                                    round(average_com[0][2],2),
                                    0,
                                    0])
    
    # if len(output_spreadsheet) == 0:
    #     output_spreadsheet.append([muscle,
    #                                'Mean group map',
    #                                 round(average_hotspot[0][0],0),
    #                                 round(average_hotspot[0][1],0),
    #                                 round(average_hotspot[0][2],0),
    #                                 round(average_com[0][0],2),
    #                                 round(average_com[0][1],2),
    #                                 round(average_com[0][2],2),
    #                                 0,
    #                                 0])
    
    for index in range(0,len(heatmap_list)):
        
        measures_list = [muscle,
                         heatmap_tags[index],
                         distance_metrics[index][0][0][0],
                         distance_metrics[index][0][0][1],
                         distance_metrics[index][0][0][2],
                         round(distance_metrics[index][1][0][0],2),
                         round(distance_metrics[index][1][0][1],2),
                         round(distance_metrics[index][1][0][2],2),                         
                         round(distance_metrics[index][2],2),
                         round(distance_metrics[index][3],2)]
        output_spreadsheet.append(measures_list)

def print_spreadsheet(save_dir_group, output_spreadsheet):
    
    results_column_names = ['Muscle',
                            'Subject',
                            'Hotspot X',
                            'Hotspot Y',
                            'Hotspot Z',
                            'COM X',
                            'COM Y',
                            'COM Z',
                            'Dist. to group hotspot',
                            'Dist. to group COM']
    
    # ~~~~~~print values to spreadsheet after the loop has completed~~~~~~
    metrics_dataframe = pd.DataFrame(output_spreadsheet, columns=results_column_names)    
    measures_file = os.path.join(save_dir_group,'cohort_mapping_results.xlsx')
    metrics_dataframe.to_excel(measures_file)

if __name__ == "__main__":
    main()