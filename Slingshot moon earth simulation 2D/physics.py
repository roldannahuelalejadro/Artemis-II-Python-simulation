# physics.py
import numpy as np
from config import a, e

def solve_kepler(M, e):
    """Resuelve la ecuación de Kepler por iteración"""
    E = M
    for _ in range(10):
        E -= (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E


def get_moon_pos(t, n):
    """Calcula posición de la Luna en el tiempo t"""
    M = n * t
    E = solve_kepler(M, e)
    r = a * (1 - e * np.cos(E))
    th = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    return np.array([r * np.cos(th), r * np.sin(th)])