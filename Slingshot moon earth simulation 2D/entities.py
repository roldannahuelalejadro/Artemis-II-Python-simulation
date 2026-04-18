# entities.py
import numpy as np
from config import DIST_SCALE, MAX_PARTICLE_TRAIL

class Particle:
    def __init__(self, pos, vel):
        self.pos = pos.copy()
        self.vel = vel.copy()
        self.trail = [pos.copy() / DIST_SCALE]

    def update(self, dt, pos_earth, pos_moon, GM_earth, GM_moon):
        """Actualiza usando gravedad de Tierra + Luna"""
        # Vector desde partícula a Tierra
        r_earth = pos_earth - self.pos
        dist_earth = np.linalg.norm(r_earth)
        
        # Vector desde partícula a Luna
        r_moon = pos_moon - self.pos
        dist_moon = np.linalg.norm(r_moon)

        acc = np.zeros(2)

        # Gravedad de la Tierra
        if dist_earth > 1e6:
            acc += GM_earth * r_earth / dist_earth**3

        # Gravedad de la Luna
        if dist_moon > 1e6:                    # evitar singularidad
            acc += GM_moon * r_moon / dist_moon**3

        # Integración Symplectic Euler
        self.vel += acc * dt
        self.pos += self.vel * dt

        # Actualizar trail
        self.trail.append(self.pos.copy() / DIST_SCALE)
        if len(self.trail) > MAX_PARTICLE_TRAIL:
            self.trail.pop(0)

    def is_colliding_earth(self):
        return np.linalg.norm(self.pos) < 6.5e6

    def is_colliding_moon(self, pos_moon):
        return np.linalg.norm(self.pos - pos_moon) < 2.0e6   # radio aproximado de la Luna + margen