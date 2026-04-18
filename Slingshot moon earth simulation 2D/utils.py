# utils.py
import numpy as np
from config import DIST_SCALE

def format_vec(v):
    """Formatea vector en kilómetros"""
    return f"({v[0]/1000:,.0f}, {v[1]/1000:,.0f}) km"


def get_world_coords(x, y, camera, WINDOW_WIDTH, WINDOW_HEIGHT):
    """Convierte píxeles de pantalla a coordenadas del mundo"""
    nx = (2.0 * x / WINDOW_WIDTH - 1.0) / camera.zoom + camera.pos[0]
    ny = (1.0 - 2.0 * y / WINDOW_HEIGHT) / camera.zoom + camera.pos[1]
    return np.array([nx * DIST_SCALE, ny * DIST_SCALE])


def reset_simulation(sim_time_ref, particles, luna_trail, camera):
    """Resetea toda la simulación"""
    sim_time_ref[0] = 0.0
    particles.clear()
    luna_trail.clear()
    camera.reset()
    print("Simulación reiniciada")