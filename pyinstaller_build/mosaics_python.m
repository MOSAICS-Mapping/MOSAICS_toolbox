%
% mosaics.m 
%
% MOSAICS - Mapping of sensory activation hotspots during cortical
% stimulation 
%
% Author: H Carlson, Calgary Pediatric Stroke Program, Alberta Children's Hospital
% Original: Dec 20, 2016 
% Latest: September 11, 2019
%
% A suite of Matlab scripts designed to calculate and generate
% three-dimensional hotspot maps based on electromyography (EMG) recordings
% during transcranial magnetic brain stimulation (TMS). Maps are overlaid
% on individualized brain anatomy using MRI, can characterize motor
% hotspots as well as changes in motor networks due to neuroplasticity
% after intensive therapy. MOSAICS is also extensible to other sensory
% modalities such as language mapping using TMS virtual lesions. Recent
% updates have added functionality to generalize MOSAICS for use with near
% infrared spectroscopy (fNIRS) data.
%
% MOSAICS may be useful for conversion of motor maps, digitized electrode,
% optode and fiducial locations into standard space (MNI) for group
% comparisons.
%
% Before you start, ensure that the datafile contains applicable
% stimulation coordinates (XYZ) and intensity values in column 4 (i.e.,
% MEPs or language error rates for language mapping).
%
% PREREQUISITES:
% For this script, you will need the following in your Matlab path:
% SPM12: http://www.fil.ion.ucl.ac.uk/spm
% MOSAICS (this folder)
%
% GET STARTED:
% 1. First change your working directory to the directory in which your
% patient files reside (project_folder/patient1).
%
% 2. In this folder, you will be prompted to select a T1-weighted MRI of a
% participant in patient space (i.e., not normalized and not
% skull-stripped). 
%
% 3. A Brainsight output file containing a list of brain surface
% coordinates (XYZ) in the first 3 columns used to stimulate the area of
% interest (i.e., M1). The fourth column should contain corresponding MEP
% amplitudes that resulted from stimulation at the above coordinates or in
% the case of language mapping, picture naming error rates. For fNIRS or
% foducial locations, a large value such as 1000 in every row is
% sufficient.
%
% 4. OPTIONAL: A warp file defining deformation field from patient space to
% MNI space. Only applies if cov2MNI is true. Or you can calculate a new
% one by clicking cancel at the prompt.
%
% OUTPUTS:
% 1. Pt#_GridLoc.nii - All planned grid locations with intensity of 1 (including MEP=0 or not sampled)
% 2. Pt#_Samples.nii - Sampled grid locations weighted by corresponding MEP intensities (1mm isotropic)
% 3. Pt#_Dotmap.nii - Sampled grid locations weighted by corresponding MEP intensities (3mm isotropic)
% 4. Pt#_Hotspots.nii - Sampled grid locations weighted by corresponding MEP intensities (5mm isotropic)
% 5. Pt#_Heatmap.nii - Smoothed hotspot map
% 6. Pt#_Results.xlsx - Hotspot and COG coordinates in SPSS format
% 7. Pt#_GridMNI.xlsx - Grid locations in MNI coordinate space
% 8. Pt#_Grid.xlsx - Grid locations in patient RAS space (converted from LPS)
%
% OPTIONS:
% if conv2MNI is true, output files will also be converted to MNI standard space
% prefixed with a 'w'
%
% UPDATES
% Sep 11, 2019 - Added functionality for fNIRS optode analysis. 

function mosaics_python(SID, T1image, BSfile)

home
%clear all;
spm_jobman('initcfg');

% ************* Set preferences here *************
skullstrip = false;     % true = generate a skull stripped brain (GM+WM) - UNDER DEV
conv2MNI = false;        % true = convert .nii files to MNI standard space
pad_top = false;         % Pad the top of brain matrix by 5 slices of 0s for fNIRS processing
smooth = 7;             % Set isotropic smoothing kernel or give vector (mm)
MEP_thresh = 0;        % Set MEP threshold (mV) for maps
svGridLoc = true;       % Save Pt#_GridLoc.nii
svSamples = true;       % Save Pt#_Samples.nii
svDotMap = true;        % Save Pt#_DotMap.nii
svHotspots = true;      % Save Pt#_Hotspots.nii
% ************************************************

disp(['SID : ' SID])
disp(['T1image : ' T1image])
disp(['BSfile : ' BSfile])

disp(' ') 
disp('Welcome to MOSAICS. One moment please...') 
disp(' ')

% Read the T1-weighted MRI .nii file to a structure called brain. This file
% should have a resolution of 1mm isotropic. If it has a different
% resolution, customizations may need to be made to the script.

%%%SID = inputdlg('Please enter your participant ID and session:');
%%%disp('Select the original T1-weighted image (not skull stripped)')
%%%T1image = uigetfile('*.nii','Select the original T1-weighted image (not skull stripped)');
header = spm_vol(T1image); 
brain = spm_read_vols(header);

% Read the coordinates file exported from Brainsight. It should contain
% four columns, X, Y, Z coordinates and corresponding MEP amplitude

%%%disp('Select the Brainsight coordinate file')
%%%BSfile = uigetfile('*.xls*','Select the Brainsight coordinate file');
inputdata = xlsread(BSfile); 
tic

% Segment the brain into five tissue types and reassemble a skull-stripped
% version [GM(c1)+WM(c2)] for visualization - UNDER DEVELOPMENT

if skullstrip == true
    
    % organise some directories
    mkdir( fullfile(pwd, 'skullstrip') );
    copyfile (T1image, 'skullstrip');
    cd ( fullfile(pwd, 'skullstrip') );
    
    % segment the image using spm segment
    jobfile = {'mos_segment_job.m'};
    jobs = repmat(jobfile, 1, 1);
    inputs = cell(1, 1);
        inputs{1, 1} = cellstr(T1image); % Segment: Volumes - cfg_files
    spm('defaults', 'FMRI');
    spm_jobman('run', jobs, inputs{:});
    
    % recombine GM (c1) and WM (c2) using addition
    %i1 = fullfile(pwd, strcat('c1',T1image));
    i1 = 'c1LCT1.nii';
    i2 = 'c2LCT1.nii';

    %i2 = fullfile(pwd, strcat('c2',T1image));
    Vi = {i1,i2};
    Vo = 'brain.nii';
    spm_imcalc(Vi,Vo,'i1+i2');
    cd ..
else
end

mkdir( fullfile(pwd, char(SID)) );
copyfile (T1image, fullfile(pwd, char(SID)));
cd ( fullfile(pwd, char(SID)) );

% First create empty overlay matrices that are the same size as
% the T1 anatomical (256x256x166) then fill them full of zeros for now

disp('Generating patient space maps')
overlay=   zeros(size(brain));
samples=   zeros(size(brain));
dotmap=    zeros(size(brain));
grid=      zeros(size(brain));

% Import the Excel file containing column vectors x,y,z,m, where xyz are
% Brainsight coordinates and m is the corresponding MEP (or other
% behavioural variable). Brainsight coordinates will be rounded to
% the nearest integer.

x = round(inputdata(:,1));
y = round(inputdata(:,2));
z = round(inputdata(:,3));
m = inputdata(:,4);
numLocs = size(x);

% Update the zeros in the MEP overlay to be MEP amplitudes (variable m).
% Also, update the zeros in the TMS grid to be 99 for visualization.

for i = 1:numLocs(1)
    overlay(x(i),y(i),z(i))=m(i);
    samples(x(i),y(i),z(i))=m(i);
    dotmap(x(i),y(i),z(i))=m(i);
    grid(x(i),y(i),z(i))=99;
end    

% Since the hi-res T1 anatomical has such small voxels we need to dilate
% each location of the TMS grid. TMS has a spread of ~1cm and we typically
% do a grid of ~10mm anyway. So let's make each location 5x5x5mm (125
% voxels) in extent centred on the original coordinates. At the same time,
% also make the grid points slightly bigger so they are easier to visualize.

dilate = 5; % must always be an odd number to ensure proper centering
for i = 1:numLocs
    
    rowmarker=((dilate-1)/2)*-1;
    for j = 1:dilate
        cellmarker = ((dilate-1)/2)*-1;
        for k = 1:dilate
            overlay(x(i)+2, y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            overlay(x(i)+1, y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            overlay(x(i),   y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            overlay(x(i)-1, y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            overlay(x(i)-2, y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            cellmarker = cellmarker+1;
        end
        rowmarker = rowmarker+1;
    end
    
    % grid locations sharing faces w centre (6)
    grid(x(i)+1, y(i),   z(i))=1;     % x+1
    grid(x(i)-1, y(i),   z(i))=1;     % x-1
    grid(x(i),   y(i)+1, z(i))=1;     % y+1
    grid(x(i),   y(i)-1, z(i))=1;     % y-1
    grid(x(i),   y(i),   z(i)+1)=1;   % z+1
    grid(x(i),   y(i),   z(i)-1)=1;   % z-1
end

dilate = 3; % must always be an odd number to ensure proper centering
for i = 1:numLocs
    
    rowmarker=((dilate-1)/2)*-1;
    for j = 1:dilate
        cellmarker = ((dilate-1)/2)*-1;
        for k = 1:dilate
            dotmap(x(i)+1, y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            dotmap(x(i),   y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            dotmap(x(i)-1, y(i)+cellmarker,   z(i)+rowmarker)=m(i);     
            cellmarker = cellmarker+1;
        end
        rowmarker = rowmarker+1;
    end
end
clear numLocs rowmarker cellmarker dilate x y z j k i m;

% Rotate the matrices in the y dimension (AP) to convert from RPS
% (Brainsight) to RAS (Nifti)

overlay =   flip(overlay,2);
samples =   flip(samples,2);
dotmap =    flip(dotmap,2);
grid =      flip(grid,2);

% Save .nii overlay files for display on a brain. some are optional

output=overlay; 
header.fname=strcat(char(SID),'_Hotspots.nii'); 
spm_write_vol(header,output);

if svSamples == true output=samples; header.fname=strcat(char(SID),'_Samples.nii'); spm_write_vol(header,output); end
if svDotMap == true output=dotmap; header.fname=strcat(char(SID),'_DotMap.nii'); spm_write_vol(header,output); end
if svGridLoc == true output=grid; header.fname=strcat(char(SID),'_GridLoc.nii'); spm_write_vol(header,output); end
clear output overlay;

% Smooth the hotspot map using a 3D Gaussian - set smoothing kernel size in
% options above
spm_smooth(strcat(char(SID),'_Hotspots.nii'),strcat(char(SID),'_Heatmap.nii'),smooth,0);

% Calculate hotspot in pt space
[hs_MEP,hs_IDX] = max(samples(:));
[hs_X,hs_Y,hs_Z]= ind2sub(size(samples),hs_IDX);

% Calculate centre of gravity (COG) in pt space
[rowsub, colsub, pagsub] = ind2sub(size(samples),find(samples>MEP_thresh));
grid = round([rowsub, colsub, pagsub]);
grid(:,4) = samples(find(samples>MEP_thresh)); 
cog_x = round((sum(grid(:,1).*grid(:,4)))/sum(grid(:,4)));
cog_y = round((sum(grid(:,2).*grid(:,4)))/sum(grid(:,4)));
cog_z = round((sum(grid(:,3).*grid(:,4)))/sum(grid(:,4)));
%clear grid;

% Normalise outputs to MNI space
if conv2MNI == true
    disp('Normalizing to MNI template space')
    spm_jobman('initcfg');
    
    clear y_file; disp('Select deformation field (or click cancel to calculate a new one)')
    y_file = uigetfile('y_*.nii','Please select deformation file (or cancel to calculate a new one):');
    maps = {T1image;strcat(char(SID),'_Hotspots.nii');strcat(char(SID),'_Samples.nii');strcat(char(SID),'_GridLoc.nii');strcat(char(SID),'_Heatmap.nii');strcat(char(SID),'_DotMap.nii')};

    % User did not select a deformation field, so calculate a new one using
    % Normalise: Estimate & Write
    if isequal(y_file,0)
        jobfile = {'mos_normalise_job.m'};
        jobs = repmat(jobfile, 1, 1);
        inputs = cell(2, 1);
            inputs{1, 1} = cellstr(T1image);   % Normalise: Estimate & Write: Image to Align - cfg_files
            inputs{2, 1} = cellstr(maps);      % Normalise: Estimate & Write: Images to Write - cfg_files
        spm('defaults', 'FMRI');
        spm_jobman('run', jobs, inputs{:});
    
    % User selected a deformation field, so use Normalise: Write instead
    else
        maps = {T1image;strcat(char(SID),'_Hotspots.nii');strcat(char(SID),'_Samples.nii');strcat(char(SID),'_GridLoc.nii');strcat(char(SID),'_Heatmap.nii');strcat(char(SID),'_DotMap.nii')};
        jobfile = {'mos_normalisewrite_job.m'};
        jobs = repmat(jobfile, 1, 1);
        inputs = cell(2, 1);
            inputs{1, 1} = cellstr(y_file);   % Normalise: Write: Deformation Field - cfg_files
            inputs{2, 1} = cellstr(maps);      % Normalise: Write: Images to Write - cfg_files
        spm('defaults', 'FMRI');
        spm_jobman('run', jobs, inputs{:});
    end;
        
    % Load MNI .nii samples file and calculate Hotspot in MNI spce
    samples_MNI_header = spm_vol(strcat('w',char(SID),'_Samples.nii')); 
    samples_MNI = spm_read_vols(samples_MNI_header); 

    [hsm_MEP,hsm_IDX] = max(samples_MNI(:));
    [hsm_X,hsm_Y,hsm_Z]= ind2sub(size(samples_MNI),hsm_IDX);
    clear hsm_IDX;

    % Convert from matrix coordinates to MNI mm coordinates using the transformation in the header (from Xu Cui
    % http://www.alivelearn.net/?p=1434)
    V=spm_vol(strcat('w',char(SID),'_Samples.nii'));  T=V.mat;
    cor = round([hsm_X,hsm_Y,hsm_Z]);
    mni = T*[cor(:,1) cor(:,2) cor(:,3) ones(size(cor,1),1)]';
    mni = mni';
    mni(:,4) = [];
    
    % Calculate the grid locations in MNI space
    [rowsub, colsub, pagsub] = ind2sub(size(samples_MNI),find(samples_MNI>MEP_thresh)); 
    cor = round([rowsub, colsub, pagsub]); clear rowsub colsub pagsub;
    mnigrid = T*[cor(:,1) cor(:,2) cor(:,3) ones(size(cor,1),1)]';
%     mnigrid(1,:) = -mnigrid(1,:);  %flip x
    mnigrid = mnigrid';
    mnigrid(:,4) = samples_MNI(find(samples_MNI>MEP_thresh)); 
    clear samples_MNI;
    
    % Calculate COG in MNI space
    mnicog_x = round((sum(mnigrid(:,1).*mnigrid(:,4)))/sum(mnigrid(:,4)));
    mnicog_y = round((sum(mnigrid(:,2).*mnigrid(:,4)))/sum(mnigrid(:,4)));
    mnicog_z = round((sum(mnigrid(:,3).*mnigrid(:,4)))/sum(mnigrid(:,4)));
    
    % Save output files
    data = {SID, T1image, BSfile, MEP_thresh, smooth, hs_X, hs_Y, hs_Z, hs_MEP, cog_x, cog_y, cog_z, -mni(1), mni(2), mni(3), hsm_MEP, mnicog_x, mnicog_y, mnicog_z};
    mos_writeoutputfiles (SID, conv2MNI, data, mnigrid, grid);

else
    data = {SID, T1image, BSfile, MEP_thresh, smooth, hs_X, hs_Y, hs_Z, hs_MEP, cog_x, cog_y, cog_z};
    mnigrid = 0;
    mos_writeoutputfiles (SID, conv2MNI, data, mnigrid, grid);
end

clear SID T1image BSfile hs_X hs_Y hs_Z hs_MEP cog_x cog_y cog_z mni hsm_MEP mnicog_x mnicog_y mnicog_z;
fprintf('\nMap generation completed successfully in %.0f seconds\n\n',toc)
cd ..


