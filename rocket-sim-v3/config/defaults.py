"""Default launch and mission values for rocket-sim-v3."""

from config.constants import (
    DEFAULT_LAUNCH_LATITUDE_DEG,
    DEFAULT_LUNAR_ANGLE_DEG,
    DEFAULT_ROCKET_MASS_KG,
    DEFAULT_TIME_STEP_S,
    EARTH_RADIUS_M,
)

DEFAULTS = {
    "launch_theta_deg": DEFAULT_LAUNCH_LATITUDE_DEG,
    "launch_altitude_m": 0.0,
    "launch_tangential_speed_m_s": 0.0,
    "launch_radial_speed_m_s": 0.0,
    "moon_angle_deg": DEFAULT_LUNAR_ANGLE_DEG,
    "rocket_mass_kg": DEFAULT_ROCKET_MASS_KG,
    "time_step_s": DEFAULT_TIME_STEP_S,
    "surface_radius_m": EARTH_RADIUS_M,
    "phase_duration_s": 150.0,
    "phase_frame": "prograde",
    "phase_fx": "12.0 if t < 120 else 5.0",
    "phase_fy": "0.0",
    "phase_label": "Ascenso inicial",
    "ui_refresh_ms": 20,
    "steps_per_frame": 3,
    "time_speed_options": [1, 3, 10, 30, 100, 500],
}
