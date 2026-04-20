"""Owns the single-rocket simulation state and update loop."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from config.constants import DEFAULT_TIME_STEP_S, EARTH_RADIUS_M, MOON_ANGULAR_RATE_RAD_S
from coordinates.frame import FrameType, PolarState, add, magnitude
from core.entities.celestial import create_earth, create_moon
from core.phase import MissionPhase
from core.phase_manager import PhaseManager
from core.physics.gravity import combined_gravity
from core.physics.integrator import symplectic_euler
from core.physics.kepler import (
    circular_speed_for_altitude,
    classify_earth_orbit,
    orbit_quality,
)
from core.rocket import SingleRocket
from core.thrust.frame_converter import to_world_xy
from core.thrust.profile import ThrustContext, ThrustProfile
from trajectory.energy_logger import EnergyLogger


@dataclass(slots=True)
class SimulationState:
    dt_s: float = DEFAULT_TIME_STEP_S
    moon_initial_angle_rad: float = 0.0
    sim_time_s: float = 0.0
    is_running: bool = False
    earth: object = field(init=False)
    moon: object = field(init=False)
    rocket: SingleRocket = field(init=False)
    phase_manager: PhaseManager = field(default_factory=PhaseManager)
    thrust_profile: ThrustProfile = field(default_factory=ThrustProfile)
    energy_logger: EnergyLogger = field(init=False)
    last_completed_phase: MissionPhase | None = None
    termination_reason: str | None = None
    min_moon_distance_m: float = field(default=float("inf"))
    min_moon_distance_time_s: float = 0.0
    min_moon_behind_score: float = 0.0

    def __post_init__(self) -> None:
        self.earth = create_earth()
        self.moon = create_moon(self.sim_time_s, self.moon_initial_angle_rad)
        self.rocket = SingleRocket(position_xy=(EARTH_RADIUS_M, 0.0), velocity_xy=(0.0, 0.0))
        self.energy_logger = EnergyLogger(mass_kg=self.rocket.mass_kg)
        self.termination_reason = None
        self.min_moon_distance_m = float("inf")
        self.min_moon_distance_time_s = 0.0
        self.min_moon_behind_score = 0.0

    def reset(self) -> None:
        self.sim_time_s = 0.0
        self.is_running = False
        self.phase_manager = PhaseManager()
        self.earth = create_earth()
        self.moon = create_moon(self.sim_time_s, self.moon_initial_angle_rad)
        self.rocket = SingleRocket(
            name=self.rocket.name,
            mass_kg=self.rocket.mass_kg,
            position_xy=(EARTH_RADIUS_M, 0.0),
            velocity_xy=(0.0, 0.0),
        )
        self.energy_logger = EnergyLogger(mass_kg=self.rocket.mass_kg)
        self.last_completed_phase = None
        self.termination_reason = None
        self.min_moon_distance_m = float("inf")
        self.min_moon_distance_time_s = 0.0
        self.min_moon_behind_score = 0.0

    def place_rocket_on_surface(
        self,
        theta_deg: float,
        altitude_m: float = 0.0,
        tangential_speed_m_s: float = 0.0,
        radial_speed_m_s: float = 0.0,
    ) -> None:
        theta = math.radians(theta_deg)
        polar = PolarState(radius_m=EARTH_RADIUS_M + altitude_m, theta_rad=theta)
        position = polar.to_xy()
        radial = (math.cos(theta), math.sin(theta))
        tangential = (-math.sin(theta), math.cos(theta))
        velocity = add(
            (radial[0] * radial_speed_m_s, radial[1] * radial_speed_m_s),
            (tangential[0] * tangential_speed_m_s, tangential[1] * tangential_speed_m_s),
        )
        self.rocket.position_xy = position
        self.rocket.velocity_xy = velocity
        self.rocket.reset_trail(self.sim_time_s)
        self.rocket.active_thrust_xy = (0.0, 0.0)
        self.rocket.max_speed_m_s = self.rocket.speed_m_s
        self.energy_logger = EnergyLogger(mass_kg=self.rocket.mass_kg)
        self.termination_reason = None
        self.min_moon_distance_m = float("inf")
        self.min_moon_distance_time_s = self.sim_time_s
        self.min_moon_behind_score = 0.0

    def place_rocket_in_circular_orbit(
        self,
        altitude_m: float,
        theta_deg: float = 0.0,
        prograde_sign: float = 1.0,
    ) -> None:
        tangential_speed = circular_speed_for_altitude(altitude_m) * (1.0 if prograde_sign >= 0.0 else -1.0)
        self.place_rocket_on_surface(
            theta_deg=theta_deg,
            altitude_m=altitude_m,
            tangential_speed_m_s=tangential_speed,
            radial_speed_m_s=0.0,
        )

    def set_moon_angle_deg(self, angle_deg: float) -> None:
        self.moon_initial_angle_rad = math.radians(angle_deg)
        self.moon = create_moon(self.sim_time_s, self.moon_initial_angle_rad)

    def queue_phase(self, phase: MissionPhase) -> None:
        self.phase_manager.queue_phase(phase)

    def clear_phases(self) -> None:
        self.phase_manager = PhaseManager()
        self.is_running = False

    def resume(self) -> bool:
        if self.phase_manager.active is None:
            self.phase_manager.start_next_phase()
        self.is_running = self.phase_manager.active is not None
        return self.is_running

    def pause(self) -> None:
        self.is_running = False

    def _check_collisions(self) -> str | None:
        earth_distance = magnitude(self.rocket.position_xy)
        if earth_distance <= self.earth.radius_m:
            return "Impacto con la Tierra"

        moon_dx = self.rocket.position_xy[0] - self.moon.position_xy[0]
        moon_dy = self.rocket.position_xy[1] - self.moon.position_xy[1]
        moon_distance = math.hypot(moon_dx, moon_dy)
        if moon_distance <= self.moon.radius_m:
            return "Impacto con la Luna"
        return None

    def _update_moon_distance_metric(self) -> None:
        moon_dx = self.rocket.position_xy[0] - self.moon.position_xy[0]
        moon_dy = self.rocket.position_xy[1] - self.moon.position_xy[1]
        moon_distance = math.hypot(moon_dx, moon_dy)
        if moon_distance < self.min_moon_distance_m:
            self.min_moon_distance_m = moon_distance
            self.min_moon_distance_time_s = self.sim_time_s
            self.min_moon_behind_score = self._current_behind_score()

    def _current_behind_score(self) -> float:
        rho_x = self.rocket.position_xy[0] - self.moon.position_xy[0]
        rho_y = self.rocket.position_xy[1] - self.moon.position_xy[1]
        rho_dist = math.hypot(rho_x, rho_y)
        if rho_dist == 0.0:
            return 0.0
        moon_orbit_tangent_x = -self.moon.position_xy[1] / 384_400_000.0
        moon_orbit_tangent_y = self.moon.position_xy[0] / 384_400_000.0
        return (rho_x / rho_dist) * moon_orbit_tangent_x + (rho_y / rho_dist) * moon_orbit_tangent_y

    def earth_angular_momentum_z(self) -> float:
        """Signed Earth-centered angular momentum per unit mass."""
        x, y = self.rocket.position_xy
        vx, vy = self.rocket.velocity_xy
        return x * vy - y * vx

    def geocentric_direction_label(self) -> str:
        hz = self.earth_angular_momentum_z()
        if hz > 0.0:
            return "antihorario"
        if hz < 0.0:
            return "horario"
        return "radial"

    def _snap_to_known_heo_free_return_state(self) -> None:
        """Glue a launch demo onto the calibrated HEO free-return preset.

        The Artemis toy preset first demonstrates ascent to LEO. Once that
        visual orbit is complete, this snap restores the exact HEO initial
        energy used by the already-calibrated toy free-return preset, but keeps
        the current geocentric angle so the trajectory does not visibly jump to
        another side of Earth. The Moon is re-phased to preserve the calibrated
        Moon-spacecraft angular separation from the known setup.
        """
        current_theta_rad = math.atan2(self.rocket.position_xy[1], self.rocket.position_xy[0])
        current_theta_deg = math.degrees(current_theta_rad)

        # The calibrated free-return started with rocket theta=90 deg and Moon
        # angle=206 deg, so the important lunar phasing is a 116 deg lead.
        desired_moon_angle_rad = current_theta_rad + math.radians(206.0 - 90.0)
        self.moon_initial_angle_rad = desired_moon_angle_rad - MOON_ANGULAR_RATE_RAD_S * self.sim_time_s
        self.moon = create_moon(self.sim_time_s, self.moon_initial_angle_rad)
        self.place_rocket_on_surface(
            theta_deg=current_theta_deg,
            altitude_m=185_000.0,
            tangential_speed_m_s=10_590.67,
            radial_speed_m_s=0.0,
        )

    def _apply_phase_completion_action(self, phase: MissionPhase) -> None:
        if phase.label == "Pegado a HEO 24h conocida":
            self._snap_to_known_heo_free_return_state()

    def _abort_mission(self, reason: str) -> None:
        self.is_running = False
        self.rocket.active_thrust_xy = (0.0, 0.0)
        self.phase_manager.active = None
        self.phase_manager.pending.clear()
        self.phase_manager.elapsed_in_phase_s = 0.0
        self.phase_manager.paused_waiting_next_phase = True
        self.termination_reason = reason

    def update_step(self) -> MissionPhase | None:
        self.moon = create_moon(self.sim_time_s, self.moon_initial_angle_rad)
        if not self.is_running or self.phase_manager.active is None:
            return None
        self.termination_reason = None

        phase = self.phase_manager.active
        context = ThrustContext(
            t=self.phase_manager.elapsed_in_phase_s,
            mission_time=self.sim_time_s,
            position_xy=self.rocket.position_xy,
            velocity_xy=self.rocket.velocity_xy,
            moon_position_xy=self.moon.position_xy,
        )
        primary, secondary = self.thrust_profile.evaluate_components(phase, context)
        thrust_xy = to_world_xy(phase.frame, primary, secondary, self.rocket.position_xy, self.rocket.velocity_xy)
        gravity_xy = combined_gravity(self.earth, self.moon, self.rocket.position_xy)
        total_acc_xy = add(gravity_xy, thrust_xy)

        self.rocket.position_xy, self.rocket.velocity_xy = symplectic_euler(
            self.rocket.position_xy,
            self.rocket.velocity_xy,
            total_acc_xy,
            self.dt_s,
        )
        self.rocket.active_thrust_xy = thrust_xy
        self.rocket.store_trail_point(self.sim_time_s + self.dt_s)
        if phase.frame != FrameType.NONE:
            self.energy_logger.record(phase.label, thrust_xy, self.rocket.velocity_xy, self.dt_s)

        self.sim_time_s += self.dt_s
        self.moon = create_moon(self.sim_time_s, self.moon_initial_angle_rad)
        self._update_moon_distance_metric()

        collision = self._check_collisions()
        if collision is not None:
            self._abort_mission(collision)
            return None

        finished = self.phase_manager.advance(self.dt_s)
        if finished is not None:
            self._apply_phase_completion_action(finished)
            self.is_running = False
            self.last_completed_phase = finished
            self.rocket.active_thrust_xy = (0.0, 0.0)
        return finished

    def run_until_pause(self, max_steps: int = 10_000) -> list[str]:
        logs: list[str] = []
        if not self.resume():
            logs.append("No hay fases pendientes para ejecutar.")
            return logs

        for _ in range(max_steps):
            finished = self.update_step()
            if finished is not None:
                logs.append(self.phase_completion_message(finished))
                break
        else:
            logs.append("Se alcanzo el maximo de pasos sin pausar la simulacion.")
        return logs

    def phase_completion_message(self, phase: MissionPhase) -> str:
        orbit_state = classify_earth_orbit(self.rocket.position_xy, self.rocket.velocity_xy)
        return (
            f"Fase '{phase.label}' completa en t={self.sim_time_s:.1f}s | "
            f"posicion={self.rocket.position_xy} | velocidad={self.rocket.velocity_xy} | "
            f"estado orbital={orbit_state}"
        )

    def status_snapshot(self) -> dict[str, object]:
        polar = self.rocket.polar_state
        energy = self.energy_logger.summary()
        quality = orbit_quality(
            self.rocket.position_xy,
            self.rocket.velocity_xy,
            polar.radius_m - EARTH_RADIUS_M,
        )
        return {
            "sim_time_s": self.sim_time_s,
            "rocket_pos": self.rocket.position_xy,
            "rocket_vel": self.rocket.velocity_xy,
            "rocket_speed_m_s": self.rocket.speed_m_s,
            "rocket_radius_m": polar.radius_m,
            "rocket_theta_deg": math.degrees(polar.theta_rad),
            "hz_earth": self.earth_angular_momentum_z(),
            "geocentric_direction": self.geocentric_direction_label(),
            "moon_pos": self.moon.position_xy,
            "thrust_xy": self.rocket.active_thrust_xy,
            "thrust_mag_m_s2": magnitude(self.rocket.active_thrust_xy),
            "phase_label": self.phase_manager.active.label if self.phase_manager.active else None,
            "phase_elapsed_s": self.phase_manager.elapsed_in_phase_s,
            "phase_pending": [phase.label for phase in self.phase_manager.pending],
            "orbit_state": classify_earth_orbit(self.rocket.position_xy, self.rocket.velocity_xy),
            "orbit_altitude_error_m": quality["altitude_error_m"],
            "orbit_speed_error_m_s": quality["speed_error_m_s"],
            "radial_velocity_m_s": quality["radial_velocity_m_s"],
            "delta_v_m_s": energy["delta_v_m_s"],
            "work_j": energy["work_j"],
            "is_running": self.is_running,
            "termination_reason": self.termination_reason,
            "min_moon_distance_m": self.min_moon_distance_m,
            "min_moon_distance_time_s": self.min_moon_distance_time_s,
            "min_moon_behind_score": self.min_moon_behind_score,
        }
