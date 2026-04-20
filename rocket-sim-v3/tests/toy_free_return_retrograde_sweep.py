"""Sweep for a toy free-return with clockwise geocentric return.

This is intentionally a 2D toy optimizer, not an Artemis II reconstruction. The
search rewards four geometric facts: leave Earth counterclockwise, pass behind
the Moon, flip Earth-centered angular momentum negative after the flyby, and
return to a safe Earth periapsis band.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.constants import EARTH_RADIUS_M
from coordinates.frame import FrameType, magnitude
from core.phase import MissionPhase
from core.simulation import SimulationState
from ui.mission_panel import HEO_24H_CHECKOUT


def build_phases(
    tli_duration_s: float,
    tli_gain: float,
    tli_max_accel: float,
    target_a_m: float,
    guide_gain: float,
    behind_gain: float,
    return_radial_gain: float,
    retro_gain: float,
    periapsis_gain: float,
) -> list[MissionPhase]:
    tli_expr = (
        f"max(0,min({tli_max_accel},"
        f"{tli_gain}*(sqrt(mu_earth*(2/r - 1/{target_a_m}))-speed)+0.25))"
    )
    return [
        MissionPhase("HEO 24h checkout", 86_400.0, FrameType.NONE),
        MissionPhase("TLI directa", tli_duration_s, FrameType.PROGRADE, tli_expr, "0.0"),
        MissionPhase(
            "Guiado translunar",
            165_000.0,
            FrameType.XY,
            f"({guide_gain}*moon_radial_x - 0.00000028*moon_vrel_t*moon_tangent_x) if moon_dist > 6e7 else 0.0",
            f"({guide_gain}*moon_radial_y - 0.00000028*moon_vrel_t*moon_tangent_y) if moon_dist > 6e7 else 0.0",
        ),
        MissionPhase(
            "Paso detras de la Luna",
            105_000.0,
            FrameType.XY,
            f"((-{behind_gain}*moon_orbit_tangent_x if behind_score > -0.35 else 0.0) + (-0.00000020*moon_vrel_t*moon_tangent_x) + (0.0030*(-moon_radial_x) if moon_dist < 7e6 else 0.0)) if moon_dist < 1.35e8 else 0.0",
            f"((-{behind_gain}*moon_orbit_tangent_y if behind_score > -0.35 else 0.0) + (-0.00000020*moon_vrel_t*moon_tangent_y) + (0.0030*(-moon_radial_y) if moon_dist < 7e6 else 0.0)) if moon_dist < 1.35e8 else 0.0",
        ),
        MissionPhase(
            "Retorno geocentrico horario",
            520_000.0,
            FrameType.XY,
            f"((-{return_radial_gain}*x/r) + ({retro_gain}*y/r if hz_earth > -6e10 else 0.0)) if (moon_vrel_r < -50 and moon_dist < 2.7e8) or r > 1.6e8 else 0.0",
            f"((-{return_radial_gain}*y/r) + (-{retro_gain}*x/r if hz_earth > -6e10 else 0.0)) if (moon_vrel_r < -50 and moon_dist < 2.7e8) or r > 1.6e8 else 0.0",
        ),
        MissionPhase(
            "Afinado periapsis terrestre",
            320_000.0,
            FrameType.XY,
            f"(({periapsis_gain}*x/r) if (earth_vr < -120 and earth_dist < 3.00e8) else ((-0.0020*x/r) if (earth_dist > 3.20e8) else 0.0))",
            f"(({periapsis_gain}*y/r) if (earth_vr < -120 and earth_dist < 3.00e8) else ((-0.0020*y/r) if (earth_dist > 3.20e8) else 0.0))",
        ),
        MissionPhase("Costa final de retorno", 80_000.0, FrameType.NONE),
    ]


def moon_distance(sim: SimulationState) -> float:
    dx = sim.rocket.position_xy[0] - sim.moon.position_xy[0]
    dy = sim.rocket.position_xy[1] - sim.moon.position_xy[1]
    return math.hypot(dx, dy)


def run_case(
    moon_angle_deg: float,
    tli_duration_s: float,
    tli_gain: float,
    tli_max_accel: float,
    target_a_m: float,
    guide_gain: float,
    behind_gain: float,
    return_radial_gain: float,
    retro_gain: float,
    periapsis_gain: float,
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
    for phase in build_phases(
        tli_duration_s,
        tli_gain,
        tli_max_accel,
        target_a_m,
        guide_gain,
        behind_gain,
        return_radial_gain,
        retro_gain,
        periapsis_gain,
    ):
        sim.queue_phase(phase)

    post_tli_start_s = 86_400.0 + tli_duration_s
    min_moon_m = float("inf")
    min_moon_time_s = 0.0
    min_moon_behind = 0.0
    hz_before_flyby = 0.0
    hz_after_flyby = 0.0
    saw_lunar_neighborhood = False
    passed_perilune = False
    min_earth_return_radius_m = float("inf")
    return_start_s = 0.0

    while sim.phase_manager.pending or sim.phase_manager.active is not None:
        sim.resume()
        while sim.is_running:
            sim.update_step()
            hz = sim.earth_angular_momentum_z()
            dist_moon = moon_distance(sim)

            if sim.sim_time_s >= post_tli_start_s:
                if dist_moon < 1.4e8 and not saw_lunar_neighborhood:
                    hz_before_flyby = hz
                    saw_lunar_neighborhood = True
                if dist_moon < min_moon_m:
                    min_moon_m = dist_moon
                    min_moon_time_s = sim.sim_time_s
                    min_moon_behind = sim._current_behind_score()
                elif min_moon_m < float("inf") and sim.sim_time_s > min_moon_time_s + 3_600.0:
                    passed_perilune = True

                if passed_perilune:
                    hz_after_flyby = hz
                    return_start_s = return_start_s or sim.sim_time_s
                    min_earth_return_radius_m = min(min_earth_return_radius_m, magnitude(sim.rocket.position_xy))

            if sim.termination_reason:
                break
        if sim.termination_reason:
            break

    if min_moon_m == float("inf"):
        min_moon_m = 1e99
    if min_earth_return_radius_m == float("inf"):
        min_earth_return_radius_m = magnitude(sim.rocket.position_xy)

    min_return_altitude_m = min_earth_return_radius_m - EARTH_RADIUS_M

    if min_moon_m < 5e6:
        moon_penalty = 200.0 + (5e6 - min_moon_m) / 1e6
    elif min_moon_m > 2e7:
        moon_penalty = (min_moon_m - 2e7) / 1e6
    else:
        moon_penalty = 0.0

    if min_return_altitude_m < 5e5:
        periapsis_penalty = 200.0 + (5e5 - min_return_altitude_m) / 1e5
    elif min_return_altitude_m > 1e7:
        periapsis_penalty = (min_return_altitude_m - 1e7) / 1e6
    else:
        periapsis_penalty = 0.0

    impact_penalty = 1000.0 if sim.termination_reason else 0.0
    behind_penalty = max(0.0, min_moon_behind + 0.10) * 80.0
    outbound_spin_penalty = 120.0 if hz_before_flyby <= 0.0 else 0.0
    return_spin_penalty = 120.0 if hz_after_flyby >= 0.0 else 0.0
    no_flyby_penalty = 250.0 if not saw_lunar_neighborhood else 0.0

    score = (
        moon_penalty
        + periapsis_penalty
        + impact_penalty
        + behind_penalty
        + outbound_spin_penalty
        + return_spin_penalty
        + no_flyby_penalty
    )

    return {
        "score": score,
        "moon_angle_deg": moon_angle_deg,
        "tli_duration_s": tli_duration_s,
        "tli_gain": tli_gain,
        "tli_max_accel": tli_max_accel,
        "target_a_m": target_a_m,
        "guide_gain": guide_gain,
        "behind_gain": behind_gain,
        "return_radial_gain": return_radial_gain,
        "retro_gain": retro_gain,
        "periapsis_gain": periapsis_gain,
        "time_to_perilune_s": min_moon_time_s,
        "min_moon_distance_m": min_moon_m,
        "behind_score": min_moon_behind,
        "hz_earth_before_flyby": hz_before_flyby,
        "hz_earth_after_flyby": hz_after_flyby,
        "min_earth_return_altitude_m": min_return_altitude_m,
        "mission_time_s": sim.sim_time_s,
        "return_start_s": return_start_s,
        "termination": sim.termination_reason,
    }


def main() -> None:
    best: dict[str, float | str | None] | None = None
    for moon_angle in [204.0, 206.0, 208.0]:
        for tli_duration in [620.0, 650.0]:
            for tli_gain in [0.025, 0.030]:
                for tli_max in [9.0]:
                    for target_a in [235_000_000.0, 245_000_000.0]:
                        for guide_gain in [0.00035]:
                            for behind_gain in [0.0012, 0.0014, 0.0016]:
                                for return_radial_gain in [0.0040, 0.0060]:
                                    for retro_gain in [0.0040]:
                                        for periapsis_gain in [0.0268, 0.0280]:
                                            result = run_case(
                                                moon_angle,
                                                tli_duration,
                                                tli_gain,
                                                tli_max,
                                                target_a,
                                                guide_gain,
                                                behind_gain,
                                                return_radial_gain,
                                                retro_gain,
                                                periapsis_gain,
                                            )
                                            if best is None or float(result["score"]) < float(best["score"]):
                                                best = result

    assert best is not None
    print("=== Toy Free Return Retrograde Sweep ===")
    print(f"score={float(best['score']):.3f}")
    print(f"moon_angle_deg={best['moon_angle_deg']}")
    print(f"tli_duration_s={best['tli_duration_s']}")
    print(f"tli_gain={best['tli_gain']}")
    print(f"tli_max_accel={best['tli_max_accel']}")
    print(f"target_a_m={best['target_a_m']}")
    print(f"guide_gain={best['guide_gain']}")
    print(f"behind_gain={best['behind_gain']}")
    print(f"return_radial_gain={best['return_radial_gain']}")
    print(f"retro_gain={best['retro_gain']}")
    print(f"periapsis_gain={best['periapsis_gain']}")
    print(f"time_to_perilune_days={float(best['time_to_perilune_s']) / 86400.0:.3f}")
    print(f"min_moon_distance_m={float(best['min_moon_distance_m']):.1f}")
    print(f"behind_score={float(best['behind_score']):.3f}")
    print(f"hz_earth_before_flyby={float(best['hz_earth_before_flyby']):.3e}")
    print(f"hz_earth_after_flyby={float(best['hz_earth_after_flyby']):.3e}")
    print(f"min_earth_return_altitude_m={float(best['min_earth_return_altitude_m']):.1f}")
    print(f"mission_time_days={float(best['mission_time_s']) / 86400.0:.3f}")
    print(f"termination={best['termination']}")
    print("\nSuggested sequence:")
    for phase in build_phases(
        float(best["tli_duration_s"]),
        float(best["tli_gain"]),
        float(best["tli_max_accel"]),
        float(best["target_a_m"]),
        float(best["guide_gain"]),
        float(best["behind_gain"]),
        float(best["return_radial_gain"]),
        float(best["retro_gain"]),
        float(best["periapsis_gain"]),
    ):
        print(f"- {phase.label}: duration={phase.duration_s}, frame={phase.frame.value}, primary={phase.primary_expr}, secondary={phase.secondary_expr}")


if __name__ == "__main__":
    main()
