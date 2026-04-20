# core/physics/thrust.py
import numpy as np
from utils.safe_eval import safe_eval
from .control import ThrustController

class ThrustProfile:
    def __init__(self):
        self.thrust_x_expr: str = "0.0"
        self.thrust_y_expr: str = "0.0"
        self.enabled = True
        self.mode: str = "expression"
        
        # Modos inteligentes
        self.hover_target_alt_km: float = 200.0
        self.kp: float = 0.015
        self.kd: float = 0.8
        self.orbit_strength: float = 0.6
        
        # Artemis II phases
        self.phase: int = 0                    # 0=LEO, 1=TLI, 2=Coast, 3=Captura, 4=Órbita lunar, 5=TEI, 6=Regreso, 7=Captura Tierra
        self.phase_start_t: float = 0.0
        
        self.max_thrust_acc: float = 30.0

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == "artemis_phases":
            self.phase = 0
            self.phase_start_t = 0.0
            print("🚀 MODO ARTEMIS II FASES AUTOMÁTICAS ACTIVADO")

    def set_expressions(self, x_expr: str, y_expr: str):
        self.thrust_x_expr = x_expr.strip() or "0.0"
        self.thrust_y_expr = y_expr.strip() or "0.0"
        self.mode = "expression"

    def evaluate(self, t: float, pos: np.ndarray, vel: np.ndarray, moon_pos: np.ndarray = None) -> np.ndarray:
        if not self.enabled:
            return np.zeros(2, dtype='f8')

        if moon_pos is None:
            moon_pos = np.array([3.844e8, 0.0], dtype='f8')

        if self.mode == "artemis_phases":
            self._update_phase(t, pos, vel, moon_pos)
            thrust = self._compute_thrust_by_phase(pos, vel, moon_pos, t)
            print(f"Fase {self.phase} | t={t:.0f} | r={np.linalg.norm(pos)/1e6:.1f} Mm | dist_moon={np.linalg.norm(pos-moon_pos)/1e6:.1f} Mm")  # DEBUG
            return thrust

        elif self.mode == "hover":
            return ThrustController.hover(pos, vel, self.hover_target_alt_km, self.kp, self.kd)
        elif self.mode == "circular_orbit":
            return ThrustController.circular_orbit(pos, vel, self.orbit_strength)
        else:
            ax = safe_eval(self.thrust_x_expr, t, pos, vel)
            ay = safe_eval(self.thrust_y_expr, t, pos, vel)
            return np.array([ax, ay], dtype='f8')

    def _update_phase(self, t: float, pos: np.ndarray, vel: np.ndarray, moon_pos: np.ndarray):
        r = np.linalg.norm(pos)
        dist_moon = np.linalg.norm(pos - moon_pos)

        if self.phase == 0:   # LEO → TLI después de 300 segundos
            if t - self.phase_start_t > 300:
                self.phase = 1
                self.phase_start_t = t
                print("→ Fase 1: TLI (burn prograde)")

        elif self.phase == 1:   # TLI → Coast cuando ya está en elipse grande
            if r > 1.8e8:
                self.phase = 2
                self.phase_start_t = t
                print("→ Fase 2: Coast translunar")

        elif self.phase == 2:   # Coast → Captura lunar
            if dist_moon < 1.5e7:
                self.phase = 3
                self.phase_start_t = t
                print("→ Fase 3: Captura lunar (burn retrograde)")

        elif self.phase == 3:   # Captura → Órbita lunar
            if dist_moon < 5e6 and np.linalg.norm(vel) < 2000:
                self.phase = 4
                self.phase_start_t = t
                print("→ Fase 4: Órbita lunar estabilizada")

        elif self.phase == 4:   # Órbita lunar → TEI después de 1.5 días
            if t - self.phase_start_t > 129600:   # ~1.5 días
                self.phase = 5
                self.phase_start_t = t
                print("→ Fase 5: TEI (escape lunar)")

        elif self.phase == 5:   # TEI → Regreso
            if dist_moon > 1.8e7:
                self.phase = 6
                self.phase_start_t = t
                print("→ Fase 6: Regreso a Tierra")

        elif self.phase == 6:   # Regreso → Captura Tierra
            if r < 1.5e7:
                self.phase = 7
                self.phase_start_t = t
                print("→ Fase 7: Captura terrestre final")

    def _compute_thrust_by_phase(self, pos: np.ndarray, vel: np.ndarray, moon_pos: np.ndarray, t: float):
        speed = np.linalg.norm(vel) + 0.1
        prograde = vel / speed

        if self.phase in (0, 4, 7):          # LEO, órbita lunar, captura Tierra
            return ThrustController.circular_orbit(pos, vel, strength=1.2 if self.phase == 0 else 0.8)
        elif self.phase == 1:                # TLI
            return 35.0 * prograde
        elif self.phase == 3:                # Captura lunar
            return -28.0 * prograde
        elif self.phase == 5:                # TEI
            return 25.0 * prograde
        else:                                # Coast (2 y 6)
            return np.zeros(2, dtype='f8')