#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:25:09 2021

@author: Bryce

--- deSCRIPTION ---
"""

import pandas as pd
import numpy as np
import logging

parent_logger = logging.getLogger('main')

def main(file_nibs_map):

    # Load in NIBS data spreadsheet
    data_nibs_map = pd.read_excel(file_nibs_map)
    
    # Limit further analysis to just the first chunk of stimulation data
    # (i.e. all columns must have the same number of rows
    # Note that this assumes that the bottom chunk of these files has less columns
    # than the actual stimulation data (above)
    data_nibs_map = data_nibs_map.dropna()
    
    # Parse the entered spreadsheet data for the information that we need
    ## Simply: loop through the column names, if 'MEP' is anywhere in the name,
    ## that's an MEP and we look for a corresponding responsive column. If not,
    ## check if this could be one of our location columns, X, Y or Z
    
    muscles_dict = dict()
    locs_dict = dict()
    
    for column in data_nibs_map.columns:
        
        # If this column name has MEP in it, store it and skip the rest
        if 'MEP' in column:
            
            # MUSCLE NAME -- find name of the muscle
            # first, delete '_MEP' or 'MEP_' from the name
            if 'MEP_' in column:
                muscle_name = column.replace('MEP_','')
            elif '_MEP' in column:
                muscle_name = column.replace('_MEP','')
            else:
                muscle_name = column.replace('MEP','')
                
            # MEP COLUMN -- pull the MEP data from the column
            MEP_column = data_nibs_map[column]
                
            # RESPONSIVE COLUMN -- pull or construct (see else: )
            if muscle_name+'_responsive' in data_nibs_map.columns:
                # responsive_colname = muscle_name+'_responsive'
                responsive_column = data_nibs_map[muscle_name+'_responsive']
            elif 'responsive_'+muscle_name in data_nibs_map.columns:
                # responsive_colname = 'responsive_'+muscle_name
                responsive_column = data_nibs_map['responsive_'+muscle_name]
            else:
                # build a column of responsive or not
                # start with all zeroes
                responsive_column = np.zeros(len(MEP_column))
                # for each stimulated point, if the MEP is not zero, responsiveness column is 1
                for count, value in enumerate(responsive_column):
                    if value != 0:
                        responsive_column[count] = 1        
            
            # order = muscle name, MEP column name, MEP responsive column)
            muscles_dict[muscle_name] = [MEP_column, responsive_column]
            continue
        
        # Fill the dict for location data with the correct column names
        # Find X
        if column=='X' or column=='Loc. X':
            locs_dict['X'] = data_nibs_map[column]
        # Find Y
        if column=='Y' or column=='Loc. Y':
            locs_dict['Y'] = data_nibs_map[column]
        # Find Z
        if column=='Z' or column=='Loc. Z':
            locs_dict['Z'] = data_nibs_map[column]
    
    #check for errors:
    
    ## do all stims have 3 data points?
    error_check = 0
    if len(locs_dict['X']) == len(locs_dict['Y']) == len(locs_dict['Z']):
        
        # first error check good, proceed to second error check
        ## do all MEP columns have a data point for each stim point?
        for muscle in muscles_dict:
            if len(muscles_dict[muscle][0]) == len(locs_dict['X']):
                pass
            else:
                parent_logger.error('...'+muscle+' MEP column length does not match stimulation coordinate column length')
                error_check = 1
    else:
        parent_logger.error('...X, Y, and Z stimulation coordinate columns do not have the same amount of data points')
        error_check = 1
        
    if error_check == 0:
        # Second error check good, too. Output a logging message so we know how many muscles we'll be processing
        parent_logger.info('...Found data for '+str(len(muscles_dict))+' to process')
        parent_logger.info('...'+str(len(locs_dict['X']))+' stimulation coordinate sets found')

        # Pass this list back to the main script?
        stim_dict = dict()
        stim_dict['locs'] = locs_dict
        stim_dict['muscles'] = muscles_dict
        return stim_dict

if __name__ == "__main__":
    main()
