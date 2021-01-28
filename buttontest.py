#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    To add:
        - Don't update file paths unless a new file is chosen when user clicks button
"""

import tkinter as tk
import tkinter.filedialog as filedialog
from pathlib import PurePath    

# Declare global variables
nii_file = str()
stim_file = str()
save_name = str(' ')

def pick_t1():
    global nii_file
    nii_file = filedialog.askopenfilename(initialdir="~/",
                                      title="Select a t1 file (.nii, .nii.gz)",
                                      filetypes=(("Nifti", ".nii"), ("Compressed Nifti", ".nii.gz"), ("All files", "*.*")))
    p = PurePath(nii_file)
    path_t1.config(text=p.anchor+'...'+p.name)

def pick_stim_data():
    global stim_file
    stim_file = filedialog.askopenfilename(initialdir="~/",
                                      title="Select stimulation data",
                                      filetypes=(("Coordinates", ".xlsx"), ("All files", "*.*")))
    p = PurePath(stim_file)
    path_stim.config(text=p.anchor+'...'+p.name)
    
# def update_save_name():
#     global save_name
#     save_name = enter_save_name.get()
#     print("new save name = "+save_name)

def save_and_close():
    print('closing!')
    print(enter_save_name.get())

root = tk.Tk()
root.resizable(False,False)

root.title("Button test")
root.geometry("300x205")

frame = tk.Frame()
frame.pack(padx=10, pady=5)

path_t1 = tk.Label(frame,
                   text="No image specified",
                   bg="white",
                   width=30,
                   relief="groove",
                   borderwidth=2)
select_t1 = tk.Button(frame,
                      text="Select structural image",
                      command = pick_t1)
path_stim = tk.Label(frame,
                   text="No stimulation data specified",
                   bg="white",
                   width=30,
                   relief="groove",
                   borderwidth=2)
select_stim = tk.Button(frame,
                        text="Select stimulation data file",
                        command = pick_stim_data)

# Not working in the GUI yet
list_save_name = tk.Label(frame,
                          text="Enter save name below:")

enter_save_name = tk.Entry(frame,
                            relief="groove")

close_button = tk.Button(frame,
                         text="OK",
                         command = save_and_close)

# # configure the grid
# frame.columnconfigure((0,1,2), weight=0)
# frame.rowconfigure((0,1,2,3,4,5,6), weight=0)

# arrange assets
path_t1.grid(row=0, pady = 2, columnspan=3)
select_t1.grid(row=1, column=0, sticky="w")
path_stim.grid(row=2, pady = 4, columnspan=3)
select_stim.grid(row=3, column=0, sticky="w")

list_save_name.grid(row=4, columnspan=1, sticky="w")
enter_save_name.grid(row=5, columnspan=2, sticky="w")

close_button.grid(row=6, column=2, sticky="e")

frame.mainloop()