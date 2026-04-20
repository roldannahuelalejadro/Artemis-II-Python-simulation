# config/defaults.py
from .constants import R_EARTH

DEFAULTS = {
    # Configuración inicial Luna
    "moon_initial_angle_deg": 0.0,
    "moon_initial_angle_rad": 0.0,
    
    # Spawn por defecto de cohete (superficie + órbita baja)
    "rocket": {
        "x0": 0.0,
        "y0": R_EARTH + 200_000,        # 200 km de altura
        "vx0": 0.0,
        "vy0": 7800.0,                  # velocidad orbital aproximada LEO
    },
    
    # Thrust por defecto
    "thrust_x": "0.0",
    "thrust_y": "0.0",
    
    "rocket_color": (1.0, 0.3, 0.3),
}