#! /usr/bin/env python
# -*- coding: utf-8 -*-

try:
  # Python 3:
  import tkinter as tk
  from tkinter import filedialog, Label, ttk, messagebox
except ImportError:
  # Python 2:
  import Tkinter as tk
  from Tkinter import Label
  import tkFileDialog as filedialog
  import tkMessageBox as messagebox
  import ttk

import del2rpp
import os
import traceback
import types


class Args:
  pass


class Application(tk.Frame):

  def __init__(self, master=None):
    tk.Frame.__init__(self, master, padx=15, pady=15)

    self.master = master
    self.master.title("del2rpp")
    self.master.resizable(False, False)

    self.args = Args()
    self.args.input_file = None
    self.args.output_file = None
    self.pack()
    self.create_widgets()

  def create_widgets(self):
    frame1 = tk.Frame(self)
    frame2 = tk.Frame(self)

    frame1.pack(side='top', fill='both', expand=True)
    ttk.Separator(
        self, orient='horizontal').pack(
            side='top', fill='x', padx=0, pady=15)
    frame2.pack(side='top', fill='both', expand=True)

    self.input_label = Label(
        frame1, text="Input Deluge song file: ", justify=tk.LEFT, anchor=tk.W)
    self.input_label.grid(column=0, row=0, sticky=tk.W, padx=5, pady=(0, 2))
    self.output_label = Label(
        frame1,
        text="Output REAPER project file: ",
        justify=tk.LEFT,
        anchor=tk.W)
    self.output_label.grid(column=0, row=1, sticky=tk.W, padx=5, pady=(2, 0))

    self.input_path_label = Label(frame1, justify=tk.LEFT, anchor=tk.W)
    self.input_path_label.grid(column=1, row=0, sticky=tk.W)
    self.output_path_label = Label(frame1, justify=tk.LEFT, anchor=tk.W)
    self.output_path_label.grid(column=1, row=1, sticky=tk.W)

    self.open_song_button = tk.Button(frame2)
    self.open_song_button["text"] = "Open Deluge song"
    self.open_song_button["command"] = self.open_song
    self.open_song_button.grid(column=0, row=0, padx=20)

    self.convert_button = tk.Button(frame2)
    self.convert_button["text"] = "Convert to REPAER project"
    self.convert_button["command"] = self.convert
    self.convert_button.grid(column=1, row=0, padx=20)

    frame2.grid_columnconfigure(0, weight=1)
    frame2.grid_columnconfigure(4, weight=1)

    self.update()

  def open_song(self):
    self.args.input_file = filedialog.askopenfile(
        mode="r",
        parent=self,
        title="Select a Deluge song to open",
        filetypes=[("Deluge song", "*.XML")])
    # Reset output file.
    self.args.output_file = None
    self.update()

  def convert(self):
    initial_file_name = os.path.splitext(
        os.path.basename(self.args.input_file.name))[0] + ".rpp"

    self.args.output_file = filedialog.asksaveasfile(
        mode="w",
        parent=self,
        title="Save converted REAPER project",
        initialfile=initial_file_name,
        filetypes=[("REAPER project", "*.rpp")])
    self.update()

    if self.args.output_file == None:
      return

    try:
      del2rpp.convert(self.args)
    except Exception as e:
      tb = traceback.format_exc()
      messagebox.showerror(
          "Error converting to REAPER project",
          "Please file an issue on the del2rpp GitHub.\n\nError:\n" + str(e) +
          "\n\n" + tb)

    self.args.output_file.close()

  def update(self):
    input_path = "<none>"
    if self.args.input_file:
      input_path = self.args.input_file.name
    self.input_path_label.config(text=input_path)

    output_path = "<none>"
    if self.args.output_file:
      output_path = self.args.output_file.name
    self.output_path_label.config(text=output_path)

    self.convert_button[
        "state"] = "normal" if self.args.input_file else "disabled"


root = tk.Tk()

app = Application(master=root)
app.mainloop()
