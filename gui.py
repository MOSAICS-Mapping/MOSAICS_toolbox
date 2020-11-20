import pygame as pg
import tkinter as tk
from tkinter import filedialog, Text
import os


frame = tk.Tk()
frame.title("MOSAICS 2020")
frame.configure(background="#00FFFF")
frame.geometry("500x500")

def select_brain():
    brain_file = filedialog.askopenfile(initialdir="/", title="Select Brain",
                                      filetypes=(("Brain", ".nii"), ("All Files", "*.*")))

def select_coordinates():
    coordinates = filedialog.askopenfile(initialdir="/", title="Select Coordinates",
                                      filetypes=(("Coordinates", ".xlsx"), ("All Files", "*.*")))

def process_display():
    pass


background = tk.Frame(frame, bg="red")
background.place(relwidth=0.8, relheight=0.8, relx=0.1, rely=0.1)


select_brain_button = tk.Button(frame, text="Upload a Brain", padx=15,
                        pady=5, fg="black", bg="white", command=select_brain)

select_brain_button.place(relx = 0.1, rely = 0.0)

select_coordinates_button = tk.Button(frame, text="Upload the coordinates", padx=15,
                        pady=5, fg="black", bg="white", command=select_coordinates)

select_coordinates_button.place(relx=0.335, rely=0.0)

proceed_and_display = tk.Button(frame, text = "Proceed and Display", padx = 15,
                        pady = 5, fg = "black", bg = "white", command = process_display)

proceed_and_display.place(relx = 0.665, rely = 0.0)


frame.mainloop()