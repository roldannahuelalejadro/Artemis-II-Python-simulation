# core/physics/kepler.py
import numpy as np
from config.constants import a, e, n

def solve_kepler(M: float, e: float, tol=1e-10, max_iter=50) -> float:
    """Resuelve la ecuación de Kepler con método de Newton."""
    E = M
    for _ in range(max_iter):
        delta = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E -= delta
        if abs(delta) < tol:
            break
    return E


def get_moon_pos(t: float, initial_angle: float = 0.0) -> np.ndarray:
    """
    Calcula posición de la Luna en el tiempo t con ángulo inicial configurable.
    
    Args:
        t: tiempo de simulación (segundos)
        initial_angle: ángulo inicial en radianes (0 = sobre el eje +x)
    
    Returns:
        np.ndarray: posición [x, y] en metros
    """
    # Anomalía media con offset inicial
    M = n * t + initial_angle
    
    E = solve_kepler(M, e)
    
    # Anomalía verdadera
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    
    # Radio
    r = a * (1 - e * np.cos(E))
    
    # Posición en coordenadas cartesianas
    x = r * np.cos(nu)
    y = r * np.sin(nu)
    
    return np.array([x, y], dtype='f8')