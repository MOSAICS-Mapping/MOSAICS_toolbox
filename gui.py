import pygame as pg
import tkinter as tk
from tkinter import filedialog, Text
import os
from tkinter import *
from PIL import ImageTk, Image


frame = tk.Tk()
frame.title("MOSAICS 2020")
img = ImageTk.PhotoImage(Image.open("1.png"))
panel = Label(frame,image = img)
#frame.configure(background="#00FFFF")
frame.geometry("600x550")

def select_brain():
    brain_file = filedialog.askopenfile(initialdir="/", title="Select Brain",
                                      filetypes=(("Brain", ".nii"), ("All Files", "*.*")))

def select_coordinates():
    coordinates = filedialog.askopenfile(initialdir="/", title="Select Coordinates",
                                      filetypes=(("Coordinates", ".xlsx"), ("All Files", "*.*")))

def Mosaics():
    pass


#background = tk.Frame(frame, bg="red")
#background.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)

panel.pack(side = "bottom", fill = "both", expand = "no")

select_brain_button = tk.Button(frame, text="Upload a Brain", padx=15,
                        pady=5, fg="black", bg="white", command=select_brain)

select_brain_button.place(relx = 0.2, rely = 0.0)

select_coordinates_button = tk.Button(frame, text="Upload the coordinates", padx=15,
                        pady=5, fg="black", bg="white", command=select_coordinates)

select_coordinates_button.place(relx=0.4, rely=0.0)

proceed_and_display = tk.Button(frame, text = "MOSAICS", padx = 15,
                        pady = 5, fg = "black", bg = "white", command = Mosaics)

proceed_and_display.place(relx = 0.675, rely = 0.0)


frame.mainloop()