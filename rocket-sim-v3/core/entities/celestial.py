"""Celestial body definitions for Earth and Moon."""

from __future__ import annotations

from dataclasses import dataclass
import math

from config.constants import (
    EARTH_MU,
    EARTH_RADIUS_M,
    MOON_ANGULAR_RATE_RAD_S,
    MOON_MU,
    MOON_RADIUS_M,
    MOON_SEMIMAJOR_AXIS_M,
)


@dataclass(slots=True)
class CelestialBody:
    name: str
    mu: float
    radius_m: float
    position_xy: tuple[float, float]


def create_earth() -> CelestialBody:
    return CelestialBody("Earth", EARTH_MU, EARTH_RADIUS_M, (0.0, 0.0))


def create_moon(sim_time_s: float, initial_angle_rad: float) -> CelestialBody:
    angle = initial_angle_rad + MOON_ANGULAR_RATE_RAD_S * sim_time_s
    return CelestialBody(
        "Moon",
        MOON_MU,
        MOON_RADIUS_M,
        (
            MOON_SEMIMAJOR_AXIS_M * math.cos(angle),
            MOON_SEMIMAJOR_AXIS_M * math.sin(angle),
        ),
    )
