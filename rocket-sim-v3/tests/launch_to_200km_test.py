"""Validation test: attempt orbital insertion from surface using explicit phases."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordinates.frame import FrameType
from core.phase import MissionPhase
from core.physics.kepler import orbit_quality, orbital_period_for_altitude
from core.simulation import SimulationState


def build_surface_to_orbit_phases() -> list[MissionPhase]:
    return [
        MissionPhase(
            label="Ascenso radial inicial",
            duration_s=140.0,
            frame=FrameType.POLAR,
            primary_expr="24.0",
            secondary_expr="2.0 + 0.04*t",
        ),
        MissionPhase(
            label="Giro gravitacional",
            duration_s=220.0,
            frame=FrameType.POLAR,
            primary_expr="max(8.0, 18.0 - 0.045*t)",
            secondary_expr="16.0 + 0.02*t",
        ),
        MissionPhase(
            label="Construccion orbital",
            duration_s=260.0,
            frame=FrameType.POLAR,
            primary_expr="-2.0 - 0.01*t",
            secondary_expr="14.0 - 0.02*t",
        ),
        MissionPhase(
            label="Costa de chequeo",
            duration_s=600.0,
            frame=FrameType.NONE,
        ),
    ]


def run_surface_to_orbit_test(
    target_altitude_m: float = 200_000.0,
    theta_deg: float = 90.0,
    moon_angle_deg: float = 0.0,
    dt_s: float = 1.0,
    altitude_tolerance_m: float = 40_000.0,
    speed_tolerance_m_s: float = 350.0,
    radial_velocity_tolerance_m_s: float = 250.0,
) -> tuple[bool, dict[str, float]]:
    simulation = SimulationState(dt_s=dt_s)
    simulation.set_moon_angle_deg(moon_angle_deg)
    simulation.place_rocket_on_surface(theta_deg=theta_deg, altitude_m=0.0, tangential_speed_m_s=0.0, radial_speed_m_s=0.0)

    for phase in build_surface_to_orbit_phases():
        simulation.queue_phase(phase)

    logs: list[str] = []
    while simulation.phase_manager.pending or simulation.phase_manager.active is not None:
        logs.extend(simulation.run_until_pause(max_steps=50_000))

    metrics = orbit_quality(simulation.rocket.position_xy, simulation.rocket.velocity_xy, target_altitude_m)
    period_guess = orbital_period_for_altitude(max(metrics["altitude_m"], 1.0))
    metrics["period_guess_s"] = period_guess
    metrics["final_sim_time_s"] = simulation.sim_time_s

    success = (
        abs(metrics["altitude_error_m"]) <= altitude_tolerance_m
        and abs(metrics["speed_error_m_s"]) <= speed_tolerance_m_s
        and abs(metrics["radial_velocity_m_s"]) <= radial_velocity_tolerance_m_s
    )

    print("=== Surface To Orbit Test ===")
    print(f"Objetivo altitud: {target_altitude_m:.1f} m")
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
    ok, _metrics = run_surface_to_orbit_test()
    raise SystemExit(0 if ok else 1)
