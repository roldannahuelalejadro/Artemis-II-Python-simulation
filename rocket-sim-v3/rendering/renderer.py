"""Main rendering orchestration for bodies, rocket, trails, and overlays."""

from __future__ import annotations

from rendering.thrust_visual import thrust_indicator_text
from utils.formatting import format_energy, format_seconds, format_vector


class Renderer:
    """Text renderer placeholder for the architecture-first v3."""

    def render_summary(self, simulation) -> str:
        energy = simulation.energy_logger.summary()
        lines = [
            "Rocket Sim v3",
            f"Tiempo de mision: {format_seconds(simulation.sim_time_s)}",
            f"Posicion cohete: {format_vector(simulation.rocket.position_xy)} m",
            f"Velocidad cohete: {format_vector(simulation.rocket.velocity_xy)} m/s",
            thrust_indicator_text(simulation.rocket.active_thrust_xy),
            f"Delta-v acumulado: {energy['delta_v_m_s']:.2f} m/s",
            f"Energia de impulso: {format_energy(energy['work_j'])}",
        ]
        return "\n".join(lines)
