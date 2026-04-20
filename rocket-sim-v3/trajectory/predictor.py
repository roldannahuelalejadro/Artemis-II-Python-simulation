"""Predictive trajectory tools for previewing future motion."""

from __future__ import annotations

from coordinates.frame import Vector
from core.physics.gravity import combined_gravity
from core.physics.integrator import symplectic_euler


def predict_ballistic_path(earth, moon, position_xy: Vector, velocity_xy: Vector, dt_s: float = 5.0, steps: int = 120) -> list[Vector]:
    trail: list[Vector] = []
    pos = position_xy
    vel = velocity_xy
    for _ in range(steps):
        acc = combined_gravity(earth, moon, pos)
        pos, vel = symplectic_euler(pos, vel, acc, dt_s)
        trail.append(pos)
    return trail
