#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 13:36:20 2021

@author: Bryce

Toolbox version: α - v1.1.2
"""

import os, sys
import logging
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from PIL import ImageTk
from pathlib import PurePath, Path
import subprocess

from queue import Queue, Empty
from threading import Thread

import mos_analysis_main
import mos_find_datasets
import mos_analysis_group

main_logger = logging.getLogger('main')

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.disable(logging.DEBUG)

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
        
        self.app_layout()
        self.declare_dicts()
    
    # ~~~~~~ Initialization functions (created to declutter __init__)
    def app_layout(self):
        
        # ~~~~~~Baseline GUI appearance (size, parent frames)~~~~~~
        self.title("MOSAICS Toolbox")
        
        # Dimensions and placement of gui window
        gui_w = 950
        gui_h = 700
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w/2) - (gui_w/2)
        y = (screen_h/2) - (gui_h/2)
        self.geometry('%dx%d+%d+%d' % (gui_w, gui_h, x, y))
        # self.resizable(False,False)       
        
        # Create baseline GUI frames
        self.buttons = tk.Frame(self) # bg="blue"
        self.graphics = tk.Frame(self)
        self.logger = tk.Frame(self)
        
        # Arrange GUI Frames     
        self.buttons.grid(row=0, column=0, rowspan=4, columnspan=1, sticky="nsew", padx=10)
        self.graphics.grid(row=0, column=1, rowspan=3, columnspan=4, sticky="nsew", pady=(10,0))
        self.logger.grid(row=3, column=1, rowspan=1, columnspan=4, sticky="nsew", pady=(0,15))

        for r in range(4):
            self.rowconfigure(r, weight=1)
        for c in range(5):
            self.columnconfigure(c, weight=1)
        
        # ~~~~~~ BBACKGROUND GRAPHICS FRAME ~~~~~~
        # Add MOSAICS logo to self.graphics Frame
        global img #important so that path to our file doesn't get wiped byPython cleanup
        background_image = resource_path("include/1_crop.png")
        img = ImageTk.PhotoImage(file=background_image)
        width, height = 512, 475

        self.background = tk.Canvas(self.graphics)
        self.background.pack(expand="yes", fill="both")
        self.background.create_image(width/2, height/2, image=img, anchor="center")
        
        # ~~~~~~ BUTTONS FRAME ~~~~~~
        # select data button
        self.button_select = tk.Button(self.buttons,
                                       text="Select data",
                                       pady=5,
                                       width=15,
                                       command=self.call_gui_select) # only works if gui_select isn't already open
        # configure analysis button
        self.button_configure_analysis = tk.Button(self.buttons,
                                                   text="Configure processing",
                                                   pady=5,
                                                   width=15,
                                                   command=self.call_gui_configure)
        # MOSIACS analysis button
        self.button_analysis_main = tk.Button(self.buttons,
                                         text="MOSAICS analysis",
                                         pady=5,
                                         width=15,
                                         command=self.call_main_analysis_threaded)
        self.button_analysis_group = tk.Button(self.buttons,
                                               text="Group-wise analysis",
                                               pady=5,
                                               width=15,
                                               command=self.call_group_analysis_threaded)
        self.button_view = tk.Button(self.buttons,
                                     text="Launch MRIcroGL",
                                     pady=5,
                                     width=15,
                                     command=self.view_results_threaded)
        self.button_close = tk.Button(self.buttons,
                                      text="Close GUI",
                                      pady=5,
                                      width=10,
                                      command=self.close_app)
        
        # ~~~~~~Arrange buttons in Button frame (left)~~~~~~
        self.button_select.grid(row=1,pady=10)
        self.button_configure_analysis.grid(row=2,pady=10)
        self.button_analysis_main.grid(row=3,pady=10)
        self.button_analysis_group.grid(row=4,pady=10)
        self.button_view.grid(row=5,pady=10)
        self.button_close.grid(row=6,pady=10)
        # center buttons with empty top and bottom rows that are greedy for space.
        self.buttons.grid_rowconfigure(0, weight=1)
        self.buttons.grid_rowconfigure(7, weight=1)        
        
        # ~~~~~~ LOGGING FRAME ~~~~~~
        self.logger_text = tk.Text(self.logger,
                                   state="disabled",
                                   relief="groove",
                                   borderwidth=2,
                                   wrap="word",
                                   height=3)
        self.logger_scrollbar = tk.Scrollbar(self.logger,
                                             command=self.logger_text.yview)
        self.logger_text.config(yscrollcommand=self.logger_scrollbar.set)

        self.logger_text.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        self.logger_scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
        
    def declare_dicts(self):
        
        self.data_dict = dict()
        self.data_dict['data select text'] = "No data specified"
        # self.data_dict['stim_flip'] = tk.IntVar(self) # tk.Checkbutton in gui_select
        self.data_dict['brainmask check'] = tk.IntVar(self) # default is 0
        self.data_dict['brainmask suffix'] = '_brain_mask.nii.gz'
        self.data_dict['stim_coords_list'] = ["Brainsight", "Nifti"]
        self.data_dict['stim_coords'] = tk.StringVar(self)
        self.data_dict['stim_coords'].set(self.data_dict['stim_coords_list'][0])
        self.data_dict['save_dir'] = os.getcwd()
        self.data_dict['save_prefix'] = 'outputs'
        self.data_dict['data list'] = list()
        self.data_dict['select gui open'] = None
        self.data_dict['grid spacing'] = 7
        
        self.configure_dict = dict()
        # Set default variables for analysis, updated by guiConfigure class as desired
        self.configure_dict['dilate'] = 3
        self.configure_dict['smooth'] = 7
        self.configure_dict['MEP_threshold'] = 0
        self.configure_dict['normalize'] = tk.IntVar(self) # default is 0
        self.configure_dict['atlas'] = resource_path('include/MNI152_T1_1mm.nii.gz')
        self.configure_dict['atlas mask'] = resource_path('include/MNI152_T1_1mm_brain_mask.nii.gz')
        self.configure_dict['config gui open'] = None
    
    # ~~~~~~ Methods for MOSAICS functions ~~~~~~
    def call_gui_select(self):
        if self.data_dict['select gui open'] is None:
            self.gui_select_master = tk.Toplevel(self.master)
            self.gui_select_master.protocol("WM_DELETE_WINDOW", self.close_gui_select)
            self.gui_select = guiSelect(self.gui_select_master,
                                        self.data_dict,
                                        self.configure_dict)
            CenterToWin(self.gui_select_master)
        else:
            main_logger.error('Cannot open selection dialogue, window already exists!')

    def call_gui_configure(self):
        if self.configure_dict['config gui open'] == None:
            self.gui_config_master = tk.Toplevel(self.master)
            self.gui_config_master.protocol("WM_DELETE_WINDOW", self.close_gui_config)
            self.gui_config = guiConfigure(self.gui_config_master,
                                        self.configure_dict)
            CenterToWin(self.gui_config_master)
        else:
            main_logger.error('Cannot open configure dialogue, window already exists!')

    # def call_mosaics(self):
    #     mos_main.main(self.data_dict, self.configure_dict)

    def call_main_analysis_threaded(self):
        
        main_processing_thread = MainAsyncProcessing(self.data_dict, self.configure_dict)
        if main_processing_thread.running == False:
            self.button_analysis_main['state'] = tk.DISABLED
            main_processing_thread.start()
            self.monitor_thread_main(main_processing_thread)
        
    def call_group_analysis_threaded(self):
        group_processing_thread = GroupAsyncProcessing(self.data_dict, self.configure_dict)
        if group_processing_thread.running == False:
            self.button_analysis_group['state'] = tk.DISABLED
            group_processing_thread.start()
            self.monitor_thread_group(group_processing_thread)
            
    def view_results_threaded(self):
        view_processing_thread = ViewAsyncProcessing()
        if view_processing_thread.running == False:
            self.button_view['state'] = tk.DISABLED
            view_processing_thread.start()
            self.monitor_thread_viewer(view_processing_thread)
        
    def monitor_thread_main(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self.monitor_thread_main(thread))
        else:
            self.button_analysis_main['state'] = tk.NORMAL
            
    def monitor_thread_group(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self.monitor_thread_group(thread))
        else:
            self.button_analysis_group['state'] = tk.NORMAL
            
    def monitor_thread_viewer(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self.monitor_thread_viewer(thread))
        else:
            self.button_view['state'] = tk.NORMAL

    def view_results(self):
        
        main_logger.info('...Launching MRIcroGL')

        # Debugging section below -----
        # tag = 'LCT1'
        # img_brain = os.path.join(self.data_dict['save_dir'], tag, tag+'_brain.nii.gz')
        # img_responses = os.path.join(self.data_dict['save_dir'], tag, tag+'_responses.nii.gz')
        # img_heatmap = os.path.join(self.data_dict['save_dir'], tag, tag+'_heatmap.nii.gz')

        # main_logger.info(img_brain)
        # main_logger.info(img_responses)
        # main_logger.info(img_heatmap)
        # Debugging section above -----

        # open a window that asks which person, from the data folder, you want to view?
        # 3 radio buttons:
        # option 1: dropdown menu with the list of tags from the data folder
        # option 2: cycle through the list above
        # option 3: the group-average template on the MNI brain

        subprocess.call(['./include/MRIcroGL.app/Contents/MacOS/MRIcroGL','-s','mos_viewer_launch.py'])
        
    def close_gui_select(self):
        self.gui_select_master.destroy()
        self.data_dict['select gui open'] = None

    def close_gui_config(self):
        self.gui_config_master.destroy()
        self.configure_dict['config gui open'] = None

    def close_app(self):
        # note that self.destroy works just fine in terminal but hangs in Spyder IDE
        self.destroy()

class guiSelect(tk.Toplevel):
    
    def __init__(self, master, root_data_dict, root_config_dict):
        
        # tk.Toplevel.__init__(self, master)
        
        #self.master = master
        # super().__init__(master) #<--- works without this, it was in some example code
        self.local_data = root_data_dict
        self.config_dict = root_config_dict

        self.local_data['select gui open'] = True

        self.window = master
        
        self.gui_select_layout()
        #CenterToWin(self, master)

    def gui_select_layout(self):
        self.window.title("Select data")
        # self.window.geometry("300x210")
        
        self.window.resizable(False,False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10,pady=5)
        
        # ~~~~~~CONFIGURE GUI OBJECTS (BUTTONS ETC)~~~~~~
        self.data_label = tk.Label(self.frame,
                                   text="Data folder: ")
        self.data_path = tk.Label(self.frame,
                            text=self.local_data['data select text'],
                            bg="white",
                            width=20, #30
                            relief="groove",
                            borderwidth=2)
        self.data_select = tk.Button(self.frame,
                              text="Select data folder",
                              command = self.find_data)
        
        # checkbox: specify your own brainmask?
        self.brainmask_label = tk.Label(self.frame,
                                        text="Brainmask suffix: ")
        self.brainmask_check = tk.Checkbutton(self.frame, 
                                              text="Custom suffix",
                                              variable=self.local_data['brainmask check'],
                                              command=self.mask_check)
        # entry field for brainmask suffix if user wants to change it
        self.brainmask_suffix = tk.Entry(self.frame,
                                         relief="groove",
                                         justify='center')
        self.brainmask_suffix.delete(0, tk.END)
        self.brainmask_suffix.insert(0, self.local_data['brainmask suffix'])
       # set brainmask check button and entry field depending upon its current value
        if self.local_data['brainmask check'].get() == 1:
            self.brainmask_check.select()
            self.brainmask_suffix.config(state='normal')
        elif self.local_data['brainmask check'].get() == 0:
            self.brainmask_check.deselect()
            self.brainmask_suffix.config(state='readonly')    
        # specify whether stimulation data is in Brainsight or Nifti coordinate system
        self.flip_stim_label = tk.Label(self.frame, text="Stimulation coordinate system: ")
        self.flip_stim_opts = tk.OptionMenu(self.frame, self.local_data['stim_coords'], *self.local_data['stim_coords_list'])
        self.flip_stim_opts.config(width=8)
        # set grid spacing (7mm for SPORT)
        self.gridspace_label = tk.Label(self.frame,
                                 text="Grid spacing (mm):")
        self.gridspace_form = tk.Entry(self.frame,
                                      width=5,
                                      relief="groove",
                                      justify="center")
        self.gridspace_form.insert(0,str(self.local_data['grid spacing']))
        
        save_text = os.path.normpath(self.local_data['save_dir'])
        self.save_label = tk.Label(self.frame,
                                   text="Output folder: ")
        self.path_save = tk.Label(self.frame,
                            text='...'+save_text.split(os.sep)[-2]+os.sep+save_text.split(os.sep)[-1],
                            bg="white",
                            width=20, #30
                            relief="groove",
                            borderwidth=2)
        self.select_save = tk.Button(self.frame,
                                text="Select save directory",
                                command = self.set_save_dir)
        
        self.close_button = tk.Button(self.frame,
                                  text="Save",
                                  command = self.save_and_close)

        # GRID ARRANGEMENT AND CONFIG BELOW    
        self.data_label.grid(row=0, column=0, columnspan=1, pady = (5,2), sticky="e")
        self.data_path.grid(row=0, column=1, columnspan=2, pady = (5,2), sticky="w")
        self.data_select.grid(row=0, column=3, columnspan=1, sticky="w")
        self.brainmask_label.grid(row=1, column=0, columnspan=1, sticky="e")
        self.brainmask_suffix.grid(row=1, column=1, columnspan=2, sticky="w")
        self.brainmask_check.grid(row=1, column=3, columnspan=1, sticky="w")
        self.flip_stim_label.grid(row=2, column=0, columnspan=1, sticky="e")
        self.flip_stim_opts.grid(row=2, column=1, columnspan=1, sticky="w")
        self.gridspace_label.grid(row=3, column=0, columnspan=1, sticky="e")
        self.gridspace_form.grid(row=3, column=1, columnspan=1, sticky="w")
        self.save_label.grid(row=4, column=0, columnspan=1, pady=2, sticky="e")
        self.path_save.grid(row=4, column=1, columnspan=2, pady=2, sticky="w")
        self.select_save.grid(row=4,column=3, columnspan=1, sticky="w")
        self.close_button.grid(row=5, column=3, columnspan=1, pady=(8,0), sticky="w")

        # configure the grid
        for r in range(6):
            self.frame.rowconfigure(r, weight=1)
        for c in range(4):
            self.frame.columnconfigure(c, weight=1)
        
    def find_data(self):

        # Path.home() used here to get home directory for osx and windows, both
        data_folder = filedialog.askdirectory(initialdir=str(Path.home()),
                                          title="Select a folder of files to process")
        
        # update the text field to reflect user chosen folder
        p = PurePath(data_folder)
        self.data_path.config(text=os.path.join('...'+p.anchor,p.name))
        self.local_data['data select text'] = os.path.join('...'+p.anchor+p.name)
        
        # update save field to reflect a default 'outputs' folder unless user changes below
        self.path_save.config(text=os.path.join('...'+p.anchor,p.name,'outputs'))
        self.local_data['save_dir'] = os.path.join(data_folder, 'outputs')
        
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['data folder'] = data_folder
        
        # make a list of all datasets in this folder, stored as data_dict['data list'] within this function
        self.local_data['data list'] = mos_find_datasets.main(self.local_data, self.config_dict)
        
        main_logger.info('...'+str(len(self.local_data['data list']))+' subjects found for processing in your chosen folder.')

    def mask_check(self):
        if self.local_data['brainmask check'].get() == 1:
            self.brainmask_suffix.config(state='normal')
        elif self.local_data['brainmask check'].get() == 0:
            self.brainmask_suffix.config(state='readonly')

    def set_save_dir(self):
        save_dir = filedialog.askdirectory(initialdir=self.local_data['save_dir'],
                                           title="Select directory to save output files")
        p = PurePath(save_dir)
        self.path_save.config(text=os.path.join('...'+p.anchor,p.name))
        
        self.local_data['save_dir'] = save_dir

    def save_and_close(self):
        
        settings_error = False
        
        # checks that both nii and stim data have been selected, and that files exist    

        if 'data folder' in self.local_data:
            if not os.path.isdir(self.local_data['data folder']):
                settings_error = True
                messagebox.showerror('Input Error','Data selection must be a folder, please re-select.')
        else:
            settings_error = True
            messagebox.showerror('Input Error','Data not found, please select a folder.')
        
        if settings_error == False:
            self.local_data['data list'] = mos_find_datasets.main(self.local_data, self.config_dict)
            main_logger.info('...double checking data folder, '+str(len(self.local_data['data list']))+' subjects found for processing.')
            
            self.local_data['grid spacing'] = self.gridspace_form.get()
            
            self.window.destroy()
            self.local_data['select gui open'] = None
        
class guiConfigure(tk.Toplevel):
    
    def __init__(self, master, root_configure_dict):
        
        self.master = master
        #super().__init__(self.master) <--- not sure if I need this, it was in some example code
        self.local_data = root_configure_dict
        
        self.local_data['config gui open'] = True
                
        self.window = master
        
        self.gui_configure_layout()
        
    def gui_configure_layout(self):

        self.window.title("Configure analysis")
        #self.window.title("Select data")
        self.window.resizable(False,False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10, pady=5)
        
        # ~~~ Establish all of the buttons in this form ~~~
        # entry field for dilation
        self.dilate_label = tk.Label(self.frame,
                                     text="Stimulation dilation (mm):")
        self.dilate_form = tk.Entry(self.frame,
                                    width=5,
                                    relief="groove",
                                    justify='center')
        self.dilate_form.insert(0,str(self.local_data['dilate']))
        
        # entry field for smooth
        self.smooth_label = tk.Label(self.frame,
                                     text="Gaussian smoothing kernel (mm):")
        self.smooth_form = tk.Entry(self.frame,
                                    width=5,
                                    relief="groove",
                                    justify='center')
        self.smooth_form.insert(0,str(self.local_data['smooth']))
        
        # entry field for MEP threshold
        self.MEP_label = tk.Label(self.frame,
                                  text="MEP threshold (% max):")
        self.MEP_form = tk.Entry(self.frame,
                                 width=5,
                                 relief="groove",
                                 justify='center')
        self.MEP_form.insert(0,str(self.local_data['MEP_threshold']))
        
        # checkbox for normalise or no?
        self.normalise_bool = tk.Checkbutton(self.frame,
                                             text="Warp to standard atlas?",
                                             variable=self.local_data['normalize'],
                                             command=self.warp_check)
        # set normalize check button depending upon its current value
        if self.local_data['normalize'].get() == 1:
            self.normalise_bool.select()
        elif self.local_data['normalize'].get() == 0:
            self.normalise_bool.deselect()
            
        # if checkbox is checked, pick a standard atlas to use:
        self.normalise_atlas = tk.Label(self.frame,
                                        text="./include/"+str(os.path.basename(self.local_data['atlas'])),
                                        relief="groove",
                                        borderwidth=2,
                                        width=35)
        self.normalise_atlas_select = tk.Button(self.frame,
                                                text="Choose standard atlas:",
                                                state='disabled',
                                                command = self.select_atlas)
        
        # if checkbox is checked, pick a matching brain mask to use:
        self.atlas_mask = tk.Label(self.frame,
                                        text="./include/"+str(os.path.basename(self.local_data['atlas mask'])),
                                        relief="groove",
                                        borderwidth=2,
                                        width=35)
        self.atlas_mask_select = tk.Button(self.frame,
                                                text="Choose standard atlas mask:",
                                                state='disabled',
                                                command = self.select_atlas_mask)
        
        self.bg_init = self.normalise_atlas_select.cget("background")
        self.close_button = tk.Button(self.frame,
                                      text="Save",
                                      command = self.save_and_close)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        

        # GRID ARRANGEMENT AND CONFIGURE BELOW
        self.dilate_label.grid(row=1,column=0, columnspan=1, sticky="e")
        self.dilate_form.grid(row=1,column=1, columnspan=1, sticky="w")
        self.smooth_label.grid(row=2,column=0, columnspan=1, sticky="e")
        self.smooth_form.grid(row=2,column=1, columnspan=1, sticky="w")
        self.MEP_label.grid(row=3,column=0, columnspan=1, sticky="e")
        self.MEP_form.grid(row=3,column=1, columnspan=1, sticky="w")

        self.normalise_bool.grid(row=4, column=1, columnspan=1, sticky="w")
        self.normalise_atlas_select.grid(row=5, columnspan=1,column=0, padx=2, sticky="e")
        self.normalise_atlas.grid(row=5,column=1, columnspan=1, sticky="w")
        self.atlas_mask_select.grid(row=6, column=0, columnspan=1, padx=2, sticky="e")
        self.atlas_mask.grid(row=6,column=1,pady=5, columnspan=1, sticky="w")
        self.close_button.grid(row=7,column=1, columnspan=1, sticky="w")

        # configure the grid
        for r in range(8):
            self.frame.rowconfigure(r, weight=1)
        for c in range(2):
            self.frame.columnconfigure(c, weight=1)
        
    def warp_check(self):
        if self.local_data['normalize'].get() == 0:
            self.normalise_atlas_select.configure(state='disabled')
            self.atlas_mask_select.configure(state='disabled')
            self.normalise_atlas.configure(bg=self.bg_init)
            self.atlas_mask.configure(bg=self.bg_init)
        elif self.local_data['normalize'].get() == 1:
            self.normalise_atlas_select.configure(state='normal')
            self.atlas_mask_select.configure(state='normal')
            self.normalise_atlas.configure(bg='white')
            self.atlas_mask.configure(bg='white')
    
    def select_atlas(self):
        file_atlas = filedialog.askopenfilename(initialdir=str(Path.home()),
                                                title="Select standard atlas to normalise measure maps to (*.nii, *.nii.gz)",
                                                filetypes=(("Nifti", ".nii"), ("Compressed Nifti", ".nii.gz"), ("All files", "*.*")))
        p = PurePath(file_atlas)
        self.normalise_atlas.config(text=os.path.join('...'+p.anchor,p.name))
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['atlas'] = file_atlas
        
    def select_atlas_mask(self):
        file_atlas_mask = filedialog.askopenfilename(initialdir=str(Path.home()),
                                                title="Select standard atlas mask (*.nii, *.nii.gz)",
                                                filetypes=(("Nifti", ".nii"), ("Compressed Nifti", ".nii.gz"), ("All files", "*.*")))
        p = PurePath(file_atlas_mask)
        self.atlas_mask.config(text=os.path.join('...'+p.anchor,p.name))
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['atlas mask'] = file_atlas_mask
        
    # Submit and close button MUST include checks that each value provided is valid!          
    def save_and_close(self):
        
        settings_error = False
        
        # update dilate
        self.local_data['dilate'] = self.dilate_form.get()
        # update smooth
        self.local_data['smooth'] = self.smooth_form.get()

        # if int(self.local_data['dilate'])%2 != 1 or int(self.local_data['dilate']) < 0:
        #     settings_error = True
        #     messagebox.showerror('Input Error','Dilation value must be a positive, odd integer (no decimals).')
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
            self.local_data['config gui open'] = None
            self.window.destroy()

class guiViewSetup(tk.Toplevel):
    
    def __init__(self, master):
        
        self.master = master
        #super().__init__(self.master) <--- not sure if I need this, it was in some example code
        # self.local_data = root_configure_dict
        
        self.local_data['viewer gui open'] = True
                
        self.window = master
        
        self.gui_viewer_setup_layout()
        
    def gui_viewer_setup_layout(self):
        self.window.title("Select data")
        # self.window.geometry("300x210")
        
        self.window.resizable(False,False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10,pady=5)
        
        # ~~~~~~CONFIGURE GUI OBJECTS (BUTTONS ETC)~~~~~~
        self.data_path = tk.Label(self.frame,
                            text=self.local_data['data select text'],
                            bg="white",
                            width=30,
                            relief="groove",
                            borderwidth=2)
        self.data_select = tk.Button(self.frame,
                              text="Select data folder",
                              command = self.find_data)
        
        self.close_button = tk.Button(self.frame,
                                  text="Submit",
                                  command = self.save_and_close)
        
        # arrange assets
        self.data_path.grid(row=0, column=0, columnspan=3, pady = (5,2), sticky="w")
        self.data_select.grid(row=1, column=0, columnspan=1, sticky="w")

        self.close_button.grid(row=6, column=1, columnspan=1, pady=(8,0), sticky="e")

        # configure the grid
        for r in range(7):
            self.frame.rowconfigure(r, weight=1)
        for c in range(3):
            self.frame.columnconfigure(c, weight=1)

class LogHandler(logging.StreamHandler):
    def __init__(self, textctrl):
        logging.StreamHandler.__init__(self) # initialize parent
        self.textctrl = textctrl
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        self.textctrl.config(state="normal")
        self.textctrl.insert("end", msg + "\n")
        self.textctrl.see("end")
        self.flush()
        self.textctrl.config(state="disabled")

class MainAsyncProcessing(Thread):
    
    def __init__(self, root_data_dict, root_config_dict):
        super().__init__()
        self.running = False
        
        self.local_data = root_data_dict
        self.local_config = root_config_dict
        
    def run(self):
        self.running = True
        mos_analysis_main.main(self.local_data, self.local_config)
        self.running = False

class GroupAsyncProcessing(Thread):
    
    def __init__(self, root_data_dict, root_config_dict):
        super().__init__()
        self.running = False
        
        self.local_data = root_data_dict
        self.config_dict = root_config_dict
        
    def run(self):
        self.running = True
        mos_analysis_group.main(self.local_data, self.config_dict)
        self.running = False

class ViewAsyncProcessing(Thread):
    
    def __init__(self):
        super().__init__()
        self.running = False
        
    def run(self):
        self.running = True
        
        main_logger.info('...Launching MRIcroGL')
        
        mricro_app = resource_path("include/Contents/MacOS/MRIcroGL")
        viewer_launch_script = resource_path("mos_viewer_launch.py")
        
        subprocess.call([mricro_app,'-s',viewer_launch_script])
        
        # mos_analysis_group.main(self.local_data)
        self.running = False

def CenterToWin(window):
    window.wm_withdraw()
    window.update()
    x = window.master.winfo_x()
    y = window.master.winfo_y()
    w = window.winfo_reqwidth()
    h = window.winfo_reqheight()
    total_x = x + (window.master.winfo_width() // 2) - (w // 2)
    total_y = y + (window.master.winfo_height() // 2) - (h // 2)
    window.geometry("%dx%d+%d+%d" % (int(w), int(h), int(total_x), int(total_y)))
    window.wm_deiconify()

def main():
        
    MOS = MOSAICSapp()

    stderrHandler = logging.StreamHandler() # no arguments -> stderr
    main_logger.addHandler(stderrHandler)
    guiHandler = LogHandler(MOS.logger_text)
    main_logger.addHandler(guiHandler)
    main_logger.setLevel(logging.INFO)
    main_logger.info('Welcome to MOSAICS! Messages from the toolbox will be logged here.')
    
    MOS.mainloop()

if __name__ == "__main__":
    main()