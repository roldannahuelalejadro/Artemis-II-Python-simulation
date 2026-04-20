"""Numerical integration strategies for the rocket state."""

from __future__ import annotations

from coordinates.frame import Vector, add, scale


def symplectic_euler(position_xy: Vector, velocity_xy: Vector, acceleration_xy: Vector, dt_s: float) -> tuple[Vector, Vector]:
    new_velocity = add(velocity_xy, scale(acceleration_xy, dt_s))
    new_position = add(position_xy, scale(new_velocity, dt_s))
    return new_position, new_velocity
