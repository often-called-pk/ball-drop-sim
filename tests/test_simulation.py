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


def test_upward_throw_still_impacts():
    tr = run(no_drag(initial_height=1, initial_velocity=20, finish_time=10))
    root = (20 + math.sqrt(400 + 4 * 4.905)) / (2 * 4.905)
    assert tr.impact_time == pytest.approx(root, abs=1e-3)
    assert tr.x.max() > 1


def test_airborne_run_ends_exactly_at_finish_time():
    tr = run(no_drag(initial_height=1e6, finish_time=1.0, time_step=0.3))
    assert tr.t[-1] == 1.0
    assert len(tr.t) == 5
    assert tr.impact_time is None
    tr = run(no_drag(initial_height=1e6, finish_time=1.1, time_step=0.1))
    assert tr.t[-1] == 1.1
    assert np.all(np.diff(tr.t) > 1e-6)


def test_last_sample_is_exactly_finish_time_despite_rounding():
    tr = run(no_drag(initial_height=1e6, finish_time=0.9, time_step=0.3))
    assert tr.t[-1] == 0.9


def test_float_noise_in_step_count_adds_no_extra_sample():
    tr = run(no_drag(initial_height=1e6, finish_time=2.7, time_step=0.3))
    assert len(tr.t) == 10
    assert tr.t[-1] == 2.7
    assert np.all(np.diff(tr.t) > 1e-6)


def test_terminal_velocity():
    p = replace(Parameters(), initial_height=10000, finish_time=60)
    tr = run(p)
    assert tr.v[-1] == pytest.approx(-terminal_speed(p), rel=0.01)
    assert tr.a[-1] == pytest.approx(0.0, abs=1e-6)


def test_newtonian_matches_constant_for_huge_planet():
    R = 6.371e9
    G = 6.674e-11
    M = G_EARTH * R**2 / G
    base = replace(Parameters(), initial_height=100)
    constant = run(replace(base, gravity_model="constant", g=G_EARTH))
    newtonian = run(replace(base, gravity_model="newtonian", G=G, M=M, R=R))
    assert newtonian.impact_time == pytest.approx(constant.impact_time, rel=1e-3)


def test_newtonian_acceleration_at_ground():
    p = no_drag(gravity_model="newtonian")
    a = acceleration(State(0, 0), Ball(1, 1), make_forces(p))
    assert a == pytest.approx(-p.G * p.M / p.R**2)


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


def test_label():
    tr = run(Parameters())
    assert tr.label() == "tennis ball (constant, simple)"


def test_describe():
    assert "impact" in describe(run(Parameters()))
    assert "airborne" in describe(run(replace(Parameters(), initial_height=1e6)))
