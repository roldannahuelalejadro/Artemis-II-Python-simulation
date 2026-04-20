# ui/hud.py
from config.constants import TIME_SCALE
import numpy as np

class HUD:
    """Información en pantalla (HUD)"""
    def __init__(self):
        self.show_info = True

    def get_info_text(self, simulation, trajectory_manager) -> str:
        state = "▶️ CORRIENDO" if simulation.is_running else "⏸️ PAUSADO"
        
        text = f"Tiempo: {simulation.sim_time/86400:.2f} días  ({simulation.sim_time:,.0f} s)\n"
        text += f"Estado: {state} | Escala: {TIME_SCALE:.0f}x\n"
        text += f"Luna ángulo inicial: {np.rad2deg(simulation.moon.initial_angle):.1f}°\n"
        text += f"Cohetes: {len(simulation.rockets)} | Activos: "
        text += f"{sum(1 for r in simulation.rockets if r.active)}\n\n"

        # Info del cohete seleccionado
        selected = trajectory_manager.get_selected()
        if selected:
            speed = np.linalg.norm(selected.vel)
            text += f"Seleccionado: {selected.name}\n"
            text += f"  Pos: ({selected.pos[0]/1000:,.0f}, {selected.pos[1]/1000:,.0f}) km\n"
            text += f"  Vel: {speed:,.0f} m/s\n"
            text += f"  Max Speed: {selected.max_speed:,.0f} m/s\n"
            
            if selected.thrust_profile.enabled:
                text += f"  Thrust: Activo\n"

        return text