# import pygame as pg
import tkinter as tk
import os
from PIL import ImageTk, Image

"""
Changelog by Bryce, Nov 25:
  - added global variables for brain_file and coordinates so that they could be passed to the mosaics_analysis script
  - added a global subject_ID variable, defined by the user in a dialog box after the user selects their nifti file
  - changed Mosaics() to call_mosaics()
  - added mosaics_analysis.py to Git project, imported that code to this script (line 8)
  - MOSAICS button now calls main function of mosaics_analysis.py which takes the brain file, coordinates, and subject ID and runs the
  MOSAICS analysis, outputting subject files to the MOSAICS script folder (where gui.py is run from)
  - adjusted frame geometry from 600x550 to 750x550
  - adjusted button placing and renamed buttons to be a bit more specific
     - new labels + placements: 'Upload T1 image (*.nii) @ relx = 0.05'
                                'Upload landmark coordinates (*.xlsx) @ relx = 0.32'
                                'MOSAICS analysis @ relx = 0.703'
"""

### Important variables to change on Ajiit's computer
scripts_path = "/Users/Bryce/Desktop/Postdoc_Projects/3_MULTIMODAL_HOTSPOTS/MOSAICS/MOSAICS_Python/"
background_image = scripts_path+"1.png"
###
os.chdir(scripts_path)
import mosaics_analysis

frame = tk.Tk()
frame.title("MOSAICS 2020")
img = ImageTk.PhotoImage(Image.open(background_image))
panel = Label(frame, image = img)

# panel = Label(frame)
# frame.configure(background="#00FFFF")

frame.geometry("750x650")
 
def select_brain():
    global brain_file
    global subject_ID
    brain_file = tk.filedialog.askopenfile(initialdir="/", title="Select T1 Image",
                                      filetypes=(("Brain", ".nii"), ("All Files", "*.*")))
    subject_ID = tk.simpledialog.askstring("Input", "What is this file's subject ID?")
    

def select_coordinates():
    global coordinates
    coordinates = tk.filedialog.askopenfile(initialdir="/", title="Select Brainsight Coordinates",
                                      filetypes=(("Coordinates", ".xlsx"), ("All Files", "*.*")))

def call_mosaics():
    print('ready to run script with subprocess.run!')
    mosaics_analysis.main(brain_file.name, coordinates.name, subject_ID, scripts_path)
    
    # below code were part of my experiments but I don't think I need it anymore, leaving for now though
    #mosaics_python_path = os.path.join(os.getcwd(),"mosaics_analysis.py")
    #run("Python3", mosaics_python_path, brain_file.name, coordinates.name)
    #run(["Python3", "{}".format(self.path)])

def select_save_dir():
    save_dir = tk.filedialog.askdirectory(initialdir="/", title="Where should we save files?")
    os.chdir(save_dir)
    print("MOSAICS files will be saved in: "+save_dir)

#background = tk.Frame(frame, bg="red")
#background.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)

panel.pack(side = "bottom", fill = "both", expand = "no")

save_dir_button = tk.Button(frame, text="Select directory to save files", padx=15,
                            pady=5, fg="black", bg="white", command=select_save_dir)

save_dir_button.place(relx = 0.67, rely=0.00)

select_brain_button = tk.Button(frame, text="Upload T1 image (*.nii)", padx=15,
                        pady=5, fg="black", bg="white", command=select_brain)

#select_brain_button.place(relx = 0.2, rely = 0.0) # <<- Ajiit's original relx
select_brain_button.place(relx = 0.01, rely = 0.0)

select_coordinates_button = tk.Button(frame, text="Upload landmark coordinates (*.xlsx)", padx=15,
                        pady=5, fg="black", bg="white", command=select_coordinates)

#select_coordinates_button.place(relx=0.4, rely=0.0) # <<- Ajiit's original relx
select_coordinates_button.place(relx=0.285, rely=0.0)

proceed_and_display = tk.Button(frame, text = "MOSAICS analysis", padx = 15,
                        pady = 5, fg = "black", bg = "white", command = call_mosaics)

#proceed_and_display.place(relx = 0.675, rely = 0.0) # <<- Ajiit's original relx
proceed_and_display.place(relx = 0.35, rely = 0.05)

# #----------------------#
# # Buttons, grid option
# button_uploadT1 = tk.Button(frame, text="UploadT1 image (*.nii)", padx=10, pady=5, command=select_brain)
# button_uploadT1.grid(row=0,column=0)

# button_upload_coordinates = tk.Button(frame, text="Upload landmark coordinates (*.xlsx)", \
#                                       padx=10, pady=5, command=select_coordinates)
# button_upload_coordinates.grid(row=0,column=1)

# button_save_dir = tk.Button(frame, text="Upload T1 image (*.nii)", padx=10, pady=5, command=select_save_dir)
# button_save_dir.grid(row=0,column=2)

# button_mosaics_analysis = tk.Button(frame, text="MOSAICS analysis", padx=10, pady=5, command=call_mosaics)
# button_mosaics_analysis.grid(row=1, column=2)
# #----------------------#

frame.mainloop()










