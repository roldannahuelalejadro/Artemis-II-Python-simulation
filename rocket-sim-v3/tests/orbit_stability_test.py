"""Validation test: circular orbit should remain stable near a target altitude."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordinates.frame import FrameType
from core.phase import MissionPhase
from core.physics.kepler import orbital_period_for_altitude, orbit_quality
from core.simulation import SimulationState


def run_orbit_stability_test(
    altitude_m: float = 200_000.0,
    theta_deg: float = 0.0,
    moon_angle_deg: float = 0.0,
    dt_s: float = 1.0,
    altitude_tolerance_m: float = 15_000.0,
    speed_tolerance_m_s: float = 120.0,
    radial_velocity_tolerance_m_s: float = 80.0,
) -> tuple[bool, dict[str, float]]:
    simulation = SimulationState(dt_s=dt_s)
    simulation.set_moon_angle_deg(moon_angle_deg)
    simulation.place_rocket_in_circular_orbit(altitude_m=altitude_m, theta_deg=theta_deg)

    duration_s = orbital_period_for_altitude(altitude_m)
    simulation.queue_phase(
        MissionPhase(
            label=f"Test orbita circular {altitude_m / 1000.0:.0f} km",
            duration_s=duration_s,
            frame=FrameType.NONE,
        )
    )

    logs = simulation.run_until_pause(max_steps=int(duration_s / dt_s) + 10)
    metrics = orbit_quality(simulation.rocket.position_xy, simulation.rocket.velocity_xy, altitude_m)
    metrics["duration_s"] = duration_s
    metrics["final_sim_time_s"] = simulation.sim_time_s

    success = (
        abs(metrics["altitude_error_m"]) <= altitude_tolerance_m
        and abs(metrics["speed_error_m_s"]) <= speed_tolerance_m_s
        and abs(metrics["radial_velocity_m_s"]) <= radial_velocity_tolerance_m_s
    )

    print("=== Orbit Stability Test ===")
    print(f"Objetivo altitud: {altitude_m:.1f} m")
    print(f"Duracion propagada: {duration_s:.1f} s")
    for line in logs:
        print(line)
    print(
        "Resultado final | "
        f"altitud={metrics['altitude_m']:.2f} m | "
        f"error_altitud={metrics['altitude_error_m']:.2f} m | "
        f"velocidad={metrics['speed_m_s']:.2f} m/s | "
        f"error_velocidad={metrics['speed_error_m_s']:.2f} m/s | "
        f"vel_radial={metrics['radial_velocity_m_s']:.2f} m/s"
    )
    print(f"TEST {'PASS' if success else 'FAIL'}")
    return success, metrics


if __name__ == "__main__":
    ok, _metrics = run_orbit_stability_test()
    raise SystemExit(0 if ok else 1)
