"""Converts thrust commands from XY, prograde, or polar frames into world XY."""

from __future__ import annotations

from coordinates.frame import FrameType, Vector, add, prograde_basis, radial_basis, scale


def to_world_xy(frame: FrameType, primary: float, secondary: float, position_xy: Vector, velocity_xy: Vector) -> Vector:
    if frame == FrameType.NONE:
        return (0.0, 0.0)
    if frame == FrameType.XY:
        return (primary, secondary)
    if frame == FrameType.PROGRADE:
        prograde, normal = prograde_basis(velocity_xy, position_xy)
        return add(scale(prograde, primary), scale(normal, secondary))
    if frame == FrameType.POLAR:
        radial, tangential = radial_basis(position_xy)
        return add(scale(radial, primary), scale(tangential, secondary))
    raise ValueError(f"Unsupported frame: {frame}")
