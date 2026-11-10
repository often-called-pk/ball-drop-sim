"""The run loop: steps the state in time and stops at impact or finish time."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ballsim.forces import ConstantGravity, Force, NewtonianGravity, QuadraticDrag
from ballsim.integrators import INTEGRATORS
from ballsim.parameters import Ball, Parameters, State, validate


@dataclass
class Trajectory:
    """Sampled history of one run plus its impact, if the ball reached the ground."""

    name: str
    gravity_model: str
    integrator: str
    t: np.ndarray
    x: np.ndarray
    v: np.ndarray
    a: np.ndarray
    impact_time: float | None
    impact_velocity: float | None

    def label(self) -> str:
        return f"{self.name} ({self.gravity_model}, {self.integrator})"


def make_forces(params: Parameters) -> list[Force]:
    """Build the forces a run uses: one gravity model, then drag."""
    if params.gravity_model == "constant":
        gravity: Force = ConstantGravity(params.g)
    elif params.gravity_model == "newtonian":
        gravity = NewtonianGravity(params.G, params.M, params.R)
    else:
        raise ValueError(f"no force for gravity model {params.gravity_model!r}")
    return [gravity, QuadraticDrag(params.drag_coefficient, params.fluid_density)]


def acceleration(state: State, ball: Ball, forces: list[Force]) -> float:
    """Newton's second law: net force over mass."""
    return sum(force.force(state, ball) for force in forces) / ball.mass


def run(params: Parameters) -> Trajectory:
    """Simulate one run and return its trajectory."""
    validate(params)
    ball = Ball(params.mass, params.radius)
    forces = make_forces(params)
    step = INTEGRATORS[params.integrator]

    def accel(state: State) -> float:
        return acceleration(state, ball, forces)

    dt_nominal = params.time_step
    finish = params.finish_time
    # round off float noise: 2.7 / 0.3 is 9.000000000000002
    n = math.ceil(round(finish / dt_nominal, 9))
    t = np.zeros(n + 1)
    x = np.zeros(n + 1)
    v = np.zeros(n + 1)
    a = np.zeros(n + 1)

    state = State(params.initial_height, params.initial_velocity)
    x[0], v[0], a[0] = state.x, state.v, accel(state)
    impact_time = None
    impact_velocity = None
    last = 0

    for i in range(1, n + 1):
        # i * dt avoids float drift. The last sample is exactly finish time.
        t_new = finish if i == n else i * dt_nominal
        dt = t_new - t[i - 1]
        new = step(state, dt, accel)
        hit = new.x <= 0
        if hit:
            # Step crossed the ground: interpolate linearly between the two samples.
            frac = state.x / (state.x - new.x)
            t_new = t[i - 1] + frac * dt
            new = State(0.0, state.v + frac * (new.v - state.v))
        t[i], x[i], v[i] = t_new, new.x, new.v
        a[i] = accel(new)
        last = i
        if hit:
            impact_time, impact_velocity = float(t_new), float(new.v)
            break
        state = new

    end = last + 1
    return Trajectory(
        params.name, params.gravity_model, params.integrator,
        t[:end], x[:end], v[:end], a[:end],
        impact_time, impact_velocity,
    )


def describe(trajectory: Trajectory) -> str:
    """One-line summary of how a run ended."""
    max_speed = float(np.max(np.abs(trajectory.v)))
    if trajectory.impact_time is not None:
        return (
            f"{trajectory.name}: impact at t = {trajectory.impact_time:.3f} s, "
            f"v = {trajectory.impact_velocity:.3f} m/s, max speed {max_speed:.3f} m/s"
        )
    return (
        f"{trajectory.name}: airborne at finish time t = {trajectory.t[-1]:.3f} s, "
        f"height {trajectory.x[-1]:.3f} m, max speed {max_speed:.3f} m/s"
    )
