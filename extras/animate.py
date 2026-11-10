"""Animation of one run: a falling ball with live graphs and numbers."""
from __future__ import annotations

import argparse
import dataclasses
import math
import textwrap
import time

import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch
from matplotlib.widgets import Button, Slider

from ballsim.parameters import Parameters
from ballsim.plotting import make_axes
from ballsim.presets import load_preset
from ballsim.simulation import Trajectory, describe, run
from extras.quantities import Quantities, compute

FPS = 30
TARGET_PLAYBACK = 10.0  # s, every run plays in this time


def values_at(trajectory: Trajectory, quantities: Quantities, t: float) -> dict[str, float]:
    """Interpolate every displayed value at time t so frames between samples are smooth."""
    arrays = {"x": trajectory.x, "v": trajectory.v, "a": trajectory.a}
    for field in dataclasses.fields(quantities):
        arrays[field.name] = getattr(quantities, field.name)
    values = {name: float(np.interp(t, trajectory.t, y)) for name, y in arrays.items()}
    values["t"] = float(t)
    return values


def format_readout(values: dict[str, float]) -> str:
    """Lay the numbers out as aligned monospace lines with units."""
    v = values
    terminal = v["terminal_speed"]
    if math.isnan(terminal):
        terminal_text, ratio_text = "none (no drag)", "none"
    else:
        terminal_text = f"{terminal:10.4g} m/s"
        ratio_text = f"{abs(v['drag']) / abs(v['weight']):10.4g}" if v["weight"] else "none"
    lines = [
        f"t  {v['t']:8.2f} s",
        f"height        {v['x']:10.4g} m",
        f"velocity      {v['v']:10.4g} m/s",
        f"acceleration  {v['a']:10.4g} m/s^2",
        f"drag          {v['drag']:10.4g} N",
        f"weight        {v['weight']:10.4g} N",
        f"net           {v['net']:10.4g} N",
        f"terminal vel. {terminal_text}",
        f"drag/weight   {ratio_text}",
        f"kinetic       {v['kinetic']:10.4g} J",
        f"potential     {v['potential']:10.4g} J",
        f"lost to drag  {v['lost']:10.4g} J",
        f"numeric error {v['error']:10.4g} J",
    ]
    return "\n".join(lines)


def padded_limits(data: np.ndarray) -> tuple[float, float]:
    """Axis limits for the whole run with a 5% margin, never zero height."""
    lo, hi = float(np.nanmin(data)), float(np.nanmax(data))
    pad = 0.05 * (hi - lo) if hi > lo else 1.0
    return lo - pad, hi + pad


class Animator:
    """Owns the figure of one animated run and redraws it for any time t."""

    def __init__(self, fig: Figure, params: Parameters) -> None:
        self.fig = fig
        self.trajectory = run(params)
        self.quantities = compute(params, self.trajectory)
        self.t_end = float(self.trajectory.t[-1])
        # bottom margin 0.17 leaves a strip for the controls
        grid = fig.add_gridspec(
            1, 3, width_ratios=[1, 2.2, 1.4], left=0.07, right=0.97, bottom=0.17, top=0.95,
            wspace=0.12,
        )
        self.build_ball_axis(fig.add_subplot(grid[0, 0]))
        self.build_graphs(fig.add_subfigure(grid[0, 1]))
        self.readout_ax = fig.add_subplot(grid[0, 2])
        self.readout_ax.axis("off")
        self.readout = self.readout_ax.text(
            0.0, 1.0, "", family="monospace", fontsize=9, va="top",
            transform=self.readout_ax.transAxes,
        )
        self.time = 0.0
        self.last_tick: float | None = None  # wall clock of the previous tick, None = restart the clock
        self.playing = True
        self.build_controls()
        self.draw_frame(0.0)
        # FuncAnimation is the timer: it calls step() FPS times a second once the canvas shows
        # init_func stops the first draw_event calling step(), which would use up the clock start
        self.animation = FuncAnimation(
            fig, self.step, init_func=lambda: [], interval=1000 / FPS,
            cache_frame_data=False,
        )

    def build_ball_axis(self, ax: Axes) -> None:
        """Set up the tall left axis with ground, ball, force arrows and end banner."""
        self.ball_ax = ax
        self.top = float(np.max(self.trajectory.x)) * 1.05
        ax.set_xlim(-1, 1)
        ax.set_ylim(-0.2 * self.top, self.top)  # the band below 0 is the ground
        ax.set_xticks([])
        ax.set_yticks([t for t in ax.get_yticks() if t >= 0])  # no tick labels inside the ground band
        ax.set_ylim(-0.2 * self.top, self.top)
        ax.set_ylabel("Height [m]")
        ax.axhspan(-0.2 * self.top, 0, color="0.85")
        ax.axhline(0, color="black", linewidth=2)
        ax.text(0.55, -0.1 * self.top, "ground", ha="center", va="center", fontsize=8)
        self.ball = ax.plot([0], [self.trajectory.x[0]], "o", markersize=14, color="tab:green")[0]
        # zero weight (g = 0) would divide by zero, so fall back to the largest drag, then to 1 N
        reference = abs(self.quantities.weight[0]) or float(np.max(np.abs(self.quantities.drag))) or 1.0
        self.n_per_m = reference / (0.15 * self.top)  # N per metre of arrow
        self.drag_arrow = self.make_arrow("tab:blue")
        self.weight_arrow = self.make_arrow("tab:red")
        ax.text(-0.95, self.top * 0.97, "drag (up)", color="tab:blue", fontsize=9, va="top")
        ax.text(-0.95, self.top * 0.93, "weight (down)", color="tab:red", fontsize=9, va="top")
        self.banner = ax.text(
            0.0, self.top * 0.5, textwrap.fill(describe(self.trajectory), width=24),
            ha="center", va="center", fontsize=9,
            bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": "gray"},
        )

    def make_arrow(self, color: str) -> FancyArrowPatch:
        """Add one force arrow to the ball axis, positioned later by draw_frame."""
        arrow = FancyArrowPatch(
            (0, 0), (0, 0), arrowstyle="-|>", mutation_scale=15, color=color, linewidth=2
        )
        self.ball_ax.add_patch(arrow)
        return arrow

    def build_graphs(self, subfig: Figure) -> None:
        """Make the three shared graphs with fixed full-run limits, lines grow later."""
        traj, q = self.trajectory, self.quantities
        axes = make_axes(subfig)
        subfig.subplots_adjust(left=0.27, right=0.97, bottom=0.12, top=0.98, hspace=0.12)
        self.graph_lines, self.graph_dots = [], []
        for ax, data in zip(axes, (traj.x, traj.v, traj.a)):
            ax.set_xlim(0, self.t_end)
            ax.set_ylim(*padded_limits(data))
            ax.grid(alpha=0.3)
            self.graph_lines.append(ax.plot([], [], color="tab:blue")[0])
            self.graph_dots.append(ax.plot([], [], "o", color="tab:red")[0])
        vel_ax = axes[1]
        # skip the terminal line when it lies off the velocity scale, the readout still shows it
        has_terminal = not np.all(np.isnan(q.terminal_speed))  # no drag gives all nan
        if has_terminal and np.nanmin(-q.terminal_speed) >= vel_ax.get_ylim()[0]:
            vel_ax.plot(traj.t, -q.terminal_speed, "--", color="gray", label="terminal velocity")
            vel_ax.legend(loc="center right", fontsize=8)

    def set_graphs(self, t: float, v: dict[str, float]) -> None:
        """Grow each line up to t and move its dot to the interpolated value."""
        traj = self.trajectory
        n = int(np.searchsorted(traj.t, t, side="right"))
        keys = ("x", "v", "a")
        series = (traj.x, traj.v, traj.a)
        for line, dot, data, key in zip(self.graph_lines, self.graph_dots, series, keys):
            line.set_data(np.append(traj.t[:n], t), np.append(data[:n], v[key]))
            dot.set_data([t], [v[key]])

    def draw_frame(self, t: float) -> None:
        """Update every artist for time t. The caller redraws the canvas."""
        v = values_at(self.trajectory, self.quantities, t)
        x = v["x"]
        self.ball.set_data([0], [x])
        for arrow, force in ((self.drag_arrow, v["drag"]), (self.weight_arrow, v["weight"])):
            arrow.set_positions((0, x), (0, x + force / self.n_per_m))
        self.set_graphs(t, v)
        self.readout.set_text(format_readout(v))
        self.banner.set_visible(t >= self.t_end)

    def build_controls(self) -> None:
        """Add the Pause button and the time scrubber in the bottom strip."""
        fig = self.fig
        self.pause_button = Button(fig.add_axes((0.07, 0.085, 0.08, 0.05)), "Pause")
        self.scrubber = Slider(
            fig.add_axes((0.15, 0.025, 0.75, 0.04)), "Time", 0, self.t_end, valinit=0.0,
            valfmt="%.2f s",
        )
        self.pause_button.on_clicked(lambda event: self.toggle_pause())
        self.scrubber.on_changed(self.on_scrub)

    def step(self, frame: int) -> None:
        """Timer tick: advance the clock and move the scrubber while playing."""
        if not self.playing:
            return
        now = time.perf_counter()
        if self.last_tick is None:  # first tick after a start or resume only starts the clock
            self.last_tick = now
            return
        elapsed = min(now - self.last_tick, 0.25)  # cap: a stall must not cause a jump
        self.last_tick = now
        # real elapsed time, not 1/FPS: a slow redraw would otherwise slow the playback
        t = min(self.time + self.t_end / TARGET_PLAYBACK * elapsed, self.t_end)
        self.scrubber.set_val(t)  # on_scrub does the redraw
        if t >= self.t_end:
            self.set_playing(False)

    def set_playing(self, playing: bool) -> None:
        """Start or stop playback; a stopped timer saves CPU and a new start resets the clock."""
        self.playing = playing
        self.last_tick = None
        self.pause_button.label.set_text("Pause" if playing else "Resume")
        if playing:
            self.animation.resume()
        else:
            self.animation.pause()
        self.fig.canvas.draw_idle()

    def toggle_pause(self) -> None:
        """Pause or resume. Pressing it at the end of the run starts again."""
        if self.time >= self.t_end:
            self.scrubber.set_val(0.0)
            self.set_playing(True)
        else:
            self.set_playing(not self.playing)

    def on_scrub(self, val: float) -> None:
        """Slider callback and the only redraw path: show the chosen time."""
        self.time = float(val)
        self.draw_frame(self.time)

    def stop(self) -> None:
        """Stop the timer before the window is reused or closed."""
        self.animation.event_source.stop()


def main(argv: list[str] | None = None) -> None:
    """Open the animation window for one preset file."""
    parser = argparse.ArgumentParser(prog="extras.animate", description="Animate one run.")
    parser.add_argument("preset", help="preset JSON file to animate")
    args = parser.parse_args(argv)
    try:
        params = load_preset(args.preset)
    except (OSError, ValueError) as error:
        raise SystemExit(f"animate: {error}")
    import matplotlib.pyplot as plt  # only the CLI needs pyplot, the Animator does not

    fig = plt.figure(figsize=(13, 8))
    animator = Animator(fig, params)  # keep a reference or the timer and widgets die
    plt.show()


if __name__ == "__main__":
    main()
