# core/simulation.py
import numpy as np
from .entities.celestial import Earth, Moon
from .entities.rocket import Rocket
from config.constants import TIME_SCALE

class SimulationState:
    def __init__(self):
        self.is_running = False
        self.sim_time = 0.0
        self.dt_real = 0.0
        
        self.earth = Earth()
        self.moon = Moon(initial_angle=0.0)
        self.rockets: list[Rocket] = []

    def start(self):
        self.is_running = True
        self.sim_time = 0.0
        self.moon.frozen = False          # ← Importante: descongelar la Luna
        print("▶️ Simulación INICIADA - Luna en movimiento")

    def pause(self):
        self.is_running = False
        print("⏸️ Simulación PAUSADA")

    def reset(self):
        self.is_running = False
        self.sim_time = 0.0
        self.moon.frozen = True
        self.rockets.clear()
        self.moon.trail.clear()
        print("🔄 Simulación REINICIADA")

    def add_rocket(self, rocket: Rocket):
        self.rockets.append(rocket)

    def update(self, dt_real: float):
        if not self.is_running:
            return

        self.dt_real = dt_real
        dt = dt_real * TIME_SCALE
        self.sim_time += dt

        # Actualizar Luna
        self.moon.update(self.sim_time, self.is_running)

        # Actualizar cohetes
        for rocket in self.rockets[:]:
            rocket.update(dt, self.moon.pos, self.sim_time, self.is_running)
            
            # Chequeo de colisiones
            if rocket.destroy_on_impact:
                if rocket.is_colliding_earth() or rocket.is_colliding_moon(self.moon.pos):
                    rocket.deactivate()