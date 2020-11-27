# 04_mosaics_2020
3 important factors must be adapted for Ajiit's computer before the GUI will work.

1. gui.py line 26 - location of the MOSAICS background image, I couldn't get a relative path to work so I had to hard-code the location of this png file on my system.
2. gui.py line 27 - Location of all scripts that are called in mosaics_analysis.m. This is the folder of scripts provided by Helen on our team's Drive folder, with names like 'mos_normalise.mat', 'mos_segment.mat', etc.
3. The following pyinstaller command must be run (requires pyinstaller to be installed on your system ):
    - cd to the pyinstaller_build directory
    - pyinstaller --onefile --additional-hooks-dir=hooks gui.py