"""Validation test for the 24h high elliptical orbit checkout preset."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.constants import EARTH_RADIUS_M
from coordinates.frame import FrameType, magnitude
from core.phase import MissionPhase
from core.simulation import SimulationState


def run_heo_24h_test() -> tuple[bool, dict[str, float]]:
    expected = {
        "period_s": 86_400.0,
        "apogee_radius_m": 77_926_191.349,
        "apogee_altitude_m": 71_555_191.349,
    }

    sim = SimulationState(dt_s=10.0)
    sim.set_moon_angle_deg(0.0)
    sim.place_rocket_on_surface(
        theta_deg=90.0,
        altitude_m=185_000.0,
        tangential_speed_m_s=10_590.67,
        radial_speed_m_s=0.0,
    )
    sim.queue_phase(MissionPhase("HEO 24h checkout", 86_400.0, FrameType.NONE))

    max_radius = 0.0
    while sim.phase_manager.pending or sim.phase_manager.active is not None:
        sim.resume()
        while sim.is_running:
            sim.update_step()
            max_radius = max(max_radius, magnitude(sim.rocket.position_xy))
            if sim.termination_reason:
                break
        if sim.termination_reason:
            break

    apogee_altitude = max_radius - EARTH_RADIUS_M
    metrics = {
        "sim_time_s": sim.sim_time_s,
        "max_radius_m": max_radius,
        "apogee_altitude_m": apogee_altitude,
        "period_error_s": sim.sim_time_s - expected["period_s"],
        "apogee_radius_error_m": max_radius - expected["apogee_radius_m"],
        "apogee_altitude_error_m": apogee_altitude - expected["apogee_altitude_m"],
    }
    success = (
        sim.termination_reason is None
        and abs(metrics["period_error_s"]) <= 20.0
        and abs(metrics["apogee_altitude_error_m"]) <= 150_000.0
    )

    print("=== HEO 24h Checkout Test ===")
    print(f"termination={sim.termination_reason}")
    print(f"sim_time_s={metrics['sim_time_s']:.2f}")
    print(f"max_radius_m={metrics['max_radius_m']:.2f}")
    print(f"apogee_altitude_m={metrics['apogee_altitude_m']:.2f}")
    print(f"period_error_s={metrics['period_error_s']:.2f}")
    print(f"apogee_altitude_error_m={metrics['apogee_altitude_error_m']:.2f}")
    print(f"TEST {'PASS' if success else 'FAIL'}")
    return success, metrics


if __name__ == "__main__":
    ok, _metrics = run_heo_24h_test()
    raise SystemExit(0 if ok else 1)
