"""Integrators: each advances a state by one time step."""
from __future__ import annotations

from typing import Callable

from ballsim.parameters import State


def simple_step(state: State, dt: float, accel: Callable[[State], float]) -> State:
    """Brief scheme: one acceleration, used in both updates."""
    a = accel(state)
    v = state.v + a * dt
    x = state.x + state.v * dt + 0.5 * a * dt**2
    return State(x, v)


def rk4_step(state: State, dt: float, accel: Callable[[State], float]) -> State:
    """Classic fourth-order Runge-Kutta, more accurate at larger steps."""
    # Each k is (dx/dt, dv/dt) at a trial state.
    k1x, k1v = state.v, accel(state)
    mid1 = State(state.x + 0.5 * dt * k1x, state.v + 0.5 * dt * k1v)
    k2x, k2v = mid1.v, accel(mid1)
    mid2 = State(state.x + 0.5 * dt * k2x, state.v + 0.5 * dt * k2v)
    k3x, k3v = mid2.v, accel(mid2)
    end = State(state.x + dt * k3x, state.v + dt * k3v)
    k4x, k4v = end.v, accel(end)
    x = state.x + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
    v = state.v + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
    return State(x, v)


INTEGRATORS = {"simple": simple_step, "rk4": rk4_step}
