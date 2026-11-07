import math

import pytest

from ballsim.forces import ConstantGravity, NewtonianGravity, QuadraticDrag
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


def test_newtonian_at_ground():
    G, M, R = 6.674e-11, 5.972e24, 6.371e6
    gravity = NewtonianGravity(G, M, R)
    ground = gravity.force(State(0, 0), Ball(2, 0.1))
    assert ground / 2 == pytest.approx(-G * M / R**2)


def test_newtonian_falls_off_with_height():
    G, M, R = 6.674e-11, 5.972e24, 6.371e6
    gravity = NewtonianGravity(G, M, R)
    ball = Ball(2, 0.1)
    assert gravity.force(State(R, 0), ball) == pytest.approx(gravity.force(State(0, 0), ball) / 4)
