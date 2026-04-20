"""Tracks impulse energy usage, work, and accumulated delta-v estimates."""

from __future__ import annotations

from dataclasses import dataclass, field

from coordinates.frame import Vector, dot, magnitude


@dataclass(slots=True)
class EnergySample:
    phase_label: str
    dt_s: float
    thrust_xy: Vector
    speed_m_s: float
    delta_v_m_s: float
    work_j: float


@dataclass(slots=True)
class EnergyLogger:
    mass_kg: float
    samples: list[EnergySample] = field(default_factory=list)
    total_work_j: float = 0.0
    total_delta_v_m_s: float = 0.0

    def record(self, phase_label: str, thrust_xy: Vector, velocity_xy: Vector, dt_s: float) -> None:
        thrust_mag = magnitude(thrust_xy)
        delta_v = thrust_mag * dt_s
        force_xy = (thrust_xy[0] * self.mass_kg, thrust_xy[1] * self.mass_kg)
        work = dot(force_xy, velocity_xy) * dt_s
        sample = EnergySample(
            phase_label=phase_label,
            dt_s=dt_s,
            thrust_xy=thrust_xy,
            speed_m_s=magnitude(velocity_xy),
            delta_v_m_s=delta_v,
            work_j=work,
        )
        self.samples.append(sample)
        self.total_delta_v_m_s += delta_v
        self.total_work_j += work

    def summary(self) -> dict[str, float]:
        return {
            "samples": float(len(self.samples)),
            "delta_v_m_s": self.total_delta_v_m_s,
            "work_j": self.total_work_j,
        }
