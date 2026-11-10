"""Plot trajectories on a Figure. No pyplot, so the GUI can embed the Figure."""
from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ballsim.simulation import Trajectory


def make_axes(fig: Figure) -> list[Axes]:
    """Three stacked plots (height, velocity, acceleration) that share the time axis."""
    axes = list(fig.subplots(3, 1, sharex=True))
    axes[0].set_ylabel("Height x [m]")
    axes[1].set_ylabel("Velocity v [m/s]")
    axes[2].set_ylabel("Acceleration a [m/s^2]")
    axes[2].set_xlabel("Time t [s]")
    return axes


def add_trajectory(axes: list[Axes], trajectory: Trajectory) -> None:
    """Draw one run on all three axes in one colour, with a dashed line at impact."""
    label = trajectory.label()
    colour = axes[0].plot(trajectory.t, trajectory.x, label=label)[0].get_color()
    axes[1].plot(trajectory.t, trajectory.v, label=label, color=colour)
    axes[2].plot(trajectory.t, trajectory.a, label=label, color=colour)
    if trajectory.impact_time is not None:
        for ax in axes:
            ax.axvline(trajectory.impact_time, linestyle="--", color=colour)
    axes[0].legend()
