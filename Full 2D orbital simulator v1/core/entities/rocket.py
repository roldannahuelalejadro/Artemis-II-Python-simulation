# core/entities/rocket.py
import numpy as np
from config.constants import R_EARTH, COLLISION_EARTH_MARGIN, COLLISION_MOON_MARGIN, MAX_ROCKET_TRAIL, R_MOON
from ..physics.thrust import ThrustProfile


class Rocket:
    """
    Representa un cohete con control total vía funciones de thrust.
    Puede spawnear directamente en la superficie de la Tierra.
    """
    def __init__(self, 
                 pos: np.ndarray,
                 vel: np.ndarray,
                 name: str = "Rocket",
                 color: tuple = (1.0, 0.35, 0.35)):
        
        self.pos = np.array(pos, dtype='f8')
        self.vel = np.array(vel, dtype='f8')
        self.name = name
        self.color = color
        
        # Thrust
        self.thrust_profile = ThrustProfile()  # se edita luego desde UI
        
        # Estado
        self.active = True
        self.destroy_on_impact = True
        
        # Trail
        self.trail = [self.pos.copy() / 1e9]   # en unidades de DIST_SCALE
        
        # Estadísticas
        self.max_speed = 0.0

    def update(self, dt: float, moon_pos: np.ndarray, sim_time: float, is_running: bool):
        """Actualiza física del cohete"""
        if not self.active or not is_running:
            return

        # === 1. Gravedad ===
        acc = self._compute_gravity(moon_pos)

        # === 2. Thrust (función del usuario) ===
                # === 2. Thrust (función del usuario) ===
        thrust_acc = self.thrust_profile.evaluate(sim_time, self.pos, self.vel, moon_pos)
        acc += thrust_acc

        # === 3. Integración (Symplectic Euler - simple y estable) ===
        self.vel += acc * dt
        self.pos += self.vel * dt

        # Actualizar estadísticas
        speed = np.linalg.norm(self.vel)
        if speed > self.max_speed:
            self.max_speed = speed

        # === 4. Trail ===
        self.trail.append(self.pos.copy() / 1e9)
        if len(self.trail) > MAX_ROCKET_TRAIL:
            self.trail.pop(0)

    def _compute_gravity(self, moon_pos: np.ndarray) -> np.ndarray:
        """Gravedad de Tierra + Luna"""
        from config.constants import GM_earth, GM_moon

        acc = np.zeros(2, dtype='f8')

        # Tierra
        r_earth = -self.pos
        dist_earth = np.linalg.norm(r_earth)
        if dist_earth > R_EARTH * 0.1:
            acc += GM_earth * r_earth / dist_earth**3

        # Luna
        r_moon = moon_pos - self.pos
        dist_moon = np.linalg.norm(r_moon)
        if dist_moon > 1e6:
            acc += GM_moon * r_moon / dist_moon**3

        return acc

    def is_colliding_earth(self) -> bool:
        """Colisión con Tierra (con margen para permitir despegue)"""
        dist = np.linalg.norm(self.pos)
        return dist < (R_EARTH + COLLISION_EARTH_MARGIN)

    def is_colliding_moon(self, moon_pos: np.ndarray) -> bool:
        """Colisión con Luna"""
        dist = np.linalg.norm(self.pos - moon_pos)
        return dist < (R_MOON + COLLISION_MOON_MARGIN)

    def deactivate(self):
        self.active = False