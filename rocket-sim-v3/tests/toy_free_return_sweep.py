"""Parameter sweep for a toy lunar free-return trajectory.

The goal is not a high-fidelity Artemis II trajectory. This script searches a
small space of soft-guidance gains and lunar phase angles, then prints the best
combination for the 2D toy model.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coordinates.frame import FrameType, magnitude
from core.phase import MissionPhase
from core.simulation import SimulationState
from ui.mission_panel import HEO_24H_CHECKOUT


def build_phases(tli_duration_s: float, far_gain: float, behind_gain: float, exit_gain: float) -> list[MissionPhase]:
    return [
        MissionPhase("HEO 24h checkout", 86_400.0, FrameType.NONE),
        MissionPhase(
            "TLI desde HEO",
            tli_duration_s,
            FrameType.PROGRADE,
            "max(0,min(8,0.025*(sqrt(mu_earth*(2/r - 1/233285500.0))-speed)))",
            "0.0",
        ),
        MissionPhase(
            "Guiado translunar lejano",
            210_000.0,
            FrameType.XY,
            f"({far_gain}*moon_radial_x - 0.00000035*moon_vrel_t*moon_tangent_x) if moon_dist > 8e7 else 0.0",
            f"({far_gain}*moon_radial_y - 0.00000035*moon_vrel_t*moon_tangent_y) if moon_dist > 8e7 else 0.0",
        ),
        MissionPhase(
            "Sesgo detras de la Luna",
            120_000.0,
            FrameType.XY,
            f"((-{behind_gain}*moon_orbit_tangent_x if behind_score > -0.25 else 0.0) + (0.0025*(-moon_radial_x) if moon_dist < 9e6 else 0.0)) if moon_dist < 1.2e8 else 0.0",
            f"((-{behind_gain}*moon_orbit_tangent_y if behind_score > -0.25 else 0.0) + (0.0025*(-moon_radial_y) if moon_dist < 9e6 else 0.0)) if moon_dist < 1.2e8 else 0.0",
        ),
        MissionPhase(
            "Salida post-flyby",
            430_000.0,
            FrameType.XY,
            f"(-{exit_gain}*x/r - 0.00000045*vr*x/r) if (moon_dist < 2.4e8 or r > 1.5e8) else 0.0",
            f"(-{exit_gain}*y/r - 0.00000045*vr*y/r) if (moon_dist < 2.4e8 or r > 1.5e8) else 0.0",
        ),
        MissionPhase("Costa de retorno", 180_000.0, FrameType.NONE),
    ]


def run_case(
    moon_angle_deg: float,
    tli_duration_s: float,
    far_gain: float,
    behind_gain: float,
    exit_gain: float,
    dt_s: float = 60.0,
) -> dict[str, float | str | None]:
    sim = SimulationState(dt_s=dt_s)
    sim.set_moon_angle_deg(moon_angle_deg)
    sim.place_rocket_on_surface(
        theta_deg=90.0,
        altitude_m=HEO_24H_CHECKOUT["launch_altitude_m"],
        tangential_speed_m_s=HEO_24H_CHECKOUT["launch_tangential_speed_m_s"],
        radial_speed_m_s=0.0,
    )

    min_earth_radius_after_day6 = float("inf")
    for phase in build_phases(tli_duration_s, far_gain, behind_gain, exit_gain):
        sim.queue_phase(phase)

    post_tli_start_s = 86_400.0 + tli_duration_s
    min_post_tli_moon_distance = float("inf")
    min_post_tli_behind_score = 0.0
    min_post_tli_time_s = 0.0
    while sim.phase_manager.pending or sim.phase_manager.active is not None:
        sim.resume()
        while sim.is_running:
            sim.update_step()
            if sim.sim_time_s >= post_tli_start_s:
                moon_dx = sim.rocket.position_xy[0] - sim.moon.position_xy[0]
                moon_dy = sim.rocket.position_xy[1] - sim.moon.position_xy[1]
                moon_distance = (moon_dx * moon_dx + moon_dy * moon_dy) ** 0.5
                if moon_distance < min_post_tli_moon_distance:
                    min_post_tli_moon_distance = moon_distance
                    min_post_tli_behind_score = sim._current_behind_score()
                    min_post_tli_time_s = sim.sim_time_s
            if sim.sim_time_s >= 6.0 * 86_400.0:
                min_earth_radius_after_day6 = min(min_earth_radius_after_day6, magnitude(sim.rocket.position_xy))
            if sim.termination_reason:
                break
        if sim.termination_reason:
            break

    if min_earth_radius_after_day6 == float("inf"):
        min_earth_radius_after_day6 = magnitude(sim.rocket.position_xy)
    if min_post_tli_moon_distance == float("inf"):
        min_post_tli_moon_distance = 1e99

    # Target a safe but close flyby: 5e6 to 2e7 m from Moon center.
    dist = min_post_tli_moon_distance
    if dist < 5e6:
        flyby_penalty = (5e6 - dist) / 1e6 + 100.0
    elif dist > 2e7:
        flyby_penalty = (dist - 2e7) / 1e6
    else:
        flyby_penalty = 0.0

    behind_penalty = max(0.0, min_post_tli_behind_score + 0.05) * 50.0
    return_penalty = max(0.0, (min_earth_radius_after_day6 - 120e6) / 20e6)
    impact_penalty = 500.0 if sim.termination_reason else 0.0
    score = flyby_penalty + behind_penalty + return_penalty + impact_penalty

    return {
        "score": score,
        "moon_angle_deg": moon_angle_deg,
        "tli_duration_s": tli_duration_s,
        "far_gain": far_gain,
        "behind_gain": behind_gain,
        "exit_gain": exit_gain,
        "termination": sim.termination_reason,
        "min_moon_distance_m": min_post_tli_moon_distance,
        "min_moon_behind_score": min_post_tli_behind_score,
        "min_moon_distance_time_s": min_post_tli_time_s,
        "min_earth_radius_after_day6_m": min_earth_radius_after_day6,
        "final_radius_m": magnitude(sim.rocket.position_xy),
        "final_time_s": sim.sim_time_s,
    }


def main() -> None:
    best: dict[str, float | str | None] | None = None
    for moon_angle in [198, 200, 202, 204, 206, 208]:
        for tli_duration in [650.0, 700.0]:
            for far_gain in [0.0, 0.00035]:
                for behind_gain in [0.0008, 0.0014]:
                    for exit_gain in [0.003, 0.006, 0.01]:
                        result = run_case(moon_angle, tli_duration, far_gain, behind_gain, exit_gain)
                        if best is None or float(result["score"]) < float(best["score"]):
                            best = result

    assert best is not None
    print("=== Toy Free Return Sweep ===")
    print(f"score={best['score']:.3f}")
    print(f"moon_angle_deg={best['moon_angle_deg']}")
    print(f"tli_duration_s={best['tli_duration_s']}")
    print(f"far_gain={best['far_gain']}")
    print(f"behind_gain={best['behind_gain']}")
    print(f"exit_gain={best['exit_gain']}")
    print(f"termination={best['termination']}")
    print(f"min_moon_distance_km={float(best['min_moon_distance_m']) / 1000.0:.1f}")
    print(f"min_moon_behind_score={best['min_moon_behind_score']:.3f}")
    print(f"min_moon_time_days={float(best['min_moon_distance_time_s']) / 86400.0:.2f}")
    print(f"min_earth_radius_after_day6_km={float(best['min_earth_radius_after_day6_m']) / 1000.0:.1f}")
    print(f"final_radius_km={float(best['final_radius_m']) / 1000.0:.1f}")
    print("\nSuggested phase constants:")
    print(f"moon_angle_deg = {best['moon_angle_deg']}")
    print(f"TLI duration = {best['tli_duration_s']} s")
    print(f"far_gain = {best['far_gain']}")
    print(f"behind_gain = {best['behind_gain']}")
    print(f"exit_gain = {best['exit_gain']}")


if __name__ == "__main__":
    main()
