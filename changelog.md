# 04_mosaics_2020

0.1.2 (2021-03-22)
------------------

New
~~~
- Started this changelog!
- Added function to search for MOSAICS brainmask in both the save directory or the data directory.
A user provided brainmask is still only found if in the data directory.
- Mapping results in standard space (typically MNI) are now reported in anatomical / world coordinates
rather than voxel coordinates (affine matrix applied to voxel coordinates)
- Stimulation dilation is now performed using fslmaths (sphere kernel) rather than voxel-wise approach

Changes
~~~~~~~
- Refactored main analysis code for ease of readability / efficiency
- Limited variable declarations as much as possible to mos_main.py
- Changed 'flip stimulation coordinates' box to a selection dialogue of either
'Brainsight' or 'Nifti' 
- Added coniguration settings to mapping results spreadsheet
- Logging messages in terminal have been calmed down (no more exclamation points)
- Terminal logging messages have had an empty space added between participants for readability
- Outputs changed to .nii.gz rather than .nii to preserve space

Fix
~~~
- MOSAICS will not run if no data is found for processing in the data folder
- Data list is double-checked when data selection GUI is closed to account for changed filenames
- GUI buttons have been made uniform and justified
