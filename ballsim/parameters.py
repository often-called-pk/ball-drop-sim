"""Inputs of a run: the ball, its state, the parameters and their validation."""
from __future__ import annotations

import math
from dataclasses import dataclass, fields

GRAVITY_MODELS = ("constant", "newtonian")
INTEGRATOR_NAMES = ("simple", "rk4")
TEXT_FIELDS = ("name", "gravity_model", "integrator")  # every other field is a float


@dataclass
class Ball:
    mass: float
    radius: float


@dataclass
class State:
    x: float  # height in m, positive up
    v: float  # velocity in m/s, positive up


@dataclass
class Parameters:
    name: str = "tennis ball"
    mass: float = 0.057
    radius: float = 0.0335
    drag_coefficient: float = 0.5
    fluid_density: float = 1.225
    gravity_model: str = "constant"
    g: float = 9.81
    G: float = 6.674e-11
    M: float = 5.972e24
    R: float = 6.371e6
    initial_height: float = 100.0
    initial_velocity: float = 0.0
    finish_time: float = 10.0
    time_step: float = 0.01
    integrator: str = "simple"


def _require(ok: bool, field: str, rule: str, value: object) -> None:
    if not ok:
        raise ValueError(f"{field} must be {rule}, got {value}")


def validate(params: Parameters) -> None:
    """Reject values that would make a run meaningless, naming the field."""
    for field in fields(Parameters):
        value = getattr(params, field.name)
        if field.name not in TEXT_FIELDS:
            _require(math.isfinite(value), field.name, "finite", value)
    _require(params.mass > 0, "mass", "> 0", params.mass)
    _require(params.radius > 0, "radius", "> 0", params.radius)
    _require(params.time_step > 0, "time_step", "> 0", params.time_step)
    _require(params.finish_time > 0, "finish_time", "> 0", params.finish_time)
    _require(
        params.finish_time / params.time_step <= 1e7,
        "time_step", ">= finish_time / 1e7 (at most ten million steps)", params.time_step,
    )
    _require(params.drag_coefficient >= 0, "drag_coefficient", ">= 0", params.drag_coefficient)
    _require(params.fluid_density >= 0, "fluid_density", ">= 0", params.fluid_density)
    _require(params.initial_height > 0, "initial_height", "> 0", params.initial_height)
    _require(params.gravity_model in GRAVITY_MODELS, "gravity_model",
             f"one of {GRAVITY_MODELS}", params.gravity_model)
    _require(params.integrator in INTEGRATOR_NAMES, "integrator",
             f"one of {INTEGRATOR_NAMES}", params.integrator)
    if params.gravity_model == "constant":
        _require(params.g >= 0, "g", ">= 0", params.g)
    elif params.gravity_model == "newtonian":
        _require(params.G > 0, "G", "> 0", params.G)
        _require(params.M > 0, "M", "> 0", params.M)
        _require(params.R > 0, "R", "> 0", params.R)
