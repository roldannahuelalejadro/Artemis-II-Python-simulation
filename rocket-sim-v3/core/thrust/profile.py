"""Evaluates thrust functions over time for the active mission phase."""

from __future__ import annotations

from dataclasses import dataclass
import math

from config.constants import EARTH_MU, MOON_ANGULAR_RATE_RAD_S, MOON_SEMIMAJOR_AXIS_M
from coordinates.frame import PolarState, dot, radial_basis
from utils.safe_eval import safe_eval


@dataclass(slots=True)
class ThrustContext:
    t: float
    mission_time: float
    position_xy: tuple[float, float]
    velocity_xy: tuple[float, float]
    moon_position_xy: tuple[float, float] = (0.0, 0.0)

    def as_eval_context(self) -> dict[str, float]:
        x, y = self.position_xy
        vx, vy = self.velocity_xy
        polar = PolarState.from_xy(self.position_xy)
        speed = (vx ** 2 + vy ** 2) ** 0.5
        radial_velocity = 0.0
        tangential_velocity = 0.0
        if polar.radius_m > 0.0:
            radial_velocity = dot(self.position_xy, self.velocity_xy) / polar.radius_m
            _radial, tangential = radial_basis(self.position_xy)
            tangential_velocity = dot(self.velocity_xy, tangential)

        # Signed Earth-centered angular momentum per unit mass. Positive means
        # counterclockwise motion around Earth; negative means clockwise return.
        hz_earth = x * vy - y * vx

        # Lunar-relative geometry used by toy free-return guidance.
        # moon_dx/moon_dy point from the spacecraft toward the Moon.
        moon_x, moon_y = self.moon_position_xy
        moon_dx = moon_x - x
        moon_dy = moon_y - y
        moon_dist = math.hypot(moon_dx, moon_dy)
        if moon_dist > 0.0:
            moon_radial_x = moon_dx / moon_dist
            moon_radial_y = moon_dy / moon_dist
        else:
            moon_radial_x = 0.0
            moon_radial_y = 0.0
        moon_tangent_x = -moon_radial_y
        moon_tangent_y = moon_radial_x

        # Circular Moon velocity in the simplified model.
        moon_vx = -MOON_ANGULAR_RATE_RAD_S * moon_y
        moon_vy = MOON_ANGULAR_RATE_RAD_S * moon_x
        moon_vrel_x = vx - moon_vx
        moon_vrel_y = vy - moon_vy
        moon_vrel_r = moon_vrel_x * moon_radial_x + moon_vrel_y * moon_radial_y
        moon_vrel_t = moon_vrel_x * moon_tangent_x + moon_vrel_y * moon_tangent_y

        # Signed angular momentum relative to the Moon. This helps distinguish
        # whether the local flyby is bending the trajectory around the Moon.
        moon_hz = (x - moon_x) * (vy - moon_vy) - (y - moon_y) * (vx - moon_vx)

        # Tangent to the Moon's Earth-centered orbit.
        moon_orbit_tangent_x = -moon_y / MOON_SEMIMAJOR_AXIS_M
        moon_orbit_tangent_y = moon_x / MOON_SEMIMAJOR_AXIS_M

        # rho points from Moon to spacecraft. Negative behind_score means the
        # spacecraft is behind the Moon relative to the Moon's orbital motion.
        rho_x = x - moon_x
        rho_y = y - moon_y
        rho_dist = math.hypot(rho_x, rho_y)
        if rho_dist > 0.0:
            behind_score = (rho_x / rho_dist) * moon_orbit_tangent_x + (rho_y / rho_dist) * moon_orbit_tangent_y
        else:
            behind_score = 0.0

        return {
            "t": self.t,
            "mission_t": self.mission_time,
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy,
            "r": polar.radius_m,
            "theta": polar.theta_rad,
            "speed": speed,
            "vr": radial_velocity,
            "vtheta": tangential_velocity,
            "hz_earth": hz_earth,
            "earth_dist": polar.radius_m,
            "earth_vr": radial_velocity,
            "earth_vtheta": tangential_velocity,
            "mu_earth": EARTH_MU,
            "r_moon_mean": MOON_SEMIMAJOR_AXIS_M,
            "moon_x": moon_x,
            "moon_y": moon_y,
            "moon_vx": moon_vx,
            "moon_vy": moon_vy,
            "moon_dx": moon_dx,
            "moon_dy": moon_dy,
            "moon_dist": moon_dist,
            "moon_theta": math.atan2(moon_y, moon_x),
            "moon_radial_x": moon_radial_x,
            "moon_radial_y": moon_radial_y,
            "moon_tangent_x": moon_tangent_x,
            "moon_tangent_y": moon_tangent_y,
            "moon_vrel_x": moon_vrel_x,
            "moon_vrel_y": moon_vrel_y,
            "moon_vrel_r": moon_vrel_r,
            "moon_vrel_t": moon_vrel_t,
            "moon_hz": moon_hz,
            "moon_orbit_tangent_x": moon_orbit_tangent_x,
            "moon_orbit_tangent_y": moon_orbit_tangent_y,
            "behind_score": behind_score,
        }


class ThrustProfile:
    def evaluate_components(self, phase, context: ThrustContext) -> tuple[float, float]:
        if phase.is_coast:
            return (0.0, 0.0)

        values = context.as_eval_context()
        primary = safe_eval(phase.primary_expr, values)
        secondary = safe_eval(phase.secondary_expr, values)
        return primary, secondary
