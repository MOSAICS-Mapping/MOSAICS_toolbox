#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 13:36:20 2021

@author: Bryce
"""

import tkinter as tk
import tkinter.filedialog as filedialog
from PIL import ImageTk
from pathlib import PurePath
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MOSAICSapp(tk.Tk):
    
    def __init__(self):
        tk.Tk.__init__(self)
        
        # ~~~~~~Configure GUI appearance~~~~~~
        self.title("MOSAICS Toolbox")
        self.geometry("800x512")
        self.resizable(False,False)
        
        self.buttons = tk.Frame(self, bg="blue")
        self.logo = tk.Frame(self, bg="red")
        
        self.buttons.pack(side=tk.LEFT, expand=False, fill=tk.BOTH)
        self.logo.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        global img
        scripts_path = "/Users/Bryce/Desktop/Postdoc_Scripts/GitHub/04_mosaics_2020/"
        background_image = scripts_path+"1_crop.png"
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
                                              command=self.print_selected_vars)
        self.button_configure_analysis.grid(row=2,pady=10)
        
        # MOSIACS analysis button
        self.button_analysis = tk.Button(self.buttons,text = "MOSAICS analysis",padx=15,pady=5,
                                        command=print)# call_mosaics
        self.button_analysis.grid(row=3,pady=10)
        
        self.button_close = tk.Button(self.buttons, text="Close GUI",padx=15,pady=5,
                                 command=self.close_gui)#close_gui)
        self.button_close.grid(row=4,pady=10)
        
        # center buttons with empty top and bottom rows that are greedy for space.
        self.buttons.grid_rowconfigure(0, weight=1)
        self.buttons.grid_rowconfigure(4, weight=1)
        
        # ~~~~~~Initialize global variables~~~~~~
        # self.gui_select_open = tk.BooleanVar()
        self.gui_select_open = False
        self.path_nii_file = ''
        
        self.data_dict = dict()
        
        # self.path_stim_file = tk.StringVar()
        # self.save_name = tk.StringVar()
        
    # ~~~~~~Create methods for MOSAICS function~~~~~~
    def call_gui_select(self):
        # check if window is open, if it's not open it!
        if self.gui_select_open:
            logging.error('Cannot open selection dialogue, dialogue already exists!')
        elif self.gui_select_open == False:
            gui_select = guiSelect(self, self.data_dict)

    def print_selected_vars(self):
        print('nii file picked: '+str(self.data_dict['image']))
        print('stim file picked: '+str(self.data_dict['stim']))
        print('save name picked: '+str(self.data_dict['save_prefix']))

    # def update_file_nii(self, filename):
    #     self.path_nii_file = filename
    #     print('nii file name in root GUI set to: '+self.data_dict['image'])

    def close_gui(self):
        self.destroy()

class guiSelect(tk.Toplevel):
    
    def __init__(self, master, root_data_dict):
        self.master = master
        #super().__init__(self.master) <--- not sure if I need this, it was in some example code
        self.local_data = root_data_dict
                
        self.window = tk.Toplevel(master)
        self.window.title("Select data")
        self.window.geometry("300x220")
        self.window.resizable(False,False)
        self.frame = tk.Frame(self.window)
        self.frame.pack(padx=10, pady=5)
        
        # ~~~~~~Setup selection buttons and sane name entry field~~~~~~
        self.path_t1 = tk.Label(self.frame,
                            text="No image specified",
                            bg="white",
                            width=30,
                            relief="groove",
                            borderwidth=2)
        self.select_t1 = tk.Button(self.frame,
                              text="Select structural image (*.nii(.gz))",
                              command = self.pick_t1)
        self.path_stim = tk.Label(self.frame,
                            text="No stimulation data specified",
                            bg="white",
                            width=30,
                            relief="groove",
                            borderwidth=2)
        self.select_stim = tk.Button(self.frame,
                                text="Select stimulation data file (*.xls(x))",
                                command = self.pick_stim_data)
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
        self.path_t1.grid(row=0, pady = 2, columnspan=3)
        self.select_t1.grid(row=1, column=0, sticky="w")
        self.path_stim.grid(row=2, pady = 4, columnspan=3)
        self.select_stim.grid(row=3, column=0, sticky="w")
        self.list_save_name.grid(row=4, columnspan=1, sticky="w")
        self.enter_save_name.grid(row=5, columnspan=2, sticky="w")
        self.close_button.grid(row=6, column=2, sticky="e")

    def pick_t1(self):
        file_nii = filedialog.askopenfilename(initialdir="~/",
                                          title="Select a t1 file (.nii, .nii.gz)",
                                          filetypes=(("Nifti", ".nii"), ("Compressed Nifti", ".nii.gz"), ("All files", "*.*")))
        p = PurePath(file_nii)
        # update the text field to reflect user chosen file
        self.path_t1.config(text=p.anchor+'...'+p.name)
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['image'] = file_nii
    
    def pick_stim_data(self):
        file_stim = filedialog.askopenfilename(initialdir="~/",
                                          title="Select stimulation data",
                                          filetypes=(("Coordinates", ".xlsx"), ("All files", "*.*")))
        p = PurePath(file_stim)
        # update the text field to reflect user chosen file
        self.path_stim.config(text=p.anchor+'...'+p.name)
        
        # bring this value back to the main GUI right away, so it's not lost due to scope
        self.local_data['stim'] = file_stim
    
    # button to close gui
    def save_and_close(self):
        """
        Bring in checks for variables
        # check if returned input is valid
        """
        # global save_prefix
        # #save_prefix = self.enter_save_name.get()
        # global file_nii
        # global file_stim

        # self.window.destroy()
        # global gui_select_open
        # gui_select_open = 0
        # return

        # self.gui_select_open.set(False)
        # self.save_name = self.enter_save_name.get()
        # logging.info('save name set to '+self.save_name)
        
        self.local_data['save_prefix'] = self.enter_save_name.get()

def main():
    MOS = MOSAICSapp()
    MOS.mainloop()

if __name__ == "__main__":
    main()