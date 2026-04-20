# utils/safe_eval.py
import numpy as np
import math

ALLOWED_NAMES = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "exp": np.exp, "log": np.log, "sqrt": np.sqrt,
    "abs": abs, "pi": np.pi,
    "np": np,
    "atan2": np.arctan2,
    "deg2rad": np.deg2rad,
    "rad2deg": np.rad2deg,
}

def safe_eval(expr: str, t: float = 0.0, pos: np.ndarray = None, vel: np.ndarray = None):
    """Evalúa expresiones de thrust de forma segura.
    Unidades SI: posición en metros, velocidad en m/s, thrust en m/s²"""
    
    if not expr or expr.strip() == "":
        return 0.0

    pos = pos if pos is not None else np.zeros(2)
    vel = vel if vel is not None else np.zeros(2)

    # Variables cómodas para el usuario (más intuitivas)
    ctx = {
        "t": t,                  # tiempo (segundos)
        
        # Posición
        "pos": pos,
        "pos_x": pos[0],
        "pos_y": pos[1],
        "pos_km": pos / 1000,
        
        # Velocidad
        "vel": vel,
        "vel_x": vel[0],
        "vel_y": vel[1],
        "vel_kms": vel / 1000,
        "speed": np.linalg.norm(vel),           # velocidad total en m/s
        "speed_kms": np.linalg.norm(vel) / 1000,
        
        # Altitud aproximada
        "altitude": np.linalg.norm(pos) - 6.371e6,
        "altitude_km": (np.linalg.norm(pos) - 6.371e6) / 1000,
        
        **ALLOWED_NAMES
    }

    try:
        result = eval(expr, {"__builtins__": {}}, ctx)
        return float(result)
    except Exception as e:
        print(f"Warning: Error evaluando '{expr}': {e}")
        return 0.0