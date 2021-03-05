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

import glob
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(data_dict, config_dict):
    
    # initialize empty list that will be filled here
    data_dict['data list'] = list()
        
    # find all nii or nii.gz datasets
    datasets = glob.glob(data_dict['data folder']+'/*.nii*') #returns a list, possibly too inclusive but hopefully not
    
    # pull everything before the first dot to find the tag for each subject
    tags = [os.path.basename(x) for x in datasets]
    tags = [x.split('.')[0] for x in tags]    
    
    # add each subject with a nifti and excel spreadsheet to a list for further
    # processing
    data_dict['data list'] = list()
    for tag in tags:
        if glob.glob(os.path.join(data_dict['data folder'],tag,'.xls*')) != []:
            stimulation = glob.glob(os.path.join(data_dict['data folder'],tag,'.xls*'))[0]
            structural = glob.glob(os.path.join(data_dict['data folder'],tag,'.nii*'))[0]
            data_dict['data list'].append([tag,structural, stimulation])
    
    return data_dict['data list']
    
    # return list of subjects to process
    # this final step is already done because data_dict['data list'] has been constructed
    
if __name__ == '__main__':
    main()