"""Kepler helpers for Moon position and established orbit utilities."""

from __future__ import annotations

import math

from config.constants import EARTH_MU, EARTH_RADIUS_M
from coordinates.frame import dot, magnitude


def circular_speed(radius_m: float, mu: float = EARTH_MU) -> float:
    return math.sqrt(mu / radius_m)


def circular_speed_for_altitude(
    altitude_m: float,
    mu: float = EARTH_MU,
    body_radius_m: float = EARTH_RADIUS_M,
) -> float:
    return circular_speed(body_radius_m + altitude_m, mu=mu)


def orbital_period(radius_m: float, mu: float = EARTH_MU) -> float:
    return 2.0 * math.pi * math.sqrt((radius_m ** 3) / mu)


def orbital_period_for_altitude(
    altitude_m: float,
    mu: float = EARTH_MU,
    body_radius_m: float = EARTH_RADIUS_M,
) -> float:
    return orbital_period(body_radius_m + altitude_m, mu=mu)


def specific_orbital_energy(
    position_xy: tuple[float, float],
    velocity_xy: tuple[float, float],
    mu: float = EARTH_MU,
) -> float:
    radius = magnitude(position_xy)
    speed_sq = dot(velocity_xy, velocity_xy)
    return 0.5 * speed_sq - mu / radius


def altitude(position_xy: tuple[float, float], body_radius_m: float = EARTH_RADIUS_M) -> float:
    return magnitude(position_xy) - body_radius_m


def radial_velocity(position_xy: tuple[float, float], velocity_xy: tuple[float, float]) -> float:
    radius = magnitude(position_xy)
    if radius == 0.0:
        return 0.0
    return dot(position_xy, velocity_xy) / radius


def orbit_quality(
    position_xy: tuple[float, float],
    velocity_xy: tuple[float, float],
    target_altitude_m: float,
) -> dict[str, float]:
    radius = magnitude(position_xy)
    current_altitude = radius - EARTH_RADIUS_M
    target_speed = circular_speed(radius)
    speed = magnitude(velocity_xy)
    vr = radial_velocity(position_xy, velocity_xy)
    return {
        "altitude_m": current_altitude,
        "altitude_error_m": current_altitude - target_altitude_m,
        "speed_m_s": speed,
        "target_speed_m_s": target_speed,
        "speed_error_m_s": speed - target_speed,
        "radial_velocity_m_s": vr,
        "specific_energy_j_kg": specific_orbital_energy(position_xy, velocity_xy),
    }


def classify_earth_orbit(position_xy: tuple[float, float], velocity_xy: tuple[float, float]) -> str:
    radius = magnitude(position_xy)
    current_altitude = radius - EARTH_RADIUS_M
    if current_altitude < 0.0:
        return "impacto o subterraneo"

    speed = magnitude(velocity_xy)
    circular = circular_speed(radius)
    rel_error = abs(speed - circular) / max(circular, 1.0)

    if rel_error < 0.03:
        return "orbita casi circular"
    if speed < circular:
        return "trayectoria suborbital o eliptica baja"
    return "orbita energetica / escape parcial"
