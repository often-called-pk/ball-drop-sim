import math

import pytest

from ballsim.integrators import INTEGRATORS, rk4_step, simple_step
from ballsim.parameters import INTEGRATOR_NAMES, State


def test_simple_step_matches_brief_formula():
    def accel(state):
        return -3 + 0.1 * state.x

    a0 = -2
    new = simple_step(State(10, 2), 0.5, accel)
    assert new.v == pytest.approx(2 + a0 * 0.5)
    assert new.x == pytest.approx(10 + 2 * 0.5 + 0.5 * a0 * 0.25)


def test_rk4_exact_for_constant_acceleration():
    new = rk4_step(State(100, 5), 0.3, lambda state: -9.81)
    assert new.x == pytest.approx(100 + 5 * 0.3 - 0.5 * 9.81 * 0.09)
    assert new.v == pytest.approx(5 - 9.81 * 0.3)


def test_rk4_beats_simple_on_spring():
    def accel(state):
        return -state.x

    errors = {}
    for name, step in (("simple", simple_step), ("rk4", rk4_step)):
        state = State(1, 0)
        for _ in range(100):
            state = step(state, 0.01, accel)
        errors[name] = abs(state.x - math.cos(1))
    assert errors["rk4"] < errors["simple"]


def test_names_match_parameters():
    assert set(INTEGRATORS) == set(INTEGRATOR_NAMES)
