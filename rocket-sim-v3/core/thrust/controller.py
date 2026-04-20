"""Optional higher-level thrust controllers and helpers."""

from __future__ import annotations

from config.constants import EARTH_MU
from coordinates.frame import magnitude, normalize, scale


def circularization_hint(position_xy: tuple[float, float], velocity_xy: tuple[float, float], strength: float = 1.0) -> tuple[float, float]:
    radius = magnitude(position_xy)
    if radius == 0.0:
        return (0.0, 0.0)
    target_speed = (EARTH_MU / radius) ** 0.5
    current_speed = magnitude(velocity_xy)
    if current_speed == 0.0:
        return (0.0, 0.0)
    prograde = normalize(velocity_xy)
    return scale(prograde, (target_speed - current_speed) * strength)
