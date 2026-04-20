# core/entities/celestial.py
import numpy as np
from config.constants import R_EARTH, R_MOON, a
from ..physics.kepler import get_moon_pos

class Earth:
    def __init__(self):
        self.pos = np.zeros(2, dtype='f8')
        self.radius = R_EARTH
        self.frozen = True

    def update(self, sim_time: float, is_running: bool):
        pass  # Tierra siempre en (0,0)


class Moon:
    def __init__(self, initial_angle: float = 0.0):
        self.initial_angle = initial_angle
        self.radius = R_MOON
        self.pos = get_moon_pos(0.0, initial_angle)
        self.frozen = True
        self.trail = []

    def update(self, sim_time: float, is_running: bool):
        """Actualiza posición de la Luna"""
        if not is_running or self.frozen:
            # Mantener posición inicial hasta que inicie la simulación
            self.pos = get_moon_pos(0.0, self.initial_angle)
        else:
            # Luna en movimiento real
            self.pos = get_moon_pos(sim_time, self.initial_angle)

        # Trail de la Luna (en unidades de DIST_SCALE)
        self.trail.append(self.pos.copy() / 1e9)
        if len(self.trail) > 1200:
            self.trail.pop(0)