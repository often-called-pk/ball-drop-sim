"""Forces on the ball, each returning newtons along the height axis."""
from __future__ import annotations

import math

from ballsim.parameters import Ball, State


class Force:
    """Force along the height axis in N, negative = toward ground."""

    def force(self, state: State, ball: Ball) -> float:
        raise NotImplementedError


class ConstantGravity(Force):
    """Weight in a uniform field, for drops that stay near the ground."""

    def __init__(self, g: float) -> None:
        self.g = g

    def force(self, state: State, ball: Ball) -> float:
        return -ball.mass * self.g


class NewtonianGravity(Force):
    """Inverse-square weight, for drops from large heights."""

    def __init__(self, G: float, M: float, R: float) -> None:
        self.G = G
        self.M = M
        self.R = R

    def force(self, state: State, ball: Ball) -> float:
        # R + x = 0 is not handled, per the challenge brief.
        return -self.G * self.M * ball.mass / (self.R + state.x) ** 2


class QuadraticDrag(Force):
    """Drag grows with v squared and always opposes the motion."""

    def __init__(self, drag_coefficient: float, fluid_density: float) -> None:
        self.drag_coefficient = drag_coefficient
        self.fluid_density = fluid_density

    def force(self, state: State, ball: Ball) -> float:
        # No 1/2 factor, per the challenge brief. v * abs(v) keeps the sign of v.
        area = math.pi * ball.radius**2
        coefficient = self.drag_coefficient * self.fluid_density * area
        return -coefficient * state.v * abs(state.v)
