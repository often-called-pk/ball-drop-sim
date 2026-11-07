"""Physics values for the animation display, computed from a finished run."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ballsim.parameters import Ball, Parameters, State
from ballsim.simulation import Trajectory, make_forces


@dataclass
class Quantities:
    """One array per displayed value, same length as the trajectory."""

    drag: np.ndarray  # N, sign along height axis (up +)
    weight: np.ndarray  # N, negative
    net: np.ndarray  # drag + weight
    terminal_speed: np.ndarray  # m/s, local, nan when no drag
    kinetic: np.ndarray  # J
    potential: np.ndarray  # J, zero at ground
    lost: np.ndarray  # J removed by drag so far, >= 0, starts 0
    error: np.ndarray  # start energy - (kinetic + potential + lost)


def potential_energy(params: Parameters, height: np.ndarray) -> np.ndarray:
    """Potential energy per gravity model, zero at the ground."""
    if params.gravity_model == "constant":
        return params.mass * params.g * height
    if params.gravity_model == "newtonian":
        gm = params.G * params.M * params.mass
        return gm * (1 / params.R - 1 / (params.R + height))
    raise ValueError(f"no potential energy for gravity model {params.gravity_model!r}")


def compute(params: Parameters, trajectory: Trajectory) -> Quantities:
    """Derive forces and energies for every sample so the display needs no physics."""
    t, x, v = trajectory.t, trajectory.x, trajectory.v
    ball = Ball(params.mass, params.radius)
    gravity, drag_force = make_forces(params)
    # force classes use plain arithmetic, so they accept numpy arrays
    state = State(x, v)
    weight = np.broadcast_to(gravity.force(state, ball), x.shape).astype(float)
    drag = np.broadcast_to(drag_force.force(state, ball), x.shape).astype(float)

    # drag = -k v|v|, as QuadraticDrag
    k = params.drag_coefficient * params.fluid_density * math.pi * params.radius**2
    if k > 0:
        terminal = np.sqrt(np.abs(weight) / k)
    else:
        terminal = np.full_like(x, np.nan)

    kinetic = 0.5 * params.mass * v**2
    potential = potential_energy(params, x)
    power = drag * v  # <= 0, drag only removes energy
    lost = np.zeros_like(x)
    lost[1:] = -np.cumsum(0.5 * (power[1:] + power[:-1]) * np.diff(t))
    error = (kinetic[0] + potential[0]) - (kinetic + potential + lost)
    return Quantities(drag, weight, drag + weight, terminal, kinetic, potential, lost, error)
