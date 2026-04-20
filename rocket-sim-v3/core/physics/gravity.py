"""Gravity field contributions from Earth and Moon."""

from __future__ import annotations

from coordinates.frame import Vector, add, magnitude, scale


def gravitational_acceleration(source_position: Vector, mu: float, target_position: Vector) -> Vector:
    dx = source_position[0] - target_position[0]
    dy = source_position[1] - target_position[1]
    r = magnitude((dx, dy))
    if r == 0.0:
        return (0.0, 0.0)
    factor = mu / (r ** 3)
    return (dx * factor, dy * factor)


def combined_gravity(earth, moon, rocket_position_xy: Vector) -> Vector:
    earth_g = gravitational_acceleration(earth.position_xy, earth.mu, rocket_position_xy)
    moon_g = gravitational_acceleration(moon.position_xy, moon.mu, rocket_position_xy)
    return add(earth_g, moon_g)
