"""Tk window to edit parameters, run the simulation and plot the trajectories."""
from __future__ import annotations

import tkinter as tk
from dataclasses import fields
from tkinter import filedialog, ttk

from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from ballsim.parameters import GRAVITY_MODELS, INTEGRATOR_NAMES, TEXT_FIELDS, Parameters, validate
from ballsim.plotting import add_trajectory, make_axes
from ballsim.presets import load_preset, save_preset
from ballsim.simulation import describe, run as run_simulation

CHOICES = {"gravity_model": GRAVITY_MODELS, "integrator": INTEGRATOR_NAMES}
JSON_TYPES = [("Preset", "*.json")]
UNITS = {
    "mass": "kg", "radius": "m", "fluid_density": "kg/m^3", "g": "m/s^2",
    "G": "m^3/(kg s^2)", "M": "kg", "R": "m", "initial_height": "m",
    "initial_velocity": "m/s", "finish_time": "s", "time_step": "s",
}


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Ball drop simulation")
        self.window: tk.Toplevel | None = None
        self.fig: Figure | None = None
        self.canvas: FigureCanvasTkAgg | None = None
        self.axes: list[Axes] = []
        self.anim_window: tk.Toplevel | None = None
        self.anim_canvas: FigureCanvasTkAgg | None = None
        self.animator = None

        form = ttk.Frame(root, padding=8)
        form.pack()
        self.vars: dict[str, tk.StringVar] = {}
        for row, field in enumerate(fields(Parameters)):
            var = tk.StringVar()
            self.vars[field.name] = var
            text = f"{field.name} [{UNITS[field.name]}]" if field.name in UNITS else field.name
            ttk.Label(form, text=text).grid(row=row, column=0, sticky="w")
            if field.name in CHOICES:
                widget = ttk.Combobox(
                    form, textvariable=var, values=CHOICES[field.name],
                    state="readonly",
                )
            else:
                widget = ttk.Entry(form, textvariable=var)
            widget.grid(row=row, column=1)
        self.set_fields(Parameters())

        buttons = ttk.Frame(root, padding=8)
        buttons.pack()
        ttk.Button(buttons, text="Load preset", command=self.load).pack(side="left")
        ttk.Button(buttons, text="Save preset", command=self.save).pack(side="left")
        ttk.Button(buttons, text="Run", command=self.run).pack(side="left")
        ttk.Button(buttons, text="Animate", command=self.animate).pack(side="left")
        ttk.Button(buttons, text="Clear plots", command=self.clear).pack(side="left")

        self.keep = tk.BooleanVar(value=True)
        ttk.Checkbutton(root, text="Keep previous runs", variable=self.keep).pack()
        self.status = tk.StringVar()
        ttk.Label(root, textvariable=self.status, wraplength=400).pack(padx=8, pady=8)

    def set_fields(self, params: Parameters) -> None:
        """Show every parameter in its entry."""
        for field in fields(Parameters):
            self.vars[field.name].set(str(getattr(params, field.name)))

    def read_fields(self) -> Parameters:
        """Turn the entry texts into Parameters. Run validates the values."""
        values = {}
        for field in fields(Parameters):
            text = self.vars[field.name].get()
            if field.name not in TEXT_FIELDS:
                try:
                    values[field.name] = float(text)
                except ValueError:
                    raise ValueError(f"{field.name} must be a number, got '{text}'")
            else:
                values[field.name] = text
        return Parameters(**values)

    def load(self) -> None:
        path = filedialog.askopenfilename(filetypes=JSON_TYPES)
        if not path:
            return
        try:
            self.set_fields(load_preset(path))
        except (OSError, ValueError) as error:
            self.status.set(str(error))
            return
        self.status.set(f"Loaded {path}")

    def save(self) -> None:
        try:
            params = self.read_fields()
            validate(params)
        except ValueError as error:
            self.status.set(str(error))
            return
        path = filedialog.asksaveasfilename(filetypes=JSON_TYPES, defaultextension=".json")
        if not path:
            return
        try:
            save_preset(params, path)
        except (OSError, ValueError) as error:
            self.status.set(str(error))
            return
        self.status.set(f"Saved {path}")

    def plot_window_axes(self) -> list[Axes]:
        """Return the plot axes. Open the plot window first if it is missing or closed."""
        if self.window is None or not self.window.winfo_exists():
            self.window = tk.Toplevel(self.root)
            self.window.title("Trajectories")
            self.fig = Figure(figsize=(7, 7))
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
            NavigationToolbar2Tk(self.canvas, self.window)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            self.axes = make_axes(self.fig)
        return self.axes

    def run(self) -> None:
        try:
            trajectory = run_simulation(self.read_fields())
        except ValueError as error:
            self.status.set(str(error))
            return
        if not self.keep.get():
            self.clear()
        add_trajectory(self.plot_window_axes(), trajectory)
        self.canvas.draw()
        self.status.set(describe(trajectory))

    def animate(self) -> None:
        """Play one run as an animation in its own window, reusing the window."""
        try:
            from extras import animate as animation  # optional extra, the core does not need it
        except ModuleNotFoundError:
            self.status.set("animation extra not found")
            return
        try:
            params = self.read_fields()
            validate(params)
        except ValueError as error:
            self.status.set(str(error))
            return
        if self.anim_window is None or not self.anim_window.winfo_exists():
            self.anim_window = tk.Toplevel(self.root)
            self.anim_window.title("Animation")
            self.anim_window.protocol("WM_DELETE_WINDOW", self.close_animation)
        else:
            self.animator.stop()
            # the old canvas still holds the old animator's mouse and key handlers
            self.anim_canvas.get_tk_widget().destroy()
        fig = Figure(figsize=(13, 8))
        self.anim_canvas = FigureCanvasTkAgg(fig, master=self.anim_window)
        self.anim_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.animator = animation.Animator(fig, params)
        self.anim_canvas.draw()
        self.anim_canvas.get_tk_widget().focus_set()  # key presses need focus
        self.status.set(f"Animating {params.name}")

    def close_animation(self) -> None:
        """Stop the timer first so it does not draw into a destroyed window."""
        self.animator.stop()
        self.anim_window.destroy()

    def clear(self) -> None:
        self.plot_window_axes()
        self.fig.clear()
        self.axes = make_axes(self.fig)
        self.canvas.draw()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()

