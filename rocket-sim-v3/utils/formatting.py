"""Formatting helpers for mission summaries and telemetry."""

from __future__ import annotations


def format_vector(vec: tuple[float, float], precision: int = 2) -> str:
    return f"({vec[0]:.{precision}f}, {vec[1]:.{precision}f})"


def format_seconds(seconds: float) -> str:
    if seconds < 60.0:
        return f"{seconds:.1f} s"
    minutes = seconds / 60.0
    if minutes < 60.0:
        return f"{minutes:.1f} min"
    hours = minutes / 60.0
    return f"{hours:.2f} h"


def format_energy(joules: float) -> str:
    if abs(joules) < 1e3:
        return f"{joules:.2f} J"
    if abs(joules) < 1e6:
        return f"{joules / 1e3:.2f} kJ"
    if abs(joules) < 1e9:
        return f"{joules / 1e6:.2f} MJ"
    return f"{joules / 1e9:.2f} GJ"
