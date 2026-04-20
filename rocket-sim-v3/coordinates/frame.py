"""Coordinate frame abstractions for XY, prograde, and polar inputs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Tuple


class FrameType(str, Enum):
    NONE = "none"
    XY = "xy"
    PROGRADE = "prograde"
    POLAR = "polar"


Vector = Tuple[float, float]


def magnitude(vec: Vector) -> float:
    return math.hypot(vec[0], vec[1])


def normalize(vec: Vector) -> Vector:
    mag = magnitude(vec)
    if mag == 0.0:
        return (0.0, 0.0)
    return (vec[0] / mag, vec[1] / mag)


def add(a: Vector, b: Vector) -> Vector:
    return (a[0] + b[0], a[1] + b[1])


def scale(vec: Vector, factor: float) -> Vector:
    return (vec[0] * factor, vec[1] * factor)


def dot(a: Vector, b: Vector) -> float:
    return a[0] * b[0] + a[1] * b[1]


def angle_of(vec: Vector) -> float:
    return math.atan2(vec[1], vec[0])


def perpendicular_ccw(vec: Vector) -> Vector:
    return (-vec[1], vec[0])


def radial_basis(position_xy: Vector) -> tuple[Vector, Vector]:
    radial = normalize(position_xy)
    tangential = perpendicular_ccw(radial)
    return radial, tangential


def prograde_basis(velocity_xy: Vector, fallback_position_xy: Vector) -> tuple[Vector, Vector]:
    prograde = normalize(velocity_xy)
    if prograde == (0.0, 0.0):
        _, tangential = radial_basis(fallback_position_xy)
        prograde = tangential
    normal = perpendicular_ccw(prograde)
    return prograde, normal


@dataclass(slots=True)
class PolarState:
    radius_m: float
    theta_rad: float

    @classmethod
    def from_xy(cls, position_xy: Vector) -> "PolarState":
        return cls(radius_m=magnitude(position_xy), theta_rad=angle_of(position_xy))

    def to_xy(self) -> Vector:
        return (
            self.radius_m * math.cos(self.theta_rad),
            self.radius_m * math.sin(self.theta_rad),
        )
