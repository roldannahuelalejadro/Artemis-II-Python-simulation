# trajectory/predictor.py
import numpy as np
from core.entities.rocket import Rocket
from config.constants import DIST_SCALE, R_EARTH

class TrajectoryPredictor:
    """
    Predicción realista de trayectoria futura.
    Incluye:
    - Gravedad Tierra + Luna
    - Thrust completo (como función de t, pos y vel)
    - Avance correcto del tiempo en cada paso
    """

    def __init__(self, steps: int = 650, dt_predict: float = 2.8):
        self.steps = steps
        self.dt_predict = dt_predict

    def compute_ghost_trajectory(self, rocket: Rocket, moon_pos: np.ndarray, sim_time: float) -> list[np.ndarray]:
        """
        Retorna la trayectoria fantasma en unidades de DIST_SCALE.
        Ahora sí usa el thrust futuro correctamente.
        """
        if not rocket.active:
            return []

        ghost_pos = rocket.pos.copy()
        ghost_vel = rocket.vel.copy()

        ghost_trail: list[np.ndarray] = []
        dt = self.dt_predict
        pred_time = sim_time                     # ← tiempo que irá avanzando

        for _ in range(self.steps):
            # === 1. Gravedad (siempre) ===
            acc = self._compute_gravity(ghost_pos, moon_pos)

            # === 2. Thrust con tiempo futuro ===
                        # === 2. Thrust con tiempo futuro ===
            if rocket.thrust_profile.enabled:
                thrust_acc = rocket.thrust_profile.evaluate(pred_time, ghost_pos, ghost_vel, moon_pos)

            # === 3. Integración ===
            ghost_vel += acc * dt
            ghost_pos += ghost_vel * dt

            ghost_trail.append(ghost_pos.copy() / DIST_SCALE)

            # === 4. Avanzar tiempo para el próximo paso ===
            pred_time += dt

            # Condiciones de terminación
            if np.linalg.norm(ghost_pos) < R_EARTH + 100_000:      # impacto Tierra
                break
            if np.linalg.norm(ghost_pos - moon_pos) < 3e6:         # impacto Luna
                break
            if np.linalg.norm(ghost_pos) > 2e9:                    # muy lejos
                break

        return ghost_trail

    def _compute_gravity(self, pos: np.ndarray, moon_pos: np.ndarray) -> np.ndarray:
        """Igual que antes"""
        from config.constants import GM_earth, GM_moon, R_EARTH

        acc = np.zeros(2, dtype='f8')

        r_earth = -pos
        dist_earth = np.linalg.norm(r_earth)
        if dist_earth > R_EARTH * 0.1:
            acc += GM_earth * r_earth / dist_earth**3

        r_moon = moon_pos - pos
        dist_moon = np.linalg.norm(r_moon)
        if dist_moon > 1e6:
            acc += GM_moon * r_moon / dist_moon**3

        return acc