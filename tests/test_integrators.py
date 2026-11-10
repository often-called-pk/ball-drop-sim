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


def test_rk4_accurate_on_spring():
    state = State(1, 0)
    for _ in range(100):
        state = rk4_step(state, 0.01, lambda s: -s.x)
    assert abs(state.x - math.cos(1)) < 1e-9


def test_names_match_parameters():
    assert set(INTEGRATORS) == set(INTEGRATOR_NAMES)
