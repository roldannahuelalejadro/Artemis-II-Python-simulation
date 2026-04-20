"""Single rocket entity with kinematics, thrust state, and telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field

from config.constants import DEFAULT_ROCKET_MASS_KG, TRAIL_MAX_POINTS, TRAIL_SAMPLE_DT_S
from coordinates.frame import PolarState, Vector, magnitude


@dataclass(slots=True)
class SingleRocket:
    name: str = "Explorer-1"
    mass_kg: float = DEFAULT_ROCKET_MASS_KG
    position_xy: Vector = (0.0, 0.0)
    velocity_xy: Vector = (0.0, 0.0)
    active_thrust_xy: Vector = (0.0, 0.0)
    trail: list[Vector] = field(default_factory=list)
    trail_times_s: list[float] = field(default_factory=list)
    trail_sample_dt_s: float = TRAIL_SAMPLE_DT_S
    trail_max_points: int = TRAIL_MAX_POINTS
    last_trail_sample_time_s: float = 0.0
    max_speed_m_s: float = 0.0

    def __post_init__(self) -> None:
        if not self.trail:
            self.trail.append(self.position_xy)
        if not self.trail_times_s:
            self.trail_times_s.append(0.0)

    @property
    def speed_m_s(self) -> float:
        return magnitude(self.velocity_xy)

    @property
    def polar_state(self) -> PolarState:
        return PolarState.from_xy(self.position_xy)

    def reset_trail(self, sim_time_s: float = 0.0) -> None:
        self.trail = [self.position_xy]
        self.trail_times_s = [sim_time_s]
        self.last_trail_sample_time_s = sim_time_s

    def store_trail_point(self, sim_time_s: float) -> None:
        if self.trail and sim_time_s - self.last_trail_sample_time_s < self.trail_sample_dt_s:
            self.max_speed_m_s = max(self.max_speed_m_s, self.speed_m_s)
            return
        self.trail.append(self.position_xy)
        self.trail_times_s.append(sim_time_s)
        self.last_trail_sample_time_s = sim_time_s
        if len(self.trail) > self.trail_max_points:
            self.trail.pop(0)
            self.trail_times_s.pop(0)
        self.max_speed_m_s = max(self.max_speed_m_s, self.speed_m_s)
