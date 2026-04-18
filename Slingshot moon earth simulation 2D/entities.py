# entities.py
import numpy as np
from config import DIST_SCALE, MAX_PARTICLE_TRAIL

class Particle:
    def __init__(self, pos, vel):
        self.pos = pos.copy()
        self.vel = vel.copy()
        self.trail = [pos.copy() / DIST_SCALE]

    def update(self, dt, GM):
        dist = np.linalg.norm(self.pos)
        if dist > 1e6:
            acc = -GM * self.pos / dist**3
        else:
            acc = np.zeros(2)

        self.vel += acc * dt
        self.pos += self.vel * dt

        # Actualizar trail
        self.trail.append(self.pos.copy() / DIST_SCALE)
        if len(self.trail) > MAX_PARTICLE_TRAIL:
            self.trail.pop(0)

    def is_colliding_earth(self):
        return np.linalg.norm(self.pos) < 6.5e6