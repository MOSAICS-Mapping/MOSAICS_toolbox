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
Notes as I'm reading through the script

SPM is called, what function does this perform?

extra functions list, outsource to their own scripts hey?
    skullstrip
    warp to MNI

script steps below with their own comment headers for organization purposes
"""

##### Keeping track of variables that could be passed into this function #####
# SubjectID, file_t1, 

##### Script initialization section #####
import os
import nibabel as nib
import pandas as pd
import numpy as np
from scipy import ndimage as ndi
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

"""
    - get subject ID from somewhere (ideally in GUI)
        - this is just used to save files with the right name
        - outsource to 'Save' function / script
        
    Below section is now for variables to be passed to this script from elsewhere, currently hard-coded for development
"""
logging.critical('SAMPLE DATA DIR BELOW THIS LINE IS HARD CODED, ALONG WITH OTHER VARS')
sample_data_dir = '/Users/Bryce/Desktop/Postdoc_Projects/3_MULTIMODAL_HOTSPOTS/MOSAICS/MOSAICS_Python/Main_automated_run/'
os.chdir(sample_data_dir)
file_t1 = 'LCT1.nii'
file_nibs_map = '3001data.xlsx'
dilate = 5 # must be odd
smooth = 7 # from spm, we'll calculate standard deviation from this FWHM scalar (used by SPM)
MEP_thresh = 0

"""
    - read in a 1mm isotropic T1-weighted MRI .nii
        - key lines:
            header = spm_vol(T1image);
            brain = spm_read_vols(header)
        - translation:
            spm_vol is a structure characterizing an object, has name, is not the image itself
            spm_read_vols brings in the data from the nifti file into the brain variable
        - local implementation:
            nibabel's load_nii, perhaps?
"""
data_T1 = nib.load(file_t1)
# array shape = img_T1.shape
# actual data = img_T1.get_fdata()
# header = img_T1.header

"""
    - read the Brainsight coordindates file
    - should be four columns. X, Y, Z, and the corresponding MEP amplitude for that location
        - key lines:
            BSfile = uigetfile('*.xls*', 'Select the Brainsight coordiante file')
            inputdata = xlsread(BSfile);
            x = round(inputdata(:,1));
            y = round(inputdata(:,2));
            z = round(inputdata(:,3));
            m = inputdata(:,4);
            numLocs = size(x);
        - local implementation:
                    
        - development notes:
            - write code to read excel file with and without header
"""
data_nibs_map = pd.read_excel(file_nibs_map,header=None)
data_nibs_map[0] = round(data_nibs_map[0])
data_nibs_map[1] = round(data_nibs_map[1])
data_nibs_map[2] = round(data_nibs_map[2])

# This is how Helen did it, I figure if we keep this as a 4xn array then it will be easier to use in future loops
# Mostly so that we don't need to have a separate index variable, the coordinates of the mep are tied to the mep
# x = round(data_nibs_map[0])
# y = round(data_nibs_map[1])
# z = round(data_nibs_map[2])
# mep = data_nibs_map[3]

num_locs = data_nibs_map[0].shape[0]

"""
    - Generate patient-space maps of TMS experiment
        - create an arrays of zeroes of equal size to our T1 image (brain) for our output images
            - key lines:
                overlay=   zeros(size(brain));
                samples=   zeros(size(brain));
                dotmap=    zeros(size(brain));
                grid=      zeros(size(brain));
        - replace zeroes at locations of TMS stim with MEP amplitudes at that location, also replace
        0s with 99s in the grid map, for visualization purposes (essentially a binary map, stim or no).  

    What are these maps?
    - Overlay = MEP amplitude overlayed in an array the same size as the T1 image, dilated across 5 voxels
    (so 5mm isotropic) in the script
        renamed to map_stims
    - Dotmap = the same as overlay, but 3mm dilation instead of 5mm
        renamed to map_samples
    - Samples = the same as overlay but no dilation, so 1mm isotropic
        renamed to map_dots
    - Grid = 'binary' mask, 0 or 99, which points had a stim? But also points orthogonally adjacent
    to each stim point are 1 instead of 99, interestingly.
        renamed to map_grid
    
"""
# Create an array of zeroes equal to size of T1 image, to initialize our output images
map_stims = np.zeros(data_T1.shape)
map_samples = np.zeros(data_T1.shape)
map_dots = np.zeros(data_T1.shape)
map_grid = np.zeros(data_T1.shape)

# Put all MEP values in to the arrays of zeroes at their corresponding x,y,z coordinates
# index variable has a name (eg. 134) and dtype (eg. float64)
# row variable has all variables in the row, 0 = x, 1 = y, 2 = z, 3 = mep amplitude
for index, row in data_nibs_map.iterrows():
    map_stims[int(row[0]),int(row[1]),int(row[2])] = row[3]
    map_samples[int(row[0]),int(row[1]),int(row[2])] = row[3]
    map_dots[int(row[0]),int(row[1]),int(row[2])] = row[3]
    map_grid[int(row[0]),int(row[1]),int(row[2])] = 1
    
"""
    - Dilate voxels of TMS stimulation to cover more of the T1 image, so instead of a TMS MEP overlayed over a 1mm
    voxel, it's dilated to cover 5x5x5mm of voxels
        - key lines:
            3-nested loop
            it works by moving up across 5 slices, and filling a 5x5 grid of x and y voxels
            with the same MEP amplitude
        - local implementation:
            there's got to be a better way in NumPy perhaps?
            ??? Look into how to repeat values in an array, a specified number of times
            ??? Got to make sure, if I do this, that borders between MEPs are maintained, no values are overwritten
                if the dilation is too large.
    
    Development Notes:
        dilation solutions:
            - multi-dimensional index like: test_big[0:3,0:3,0:3] = test_unit
            - convolve a 3d function in some way, perhaps? I see 2d solutions but not 3d
        include a condition to check if any of the values we're going to replace are currently non-zero (meaning some
        dilated values are overlapping)'
        
    
"""
dilate_offset = (dilate-1)/2
         
# for all rows with nonzero MEPs, duplicate their values over the neighbouring region, the number
# of times the value is replicated is determined by the dilate variable, which must be odd.
for row in np.where(data_nibs_map[3] > 0)[0]:
    x_lower = int(data_nibs_map[0][row]) - int(dilate_offset)
    x_higher = int(data_nibs_map[0][row]) + int(dilate_offset) + 1
    y_lower = int(data_nibs_map[1][row]) - int(dilate_offset)
    y_higher = int(data_nibs_map[1][row]) + int(dilate_offset) + 1
    z_lower = int(data_nibs_map[2][row]) - int(dilate_offset)
    z_higher = int(data_nibs_map[2][row]) + int(dilate_offset) + 1
    map_stims[x_lower:x_higher,y_lower:y_higher,z_lower:z_higher] = data_nibs_map[3][row]
            
"""
    - Rotate matrices in the y dimension (AP) to convert from RPS (Brainsight) to RAS (Nifti)
        RPS = +x is right, +y is posterior, +z is superior
        RAS = +x is right, +y is anterior, +z is superior
        - key lines:
            overlay =   flip(overlay,2);
            samples =   flip(samples,2);
            dotmap =    flip(dotmap,2);
            grid =      flip(grid,2);     
        - flip 0 = flip L and R, flip 2 = flip up and down, flip 1 = flip back and front
"""
map_stims = np.flip(map_stims,1)
map_samples = np.flip(map_samples,1)
# dotmap = np.flip(dotmap,1)
# grid = np.flip(grid,1)

"""
    - Save output files as niftis
        - key lines:
            save output = overlay as SID_Hotspots.nii
            save output = samples as SID_Samples.nii
            save output = dotmap as SID_DotMap.nii
            save output = grid as SID_GridLoc.nii
            spm_write_vol(header,output); end
        - local implementation:
            add the filenames and their corresponding arrays to be saved into a dict,
            cycle through the dict to save it all
"""
# Nibabel save nifti only needs the image data and an affine, which we'll re-use from the T1 image
file_hotspot = 'LCT1_Python_stimulations.nii'
nii_hotspot = nib.Nifti1Image(map_stims, data_T1.affine)
if not os.path.exists(file_hotspot):
    logging.info('...saving hotspots!')
    nib.save(nii_hotspot, file_hotspot)

"""
    - Smooth the hotspot map (5mm dilated overlay variable) using a 3D Gaussian
        - key lines:
            spm_smooth('SIDHotspots.nii','SID_Heatmap.nii',smooth,0)
            smooth set to 7 in config zone of script
            0 means output same datatype as input (.nii)
        - local implementation:
            ??? What's the best way to smooth an image in Python'
            ??? Can we constrict smoothing to only one z slice, or just mask out non-brain voxels?
            we can smooth using scipy.ndimage.gaussian_filter
                > BUT we specify the standard deviation of the gaussian isntead of it's full width at
                half maximum (FWHM) like SPM does
                > Interestingly, FWHM = 2.355 * s.d. for normal distribution (Gaussian),
                according to wikipedia and other sources
"""
stdev_gaussian = smooth/2.355
map_heatmap = ndi.gaussian_filter(map_stims,stdev_gaussian,0,mode='reflect')
file_heatmap = 'LCT1_Python_heatmap.nii'
nii_heatmap = nib.Nifti1Image(map_heatmap, data_T1.affine)
if not os.path.exists(file_heatmap):
    logging.info('...saving heatmap!')
    nib.save(nii_heatmap, file_heatmap)

"""
    - Calculate patient hotspot in patient space
        - key lines:
            [hs_MEP,hs_IDX] = max(samples(:));
            [hs_X,hs_Y,hs_Z]= ind2sub(size(samples),hs_IDX);
                ind2sub converts from linear indexing, which is apparently being used? to find the
                x, y, and z coordinates of the maximum MEP. Maybe the max() function returns linear
                indices
            shipped away to mos_writeoutputfiles() function to output Results.xlsx
        - local implementation:
            numpy.argmax to get a linear index for the maximum value in the samples array,
            then numpy.unravel_index to get the 3D index from that linear index
"""
results_hotspot = np.unravel_index(np.argmax(map_samples), map_samples.shape)

"""
    - Calculate patient space center of gravity of map
        - key lines:
            [rowsub, colsub, pagsub] = ind2sub(size(samples),find(samples>MEP_thresh));
            grid = round([rowsub, colsub, pagsub]);
            grid(:,4) = samples(find(samples>MEP_thresh)); 
            cog_x = round((sum(grid(:,1).*grid(:,4)))/sum(grid(:,4)));
            cog_y = round((sum(grid(:,2).*grid(:,4)))/sum(grid(:,4)));
            cog_z = round((sum(grid(:,3).*grid(:,4)))/sum(grid(:,4)));
        - local implementation:
            ???
"""
results_center_mass = ndi.measurements.center_of_mass(map_samples)

"""
    - Normalize outputs to MNI space
        - key steps (lots of lines to write):
            1. generate deformation field from patient to MNI space using mos_normalise_job.m
                I'm assuming this script has the normalise step in it, afterwards..
            2. if deformation field pre-selected, use mos_normalisewrite_job.m
            3. Load the MNI samples.nii file and calculate the hotspot in MNI space
            4. Convert from matrix coordiantes to MNI mm coordinates using the transformation in the header (see line 299)
            5. Calculate grid locations in MNI space
            6. Calculate COG in MNI space
            7. Save output files
        - local implementation:
            There's a lot here, maybe make it's own script?
"""

from nipype.interfaces import fsl
# set FSLDIR in Spyder, this should be taken care of during installation I guess?
# FSLDIR=/usr/share/fsl
# . ${FSLDIR}/etc/fslconf/fsl.sh
# PATH=${FSLDIR}/bin:${PATH}
# export FSLDIR PATH

logging.critical('FLIRT/FNIRT SETTINGS HARD CODED BELOW. MUST CHANGE!')

# Register T1 image to MNI_152 template using FLIRT and FNIRT
# 1. FLIRT t1 to MNI: works, outputs a mat and nii.gz file:

t1_flirt_mni = fsl.FLIRT()
t1_flirt_mni.inputs.in_file = file_t1
t1_flirt_mni.inputs.reference = sample_data_dir+'MNI152_T1_1mm.nii.gz'
t1_flirt_mni.inputs.out_file = sample_data_dir+'T1_mni_FLIRT_out.nii.gz'
t1_flirt_mni.inputs.out_matrix_file = sample_data_dir+'T1_mni_FLIRT_omat.mat'
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

# t1_flirt_final = fsl.FLIRT()
# # flirt heatmap
# t1_flirt_final.inputs.in_file = sample_data_dir+'LCt1_Python_heatmap.nii'
# t1_flirt_final.inputs.reference = sample_data_dir+'MNI152_T1_1mm.nii.gz'
# t1_flirt_final.apply_xfm = sample_data_dir+'T1_mni_FLIRT_omat.mat'

# OR
heatmap_applyxfm = fsl.preprocess.ApplyXFM()
# heatmap or other measure map
heatmap_applyxfm.inputs.in_file = sample_data_dir+'LCT1_Python_heatmap.nii'
heatmap_applyxfm.inputs.in_matrix_file = sample_data_dir+'T1_mni_FLIRT_omat.mat'
heatmap_applyxfm.inputs.out_file = sample_data_dir+'LCT1_Python_heatmap_w.nii.gz'
heatmap_applyxfm.inputs.reference = sample_data_dir+'MNI152_T1_1mm.nii.gz'
heatmap_applyxfm.inputs.apply_xfm = True
result = heatmap_applyxfm.run()


"""
    - addon: skullstrip
        - uses mos_segment_job.m
"""

# if __name__ == '__main__':
#     main()





# Possibly useful functions to dilate MEP values across the mosaics maps

# def paste_slices(tup):
#   pos, w, max_w = tup
#   wall_min = max(pos, 0)
#   wall_max = min(pos+w, max_w)
#   block_min = -min(pos, 0)
#   block_max = max_w-max(pos+w, max_w)
#   block_max = block_max if block_max != 0 else None
#   return slice(wall_min, wall_max), slice(block_min, block_max)

# def paste(wall, block, loc):
#   loc_zip = zip(loc, block.shape, wall.shape)
#   wall_slices, block_slices = zip(*map(paste_slices, loc_zip))
#   wall[wall_slices] = block[block_slices]