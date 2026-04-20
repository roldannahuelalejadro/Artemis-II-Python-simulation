"""Draws the active thrust direction and intensity indicator."""

from __future__ import annotations

from coordinates.frame import magnitude


def thrust_indicator_text(thrust_xy: tuple[float, float]) -> str:
    mag = magnitude(thrust_xy)
    if mag == 0.0:
        return "Sin empuje activo"
    return f"Empuje activo hacia XY={thrust_xy} | magnitud={mag:.3f} m/s^2"
