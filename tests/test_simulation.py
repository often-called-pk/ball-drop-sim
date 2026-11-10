import math
from dataclasses import replace

import numpy as np
import pytest

from ballsim.parameters import Ball, Parameters, State
from ballsim.simulation import acceleration, describe, make_forces, run

G_EARTH = 9.81


def no_drag(**kw):
    return replace(Parameters(), drag_coefficient=0.0, **kw)


def terminal_speed(p):
    return math.sqrt(p.mass * p.g / (p.drag_coefficient * p.fluid_density * math.pi * p.radius**2))


@pytest.mark.parametrize("integrator", ["simple", "rk4"])
def test_free_fall_matches_closed_form(integrator):
    p = no_drag(
        initial_height=100,
        initial_velocity=5,
        finish_time=3,
        time_step=0.01,
        integrator=integrator,
    )
    tr = run(p)
    assert np.allclose(tr.x, 100 + 5 * tr.t - 0.5 * G_EARTH * tr.t**2, rtol=0, atol=1e-6)
    assert np.allclose(tr.v, 5 - G_EARTH * tr.t, rtol=0, atol=1e-6)
    assert np.allclose(tr.a, -G_EARTH, rtol=0, atol=1e-9)


@pytest.mark.parametrize("dt, tol", [(0.01, 1e-5), (0.5, 2e-3)])
def test_impact_time_interpolated(dt, tol):
    tr = run(no_drag(initial_height=100, finish_time=10, time_step=dt))
    expected = math.sqrt(2 * 100 / G_EARTH)
    assert tr.impact_time == pytest.approx(expected, abs=tol)
    assert tr.x[-1] == 0 and np.all(tr.x[:-1] > 0)
    assert tr.t[-1] == tr.impact_time
    assert tr.impact_velocity == tr.v[-1]
    assert tr.v[-1] == pytest.approx(-G_EARTH * expected, rel=1e-3)


@pytest.mark.parametrize(
    "finish, dt, samples", [(1.0, 0.3, 5), (1.1, 0.1, 12), (0.9, 0.3, 4), (2.7, 0.3, 10)]
)
def test_airborne_run_ends_exactly_at_finish_time(finish, dt, samples):
    tr = run(no_drag(initial_height=1e6, finish_time=finish, time_step=dt))
    assert tr.t[-1] == finish
    assert len(tr.t) == samples
    assert tr.impact_time is None
    assert np.all(np.diff(tr.t) > 1e-6)


def test_terminal_velocity():
    p = replace(Parameters(), initial_height=10000, finish_time=60)
    tr = run(p)
    assert tr.v[-1] == pytest.approx(-terminal_speed(p), rel=0.01)
    assert tr.a[-1] == pytest.approx(0.0, abs=1e-6)
    forces = make_forces(p)
    for x, v, a in zip(tr.x, tr.v, tr.a):
        assert a == pytest.approx(acceleration(State(x, v), Ball(p.mass, p.radius), forces))


def test_run_uses_chosen_gravity_model():
    constant = run(no_drag(g=3.0))
    newtonian = run(no_drag(g=3.0, gravity_model="newtonian"))
    p = no_drag()
    assert constant.a[0] == pytest.approx(-3.0)
    assert newtonian.a[0] == pytest.approx(-p.G * p.M / (p.R + p.initial_height) ** 2)


def test_rk4_more_accurate_and_both_converge():
    base = replace(Parameters(), initial_height=10000, finish_time=5)
    vt = terminal_speed(base)
    exact = -vt * math.tanh(G_EARTH * 5 / vt)
    err = {}
    for name in ("simple", "rk4"):
        for dt in (0.1, 0.05):
            tr = run(replace(base, integrator=name, time_step=dt))
            err[name, dt] = abs(tr.v[-1] - exact)
    for dt in (0.1, 0.05):
        assert err["rk4", dt] < err["simple", dt]
    for name in ("simple", "rk4"):
        assert err[name, 0.05] < err[name, 0.1]


def test_describe():
    assert "impact" in describe(run(Parameters()))
    assert "airborne" in describe(run(replace(Parameters(), initial_height=1e6)))
