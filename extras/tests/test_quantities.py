import math
from dataclasses import replace

import numpy as np
import pytest

from ballsim.parameters import Ball, Parameters, State
from ballsim.presets import load_preset
from ballsim.simulation import make_forces, run
from extras.quantities import compute, potential_energy


def tennis(**kw):
    return replace(load_preset("presets/tennis_ball.json"), integrator="rk4", **kw)


def satellite():
    return load_preset("presets/satellite_reentry.json")


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


def test_net_is_drag_plus_weight():
    params = tennis()
    q = compute(params, run(params))
    assert np.array_equal(q.net, q.drag + q.weight)


def test_terminal_speed_constant_gravity():
    params = tennis()
    q = compute(params, run(params))
    k = params.drag_coefficient * params.fluid_density * math.pi * params.radius**2
    assert q.terminal_speed == pytest.approx(math.sqrt(params.mass * params.g / k))


def test_terminal_speed_nan_without_drag():
    params = tennis(drag_coefficient=0.0)
    q = compute(params, run(params))
    assert np.isnan(q.terminal_speed).all()


def test_potential_constant_gravity():
    params = tennis()
    x = np.array([0.0, 10.0, 100.0])
    assert potential_energy(params, x) == pytest.approx(params.mass * params.g * x)


def test_potential_newtonian_near_ground():
    params = replace(Parameters(), gravity_model="newtonian")
    g0 = params.G * params.M / params.R**2
    pe = potential_energy(params, np.array([100.0]))
    assert pe[0] == pytest.approx(params.mass * g0 * 100.0, rel=1e-4)


def test_potential_newtonian_at_one_radius():
    params = replace(Parameters(), gravity_model="newtonian")
    pe = potential_energy(params, np.array([params.R]))
    assert pe[0] == pytest.approx(params.G * params.M * params.mass / (2 * params.R))


def test_potential_unknown_model_raises():
    with pytest.raises(ValueError):
        potential_energy(replace(Parameters(), gravity_model="flat"), np.array([1.0]))


def test_no_drag_conserves_energy():
    params = tennis(drag_coefficient=0.0)
    q = compute(params, run(params))
    e0 = q.kinetic[0] + q.potential[0]
    assert (q.lost == 0).all()
    # the last sample is the impact, where the core interpolates v linearly (~1e-6 off)
    assert np.abs(q.error[:-1]).max() < 1e-9 * e0
    assert np.abs(q.error[-1]) < 1e-5 * e0


def test_drag_loss_grows_and_energy_balances():
    params = tennis()
    q = compute(params, run(params))
    e0 = q.kinetic[0] + q.potential[0]
    assert q.lost[0] == 0
    assert (np.diff(q.lost) >= 0).all()
    assert np.abs(q.error).max() < 1e-3 * e0
