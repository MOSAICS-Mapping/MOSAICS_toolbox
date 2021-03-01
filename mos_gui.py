#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 13:36:20 2021

@author: Bryce
"""

import os, sys
import logging
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from PIL import ImageTk
from pathlib import PurePath

import mos_main
import mos_find_datasets

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.DEBUG)

# Find where a file is depending on whether we are running code from the package app (frozen)
# or in development mode (not-frozen), in which case this is based on the terminal work dir
def resource_path(path):
    if getattr(sys, "frozen", False):
        # If the frozen flag is set, we are in bundled-app mode!
        resolved_path = os.path.abspath(os.path.join(sys._MEIPASS, path))
    else:
        # Normal development mode. Use os.getcwd() or __file__ as appropriate
        resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    
    return resolved_path

class MOSAICSapp(tk.Tk):
    
    def __init__(self):
        tk.Tk.__init__(self)
        
        # ~~~~~~Configure GUI appearance~~~~~~
        self.title("MOSAICS Toolbox")
        self.geometry("800x512")
        self.resizable(False,False)
        
        self.buttons = tk.Frame(self) # bg="blue"
        self.logo = tk.Frame(self) # bg="red
        
        self.buttons.pack(side=tk.LEFT, expand=False, fill=tk.BOTH, padx=10, pady=10)
        self.logo.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        global img #important so that path to our file doesn't get wiped byPython cleanup
        #background_image = "/Users/Bryce/Desktop/Postdoc_Scripts/GitHub/04_mosaics_2020/1_crop.png"
        background_image = resource_path("1_crop.png")
        img = ImageTk.PhotoImage(file=background_image)
        width, height = 512, 475
        self.background = tk.Canvas(self.logo)
        self.background.pack(expand="yes", fill="both")
        self.background.create_image(width/2, height/2, image=img, anchor="center")
        
        # ~~~~~~Create and arrange GUI buttons~~~~~~
        # select data button
        self.button_select = tk.Button(self.buttons,text="Select data for analysis",padx=15,pady=5,
                                    command=self.call_gui_select) # only works if gui_select isn't already open
        self.button_select.grid(row=1,pady=10)
        
        # configure analysis button
        self.button_configure_analysis = tk.Button(self.buttons,text="Configure analysis",padx=15,pady=5,
                                              command=self.call_gui_configure)
        self.button_configure_analysis.grid(row=2,pady=10)
        
        # MOSIACS analysis button
        self.button_analysis = tk.Button(self.buttons,text = "MOSAICS analysis",padx=15,pady=5,
                                        command=self.call_mosaics)
        self.button_analysis.grid(row=3,pady=10)
        
        self.button_close = tk.Button(self.buttons, text="Close GUI",padx=15,pady=5,
                                 command=self.close_gui)
        self.button_close.grid(row=4,pady=10)
        
        # center buttons with empty top and bottom rows that are greedy for space.
        self.buttons.grid_rowconfigure(0, weight=1)
        self.buttons.grid_rowconfigure(4, weight=1)
        
        # ~~~~~~Initialize global variables~~~~~~
        # self.gui_select_open = tk.BooleanVar()
        self.gui_select_open = False
                
        self.data_dict = dict()
        self.data_dict['data_select_text'] = "No data specified"
        self.data_dict['stim_select_text'] = "No stimulation data specified"
        self.data_dict['stim_flip'] = 0 # tk.Checkbutton in gui_select
        self.data_dict['save_dir'] = os.getcwd()
        self.data_dict['save_prefix'] = 'outputs'
        self.data_dict['select gui open'] = False
        self.data_dict['data list'] = list()
        self.configure_dict = dict()
        # Set default variables for analysis, updated by guiConfigure class as desired
        self.configure_dict['dilate'] = 5
        self.configure_dict['smooth'] = 7
        self.configure_dict['MEP_threshold'] = 0
        self.configure_dict['normalize'] = 0 # tk.Checkbutton (guiConfigure) returns 0 or 1, not True or False
        self.configure_dict['atlas'] = 'MNI152_T1_1mm.nii.gz'
        self.configure_dict['config gui open'] = False
        
    # ~~~~~~Create methods for MOSAICS function~~~~~~
    def call_gui_select(self):
        # check if window is open, if it's not open it!
        if self.data_dict['select gui open'] == True:
            logging.error('Cannot open selection dialogue, window already exists!')
        elif self.data_dict['select gui open'] == False:
            guiSelect(self, self.data_dict)
            # gui_select = guiSelect(self, self.data_dict)

    def call_gui_configure(self):
        if self.configure_dict['config gui open'] == True:
            logging.error('Cannot open configure dialogue, window already exists!')
        elif self.configure_dict['config gui open'] == False:
            guiConfigure(self, self.configure_dict)

    def print_selected_vars(self):
        logging.info('vars from the config dialogue')
        logging.info('dilate: '+str(self.configure_dict['dilate']))
        logging.info('smooth: '+str(self.configure_dict['smooth']))
        logging.info('MEP threshold: '+str(self.configure_dict['MEP_threshold']))
        
    def call_mosaics(self):
        mos_main.main(self.data_dict, self.configure_dict)

    def close_gui(self):
        # note that self.destroy works just fine in terminal but hangs in Spyder IDE
        self.destroy()

class guiSelect(tk.Toplevel):
    
    def __init__(self, master, root_data_dict):
        self.master = master
        #super().__init__(self.master) <--- not sure if I need this, it was in some example code
        self.local_data = root_data_dict
        self.local_data['select gui open'] = True
                
        self.window = tk.Toplevel(master)
        self.window.title("Select data")
        self.window.geometry("300x240")
        self.window.resizable(False,False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10, pady=5)
        
        # ~~~~~~CONFIGURE GUI OBJECTS (BUTTONS ETC)~~~~~~
        self.path_t1 = tk.Label(self.frame,
                            text=self.local_data['data_select_text'],
                            bg="white",
                            width=30,
                            relief="groove",
                            borderwidth=2)
        self.select_t1 = tk.Button(self.frame,
                              text="Select data folder",
                              command = self.find_data)
        self.flip_stim = tk.Checkbutton(self.frame,text="Flip stimulation coordinates?",
                                             variable=self.local_data['stim_flip'],
                                             command=self.toggle_flip)  
        # set flip_stim check button depending upon its current value
        if self.local_data['stim_flip'] == 1:
            self.flip_stim.select()
        elif self.local_data['stim_flip'] == 0:
            self.flip_stim.deselect()
        self.path_save = tk.Label(self.frame,
                            text='...'+self.local_data['save_dir'].split('/')[-2]+'/'+self.local_data['save_dir'].split('/')[-1],
                            bg="white",
                            width=30,
                            relief="groove",
                            borderwidth=2)
        self.select_save = tk.Button(self.frame,
                                text="Select save directory",
                                command = self.set_save_dir)
        self.list_save_name = tk.Label(self.frame,
                                  text="Enter save name prefix below:")
        self.enter_save_name = tk.Entry(self.frame,
                                    relief="groove")
        self.close_button = tk.Button(self.frame,
                                  text="Submit",
                                  command = self.save_and_close)

        # configure the grid
        self.frame.columnconfigure((0,1,2), weight=0)
        self.frame.rowconfigure((0,1,2,3,4,5,6), weight=0)
        
        # arrange assets
        self.path_t1.grid(row=0, pady = 2, columnspan=3, sticky="w")
        self.select_t1.grid(row=1, column=0, sticky="w")
        self.flip_stim.grid(row=2, column=0, sticky="w")
        self.path_save.grid(row=3, column=0, columnspan=3, sticky="w")
        self.select_save.grid(row=4,column=0, sticky="w")
        self.list_save_name.grid(row=5, column=0, sticky="w")
        self.enter_save_name.grid(row=6, column=0, columnspan=2, sticky="w")
        self.close_button.grid(row=7, column=0, sticky="e")

    def find_data(self):
        """
        Change this function name once I've brought in the new find_datasets script
        """
        data_folder = filedialog.askdirectory(initialdir="~/",
                                          title="Select a folder of files to process")
        
        # update the text field to reflect user chosen folder
        p = PurePath(data_folder)
        self.path_t1.config(text='...'+p.anchor+p.name)
        self.local_data['image_select_text'] = '...'+p.anchor+p.name
        
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['data folder'] = data_folder
        
        # make a list of all datasets in this folder, stored as data_dict['data list'] within this function
        self.local_data['data list'] = mos_find_datasets.main(self.local_data)
        
        logging.info('...'+str(len(self.local_data['data list']))+' subjects found for processing in your chosen folder.')
    
    def toggle_flip(self):
        if self.local_data['stim_flip'] == 0:
            self.local_data['stim_flip'] = 1
        elif self.local_data['stim_flip'] == 1:
            self.local_data['stim_flip'] = 0

    def set_save_dir(self):
        save_dir = filedialog.askdirectory(initialdir=self.local_data['save_dir'],
                                           title="Select directory to save output files")
        self.path_save.config(text='...'+save_dir.split('/')[-2]+'/'+save_dir.split('/')[-1])
        self.local_data['save_dir'] = save_dir

    # button to close gui
    def save_and_close(self):
        
        settings_error = False
        
        # checks that both nii and stim data have been selected, and that files exist    
        self.local_data['save_prefix'] = self.enter_save_name.get()

        if 'data folder' in self.local_data:
            if not os.path.isdir(self.local_data['data folder']):
                settings_error = True
                messagebox.showerror('Input Error','Data selection must be a folder, please re-select.')
        else:
            settings_error = True
            messagebox.showerror('Input Error','Data not found, please select a folder.')
        
        if settings_error == False:
            self.local_data['select gui open'] = False
            self.window.destroy()

class guiConfigure(tk.Toplevel):
    
    def __init__(self, master, root_configure_dict):
        self.master = master
        #super().__init__(self.master) <--- not sure if I need this, it was in some example code
        self.local_data = root_configure_dict
        self.local_data['config gui open'] = True
                
        self.window = tk.Toplevel(master)
        self.window.title("Configure analysis")
        self.window.geometry("440x200")
        self.window.resizable(False,False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10, pady=5)
        
        # entry field for dilation
        self.dilate_label = tk.Label(self.frame, text="Stim. data dilation (odd integer):")
        self.dilate_form = tk.Entry(self.frame,width=5,relief="groove",justify='center')
        self.dilate_form.insert(0,str(self.local_data['dilate']))
        # entry field for smooth
        self.smooth_label = tk.Label(self.frame, text="Gaussian smoothing kernel (mm):")
        self.smooth_form = tk.Entry(self.frame,width=5,relief="groove",justify='center')
        self.smooth_form.insert(0,str(self.local_data['smooth']))
        # entry field for MEP threshold
        self.MEP_label = tk.Label(self.frame, text="MEP threshold (mV):")
        self.MEP_form = tk.Entry(self.frame,width=5,relief="groove",justify='center')
        self.MEP_form.insert(0,str(self.local_data['MEP_threshold']))
        # checkbox for normalise or no?
        self.normalise_bool = tk.Checkbutton(self.frame,text="Warp to standard atlas?",
                                             variable=self.local_data['normalize'], command=self.warp_check)
        # set flip_stim check button depending upon its current value
        if self.local_data['normalize'] == 1:
            self.normalise_bool.select()
        elif self.local_data['normalize'] == 0:
            self.normalise_bool.deselect()
        # if checkbox is checked, pick a standard atlas to use:
        self.normalise_atlas = tk.Label(self.frame,text="./"+str(self.local_data['atlas']),
                                        relief="groove",borderwidth=2, width=22)#width=30
        self.normalise_atlas_select = tk.Button(self.frame,text="Choose standard atlas:",
                                               state='disabled',command = self.select_atlas)
        self.bg_init = self.normalise_atlas_select.cget("background")
        self.close_button = tk.Button(self.frame,text="Submit",command = self.save_and_close)
                
        # configure the grid
        self.frame.columnconfigure((0,1), weight=0)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(6, weight=1)
        # pack buttons in a grid!
        self.dilate_label.grid(row=1,column=0)
        self.dilate_form.grid(row=1,column=1,sticky="w")
        self.smooth_label.grid(row=2,column=0)
        self.smooth_form.grid(row=2,column=1,sticky="w")
        self.MEP_label.grid(row=3,column=0)
        self.MEP_form.grid(row=3,column=1,sticky="w")
        self.normalise_bool.grid(row=4, column=0)
        self.normalise_atlas_select.grid(row=5,column=0)
        self.normalise_atlas.grid(row=5,column=1)
        self.close_button.grid(row=6,column=1)
    
    def warp_check(self):
        # logging.info('initial self.local_data(normalize) = '+str(self.local_data['normalize']))
        if self.local_data['normalize'] == 1:
            self.normalise_atlas_select.configure(state='disabled')
            self.normalise_atlas.configure(bg=self.bg_init)
            self.local_data['normalize'] = 0
        elif self.local_data['normalize'] == 0:
            self.normalise_atlas_select.configure(state='normal')
            self.normalise_atlas.configure(bg='white')
            self.local_data['normalize'] = 1
        # logging.info('function end self.local_data(normalize) = '+str(self.local_data['normalize']))
    
    def select_atlas(self):
        file_atlas = filedialog.askopenfilename(initialdir="~/",
                                                title="Select standard atlas to normalise measure maps to (*.nii, *.nii.gz)",
                                                filetypes=(("Nifti", ".nii"), ("Compressed Nifti", ".nii.gz"), ("All files", "*.*")))
        p = PurePath(file_atlas)
        self.normalise_atlas.config(text=p.anchor+'...'+p.name[-19:])
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['atlas'] = file_atlas
        
    # Submit and close button MUST include checks that each value provided is valid!          
    def save_and_close(self):
        
        settings_error = False
        
        # update dilate
        self.local_data['dilate'] = self.dilate_form.get()
        # print(int(self.local_data['dilate'])%2)
        # print(int(self.local_data['dilate']) < 0)
        if int(self.local_data['dilate'])%2 != 1 or int(self.local_data['dilate']) < 0:
            settings_error = True
            messagebox.showerror('Input Error','Dilation value must be a positive, odd integer (no decimals).')
        # update smooth
        self.local_data['smooth'] = self.smooth_form.get()
        """
        DEV NOTE:
            - Error check for smooth? Not sure what problem this variable could introduce. Maybe just a warning
            if we're concerned that the smoothing kernel is too large
        """
        # update MEP threshold
        self.local_data['MEP_threshold'] = self.MEP_form.get()
        # ['normalize'] is already set each time the button is checked / unchecked
        # ['atlas'] already set, or updated when selected in self.select_atlas()
        
        if settings_error == False:
            self.local_data['config gui open'] = False
            self.window.destroy()

def main():
    MOS = MOSAICSapp()
    MOS.mainloop()

if __name__ == "__main__":
    main()