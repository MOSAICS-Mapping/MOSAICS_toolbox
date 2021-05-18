#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:25:09 2021

@author: Bryce

--- deSCRIPTion ---

FUNCTION:
    When user selects a file or folder in the guiSelect menu, this function runs to construct
    a list of subject or subjects to process, referenced by other scripts

RELEVANT VARS:
    data_dict vals used here:
        'data': the selected folder the user picks, full of data to process
    data_dict vals CREATED here:
        'data list': list of all subjects with nii and xls to process
    

"""

import os
import re
import glob
import logging

parent_logger = logging.getLogger('main')

def main(data_dict, config_dict):
    
    # initialize variables from input dicts
    data_dir = data_dict['data folder']
    
    # initialize empty list that will be filled here
    data_dict['data list'] = list()
        
    # initialize regular expression to check whether filenames are valid
    # i.e. contain only alphanumeric characters, hyphens, and underscores
    valid_regex = re.compile(r'^[A-Za-z0-9._-]+$')
    valid_nii_regex = re.compile(r'^([A-Za-z0-9_-]+)(.nii|.nii.gz)$')
    valid_xl_regex = re.compile(r'^([A-Za-z0-9_-]+)(.xls|.xlsx)$')

    # find all nii or nii.gz datasets
    datasets = glob.glob(os.path.join(data_dict['data folder'],'*.nii*')) #returns a list, possibly too inclusive but hopefully not
    # separate filename from full path (including parent folderz)
    datasets = [os.path.basename(x) for x in datasets]
    
    for nii in datasets:
        # check if filename has alphanumerics, underscores, hyphens, and ends with .nii or .nii.gz
        nii_match = valid_nii_regex.search(nii)
        #if we find a match
        if nii_match != None:
            # tag = everything before the dot
            tag = nii_match.group(1)
            # find all xls or xlsx files that match the tag
            stim_list = glob.glob(os.path.join(data_dir,tag+'*.xls*'))
            stim_list = [os.path.basename(x) for x in stim_list]
            if stim_list != []:
                for stim_data in stim_list:
                    # probably unnecessary: check if xls* file has only alphanumeric, _, or -
                    stim_match = valid_xl_regex.search(stim_data)
                    if stim_match != None:
                        # if we have valid nii and xl files, append the info of this pair to a data processing list
                        data_dict['data list'].append([tag, nii_match.string, stim_match.string])
                        parent_logger.debug(''+nii_match.string+', '+stim_match.string+' are a matched pair. Added to processing list')
                    else:
                        parent_logger.debug(''+str(stim_data)+' name invalid, must contain only A-Z, 0-9, _, and -')
            else:
                parent_logger.debug('no stimulation data found that matches '+nii_match.string+', moving on')
        else:
            parent_logger.debug(''+str(nii)+' name invalid, must contain only A-Z, 0-9, _, and -')
    
    return data_dict['data list']
    
    # return list of subjects to process
    # this final step is already done because data_dict['data list'] has been constructed
    
if __name__ == '__main__':
    main()