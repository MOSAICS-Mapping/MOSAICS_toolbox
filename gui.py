import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.simpledialog as simpledialog
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
                                
                                
Features to add:
    - processing for multiple subjects at once
        - When selecting data, first pop-up = single or multiple subjects? 
            - Then set a variable which determines future processing steps
    
"""

### Important variables to change on Ajiit's computer
scripts_path = "/Users/Bryce/Desktop/Postdoc_Scripts/GitHub/04_mosaics_2020/"
background_image = scripts_path+"1_crop.png"
###
os.chdir(scripts_path)  
 
def select_brain():
    global brain_file
    global subject_ID
    brain_file = filedialog.askopenfile(initialdir="/", title="Select T1 Image",
                                      filetypes=(("Brain", ".nii"), ("All Files", "*.*")))
    subject_ID = simpledialog.askstring("Input", "What is this file's subject ID?")

def select_coordinates():
    global coordinates
    coordinates = filedialog.askopenfile(initialdir="/", title="Select Brainsight Coordinates",
                                      filetypes=(("Coordinates", ".xlsx"), ("All Files", "*.*")))

def call_mosaics():
    print('ready to run script with subprocess.run!')
    mosaics_analysis.main(brain_file.name, coordinates.name, subject_ID, scripts_path)
    
    # below code were part of my experiments but I don't think I need it anymore, leaving for now though
    #mosaics_python_path = os.path.join(os.getcwd(),"mosaics_analysis.py")
    #run("Python3", mosaics_python_path, brain_file.name, coordinates.name)
    #run(["Python3", "{}".format(self.path)])

def select_save_dir():
    save_dir = filedialog.askdirectory(initialdir="/", title="Where should we save files?")
    os.chdir(save_dir)
    print("MOSAICS files will be saved in: "+save_dir)

def configure_gui(frame):
    frame.title("MOSAICS 2020")
    frame.geometry("850x512")
    frame.resizable(False, False)
    
    buttons = tk.Frame(root, bg="blue")
    logo = tk.Frame(root, bg="red")

    buttons.pack(side = tk.LEFT, expand = True, fill = tk.BOTH, padx=5, pady=10)
    logo.pack(side = tk.RIGHT, expand = True, fill = tk.BOTH, padx=10, pady=10)
    
    return buttons, logo

# def set_background(frame):
#     img = ImageTk.PhotoImage(Image.open(background_image))
#     background = tk.Label(frame, image = img)
#     background.pack()

def create_widgets(frame):
    
    # center buttons with empty top and bottom rows that are greedy for space.
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_rowconfigure(5, weight=1)
    
    select_brain_button = tk.Button(frame,
                                    text="Select data for analysis",
                                    padx=15,
                                    pady=5,
                                    command=select_brain)
    select_brain_button.grid(row=1)
    
    select_coordinates_button = tk.Button(frame,
                                          text="Upload landmark coordinates (*.xlsx)",
                                          padx=15,
                                          pady=5,
                                          command=select_coordinates)
    select_coordinates_button.grid(row=2)
    
    save_dir_button = tk.Button(frame,
                                text="Select directory to save files",
                                padx=15,
                                pady=5, 
                                command=select_save_dir)
    save_dir_button.grid(row=3)
    
    analysis_button = tk.Button(frame,
                                    text = "MOSAICS analysis",
                                    padx = 15,
                                    pady = 5,
                                    command = call_mosaics)
    analysis_button.grid(row=4)

if __name__ == '__main__':
    
    root = tk.Tk()

    frame_buttons, frame_logo = configure_gui(root)

    # setting background doesn't work if I put it into a function, probably a scope issue.
    img = ImageTk.PhotoImage(file=background_image)
    width, height = 512, 512
    background = tk.Canvas(width=width, height=height)
    background.pack(expand="YES", fill="both")
    background.create_image(width/2,height/2,image=img,anchor="center")
    
    create_widgets(frame_buttons)

    root.mainloop()










