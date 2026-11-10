import math

import pytest

from ballsim.forces import ConstantGravity, QuadraticDrag
from ballsim.parameters import Ball, State


def test_drag_opposes_motion():
    ball = Ball(1, 0.1)
    drag = QuadraticDrag(0.5, 1.2)
    assert drag.force(State(0, 3), ball) < 0
    assert drag.force(State(0, -3), ball) > 0
    assert drag.force(State(0, 0), ball) == 0
    expected = 0.5 * 1.2 * 9 * math.pi * 0.01
    assert drag.force(State(0, 3), ball) == pytest.approx(-expected)


def test_constant_gravity():
    ball = Ball(2, 0.1)
    gravity = ConstantGravity(9.81)
    assert gravity.force(State(0, 0), ball) == pytest.approx(-2 * 9.81)
    assert gravity.force(State(5000, 0), ball) == pytest.approx(-2 * 9.81)
