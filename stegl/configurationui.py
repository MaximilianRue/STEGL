"""Quick and dirty UI for creating configurations."""

import json
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.messagebox import askyesno, showerror
from pathlib import Path
from tktooltip import ToolTip


DEFAULT_PADDING = 5
DEFAULT_PADDING_HALF = DEFAULT_PADDING / 2.


class PathSelectionWidget(tk.Frame):
    def __init__(
        self, 
        path_variable,
        master=None, 
        label_text=None, 
        open_mode="open_filename",
        file_dialog_text = "Select File",
        filetypes=[("All Files", "*.*")],
        file_dialog_button_text = "Browse..."
    ):
        super().__init__(master=master)
        self.path_variable = path_variable if path_variable is not None else tk.StringVar(self)
        self.open_mode = open_mode
        self.file_dialog_text = file_dialog_text
        self.filetypes = filetypes

        self.columnconfigure(1, weight=1)

        label = tk.Label(self, text=label_text)
        label.grid(row=0, column=0)
        entry = tk.Entry(self, textvariable=self.path_variable)
        entry.grid(row=0, column=1, padx=DEFAULT_PADDING, sticky="EW")
        browse_button = tk.Button(self, text=file_dialog_button_text, command=self.browse)
        browse_button.grid(row=0, column=2)

    def browse(self):
        if self.open_mode == "open_filename":
            file_path = filedialog.askopenfilename(
                title=self.file_dialog_text, 
                filetypes=self.filetypes
            )
        elif self.open_mode == "save_as_filename":
            file_path = filedialog.asksaveasfilename(
                title=self.file_dialog_text, 
                filetypes=self.filetypes
            )
        elif self.open_mode == "open_directory":
            file_path = filedialog.askdirectory(
                title=self.file_dialog_text
            )
        
        if file_path:
            self.path_variable.set(file_path)


class ProcessCaptureDetailsEditor(tk.Toplevel):
    def __init__(self, parent):
        
        super().__init__(parent)
        self.parent = parent
        self.title("Launch Options")
        #self.geometry("300x150")
        self.resizable(True, False)

        self.protocol("WM_DELETE_WINDOW", self.dismiss)

        innerFrame = tk.Frame(self)

        self.path_selector = PathSelectionWidget(
            tk.StringVar(self), innerFrame, "Exe:", file_dialog_button_text="Open")
        ToolTip(self.path_selector, msg="exe_path", delay=1.5)
        self.path_selector.path_variable.set(self.parent.configuration_data["exe_path"].get())
        self.path_selector.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        setting = tk.LabelFrame(innerFrame, text="Comma-separated launch arguments:")
        ToolTip(setting, msg="args", delay=1.5)
        self.arguments_var = tk.StringVar(self, self._arg_list_to_string(parent.configuration_data["args"]))
        self.arguments_field = tk.Entry(setting, textvariable=self.arguments_var)
        self.arguments_field.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        setting.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        setting0 = tk.LabelFrame(innerFrame, text="Max. Launch Waiting Time (seconds):")
        ToolTip(setting0, msg="max_launch_waiting", delay=1.5)
        self.max_launch_waiting_slider = tk.Scale(setting0, from_=0, to=60, orient=tk.HORIZONTAL)
        self.max_launch_waiting_slider.set(parent.configuration_data["max_launch_waiting"])
        self.max_launch_waiting_slider.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        setting0.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        setting1 = tk.LabelFrame(innerFrame, text="Min. Launch Stable Time (seconds):")
        ToolTip(setting1, msg="min_launch_stable", delay=1.5)
        self.min_launch_stable_slider = tk.Scale(setting1, from_=0, to=60, orient=tk.HORIZONTAL)
        self.min_launch_stable_slider.set(parent.configuration_data["min_launch_stable"])
        self.min_launch_stable_slider.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        setting1.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        setting2 = tk.LabelFrame(innerFrame, text="Termination Timeout (seconds):")
        ToolTip(setting2, msg="termination_timeout", delay=1.5)
        self.termination_timeout_slider = tk.Scale(setting2, from_=1, to=60, orient=tk.HORIZONTAL)
        self.termination_timeout_slider.set(parent.configuration_data["termination_timeout"])
        self.termination_timeout_slider.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        setting2.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        setting3 = tk.LabelFrame(innerFrame, text="Max. Termination Retries:")
        ToolTip(setting3, msg="termination_retries", delay=1.5)
        self.termination_retries_slider = tk.Scale(setting3, from_=0, to=10, orient=tk.HORIZONTAL)
        self.termination_retries_slider.set(parent.configuration_data["termination_retries"])
        self.termination_retries_slider.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        setting3.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        tk.Button(innerFrame, text="Save & Close", command=self.save).pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        innerFrame.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        self.wait_visibility()
        self.grab_set()

    def _arg_string_to_list(self, argstr):
        SEPARATOR = "@@STEGL_SEP@@"
        args = argstr.replace("\\\\,", SEPARATOR)
        args = args.split(",")
        args = [a.strip().replace(SEPARATOR, ",") for a in args]
        return args

    def _arg_list_to_string(self, args):
        args = [a.replace(",", "\\\\,") for a in args]
        return ",".join(args)

    def save(self):
        args = self._arg_string_to_list(self.arguments_var.get())
        self.parent.configuration_data["exe_path"].set(self.path_selector.path_variable.get())
        self.parent.configuration_data["args"] = args
        self.parent.configuration_data["max_launch_waiting"] = self.max_launch_waiting_slider.get()
        self.parent.configuration_data["min_launch_stable"] = self.min_launch_stable_slider.get()
        self.parent.configuration_data["termination_timeout"] = self.termination_timeout_slider.get()
        self.parent.configuration_data["termination_retries"] = self.termination_retries_slider.get()
        self.dismiss()

    def dismiss(self):
        self.grab_release()
        self.destroy()


class ProcessCaptureEditor(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.configuration_data = {
            "exe_path": tk.StringVar(self),
            "args": [],
            "max_launch_waiting": 10,
            "min_launch_stable": 3,
            "termination_timeout": 5,
            "termination_retries": 3
        }

        innerFrame = tk.Frame(self)
        innerFrame.columnconfigure(0, weight=1)

        self.path_selector = PathSelectionWidget(
            self.configuration_data["exe_path"],
            innerFrame, "Exe:", file_dialog_button_text="Open"
        )
        self.path_selector.grid(row=0, column=0, padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF, sticky="EW")

        tk.Button(innerFrame, text="Details...", command=self.display_advanced).grid(row=0, column=1, padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        innerFrame.pack(fill="x",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

    def display_advanced(self):
        advanced = ProcessCaptureDetailsEditor(self)
        advanced.wait_window()

    def reset(self):
        self.configuration_data.update({
            "args": [],
            "max_launch_waiting": 10,
            "min_launch_stable": 3,
            "termination_timeout": 5,
            "termination_retries": 3
        })
        self.configuration_data["exe_path"].set("")

    def set_configuration(self, configuration):
        self.configuration_data["exe_path"].set(configuration["exe_path"])
        for key in [
            "args",
            "max_launch_waiting",
            "min_launch_stable",
            "termination_timeout",
            "termination_retries"
        ]:
            self.configuration_data[key] = configuration[key]

    def get_configuration(self):
        config = {}
        config["exe_path"] = self.configuration_data["exe_path"].get()
        for key in [
            "args",
            "max_launch_waiting",
            "min_launch_stable",
            "termination_timeout",
            "termination_retries"
        ]:
            config[key] = self.configuration_data[key]
        return config


class StatusBar(tk.Frame):   
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.variable=tk.StringVar()        
        self.label=tk.Label(self, bd=1, anchor=tk.W,
                           textvariable=self.variable)
        self.variable.set("Ready")
        self.label.pack(fill=tk.X, padx=DEFAULT_PADDING)        
        self.pack()

    def set(self, text):
        self.variable.set(text)


class SteglEditor(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Stegl Editor")
        #self.geometry("400x300+300+120")
        self.option_add('*tearOff', False)
        self.resizable(True, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.iconbitmap("wizard.ico")

        menubar = tk.Menu(self)
        self["menu"] = menubar
        menu_file = tk.Menu(menubar)
        menu_file.add_command(label='New...', command=self.reset_editor)
        menu_file.add_command(label='Load...', command=self.load_config)
        menu_file.add_command(label='Save...', command=self.save_config)
        menubar.add_cascade(menu=menu_file, label="File")
        
        notebook = ttk.Notebook(self)

        game_frame = tk.Frame(self)
        self.game_directory_selector = PathSelectionWidget(
            None, game_frame, open_mode="open_directory", label_text="Game Dir.:"
        )
        ToolTip(self.game_directory_selector, msg="GAME.game_search_paths", delay=1.5)
        self.game_directory_selector.pack(fill="x", padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        self.game_editor = ProcessCaptureEditor(game_frame)
        ToolTip(self.game_editor, msg="GAME.launch_config.exe_path", delay=1.5)
        self.game_editor.pack(fill="x")

        setting0 = tk.LabelFrame(game_frame, text="Game Search Timeout (seconds):")
        ToolTip(setting0, msg="GAME.game_search_timeout", delay=1.5)
        self.game_search_timeout_slider = tk.Scale(setting0, from_=0, to=300, orient=tk.HORIZONTAL)
        self.game_search_timeout_slider.set(60)
        self.game_search_timeout_slider.pack(fill="x", padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        setting0.pack(fill="x", padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        setting1 = tk.LabelFrame(game_frame, text="After Game Wait (seconds):")
        ToolTip(setting1, msg="GAME.after_game_wait", delay=1.5)
        self.after_game_wait_slider = tk.Scale(setting1, from_=0, to=300, orient=tk.HORIZONTAL)
        self.after_game_wait_slider.set(10)
        self.after_game_wait_slider.pack(fill="x", padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)
        setting1.pack(fill="x", padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        notebook.add(game_frame, text="Game")

        self.dependencies = []

        dep_frame = tk.Frame(self)
        tk.Label(dep_frame, text="Dependencies are optional. Leave empty if not needed.").pack(fill="x", padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        self.dep_list = tk.Frame(dep_frame)
        self.dep_list.pack(fill="x")
        dep_tools = tk.Frame(dep_frame)
        tk.Button(dep_tools, text="Remove Dependency", command=self.remove_dependency).pack(side="right",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        tk.Button(dep_tools, text="Add Dependency", command=self.add_dependency).pack(side="right",padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)
        dep_tools.pack(fill="x", padx=DEFAULT_PADDING_HALF, pady=DEFAULT_PADDING_HALF)

        notebook.add(dep_frame, text="Dependencies")
        notebook.pack(fill="x")

        self.status = StatusBar(self)
        self.status.pack(fill="x", pady=DEFAULT_PADDING_HALF)

        # Add one dependency by default
        self.add_dependency()

    def add_dependency(self):
        dep_editor = ProcessCaptureEditor(self.dep_list)
        dep_editor.pack(fill="x")
        self.dependencies.append(dep_editor)

    def remove_dependency(self):
        if len(self.dependencies) > 1:
            self.dependencies[-1].destroy()
            del self.dependencies[-1]

    def on_close(self):
        if askyesno("Confirmation", "Are you sure? Unsaved changes will be lost."):
            self.destroy()

    def reset_editor(self, confirm = True):
        if confirm:
            if not askyesno("Confirmation", "Are you sure? Creating a new config will reset all changes done earlier."):
                return
        for _ in range(len(self.dependencies)-1):
            self.remove_dependency()
        self.dependencies[0].reset()
        self.game_editor.reset()
        self.game_directory_selector.path_variable.set("")
        self.game_search_timeout_slider.set(60)
        self.after_game_wait_slider.set(20)
        self.status.set("Ready")
        
    def load_config(self, confirm=True):
        if confirm:
            if not askyesno("Confirmation", "Are you sure? Loading a config will reset all changes done earlier."):
                return
        filepath = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("Stegl Config", "*.stegl"), ("All Files", "*.*")],
        )
        if filepath:
            filepath = Path(filepath)
            try:
                with filepath.open() as f:
                    config = json.load(f)
                self.reset_editor(confirm=False)
                self.game_editor.set_configuration(config["GAME"]["launch_config"])
                self.game_directory_selector.path_variable.set(config["GAME"]["game_search_paths"][0])
                self.game_search_timeout_slider.set(config["GAME"]["game_search_timeout"])
                self.after_game_wait_slider.set(config["GAME"]["after_game_wait"])
                while len(self.dependencies) < len(config["DEPENDENCIES"]):
                    self.add_dependency()
                for i,d in enumerate(config["DEPENDENCIES"]):
                    self.dependencies[i].set_configuration(d)
            except:
                showerror("Invalid Configuration", "Could not load configuration file.")
                self.status.set("Loading failed.")
                return

        self.status.set("Loaded configuration.")

    def save_config(self):

        filepath = filedialog.asksaveasfilename(
            title="Save Configuration",
            filetypes=[("Stegl Config", "*.stegl")],
        )
        filepath = Path(filepath)
        if filepath.suffix == "":
            filepath = filepath.with_suffix(".stegl")

        configuration = {}
        configuration["GAME"] = {
            "game_search_paths": [self.game_directory_selector.path_variable.get()],
            "game_search_timeout": self.game_search_timeout_slider.get(),
            "after_game_wait": self.after_game_wait_slider.get(),
            "launch_config": self.game_editor.get_configuration()
        }
        configuration["DEPENDENCIES"] = []
        for dep in self.dependencies:
            dep_config = dep.get_configuration()
            if dep_config["exe_path"].strip() == "":
                continue
            else:
                configuration["DEPENDENCIES"].append(dep_config)

        # Do a quick evaluation
        if configuration["GAME"]["game_search_paths"][0].strip() == "":
            showerror("Invalid Configuration", "The game directory must not be empty.")
            self.status.set("Invalid Configuration: Empty game filepath.")
            return

        if configuration["GAME"]["launch_config"]["exe_path"].strip() == "":
            showerror("Invalid Configuration", "The exe filepath must not be empty.")
            self.status.set("Invalid Configuration: Empty game filepath.")
            return

        try:
            with Path(filepath).open("w+") as f:
                json.dump(configuration, f, indent=4)
        except:
            showerror("Error", "Could not save configuration file. Please retry.")
            self.status.set("Attention: Config was not saved!")
            return

        self.status.set("Configuration saved.")


def launch():
    SteglEditor().mainloop()