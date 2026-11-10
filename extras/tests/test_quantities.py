import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from ballsim.parameters import Ball, State
from ballsim.presets import load_preset
from ballsim.simulation import make_forces, run
from extras.quantities import compute

PRESETS = Path(__file__).resolve().parents[2] / "presets"


def tennis(**kw):
    return replace(load_preset(PRESETS / "tennis_ball.json"), integrator="rk4", **kw)


def satellite():
    return load_preset(PRESETS / "satellite_reentry.json")


@pytest.mark.parametrize("params", [tennis(), satellite()])
def test_vectorised_forces_match_per_sample_loop(params):
    traj = run(params)
    q = compute(params, traj)
    ball = Ball(params.mass, params.radius)
    gravity, drag = make_forces(params)
    for i in range(len(traj.t)):
        state = State(traj.x[i], traj.v[i])
        assert q.weight[i] == pytest.approx(gravity.force(state, ball))
        assert q.drag[i] == pytest.approx(drag.force(state, ball))


def test_terminal_speed():
    params = tennis()
    q = compute(params, run(params))
    k = params.drag_coefficient * params.fluid_density * math.pi * params.radius**2
    assert q.terminal_speed == pytest.approx(math.sqrt(params.mass * params.g / k))
    params = tennis(drag_coefficient=0.0)
    assert np.isnan(compute(params, run(params)).terminal_speed).all()


@pytest.mark.parametrize(
    "params",
    [tennis(drag_coefficient=0.0), replace(satellite(), drag_coefficient=0.0, integrator="rk4")],
)
def test_no_drag_conserves_energy(params):
    q = compute(params, run(params))
    e0 = q.kinetic[0] + q.potential[0]
    assert (q.lost == 0).all()
    # the last sample may be the impact, where the core interpolates v linearly (~1e-6 off)
    assert np.abs(q.error[:-1]).max() < 1e-9 * e0
    assert np.abs(q.error[-1]) < 1e-5 * e0


def test_drag_loss_grows_and_energy_balances():
    params = tennis()
    q = compute(params, run(params))
    e0 = q.kinetic[0] + q.potential[0]
    assert q.lost[0] == 0
    assert (np.diff(q.lost) >= 0).all()
    assert np.abs(q.error).max() < 1e-3 * e0
