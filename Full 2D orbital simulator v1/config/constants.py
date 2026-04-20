# config/constants.py
import numpy as np

# ===================== ESCALA Y UNIDADES =====================
DIST_SCALE = 1e9                    # 1 unidad en pantalla = 1e9 metros (1 millón de km)
G = 6.67430e-11                     # m³ kg⁻¹ s⁻²

# Masas
mT = 5.972e24                       # Tierra (kg)
mL = 7.348e22                       # Luna (kg)

# Parámetros orbitales Luna
a = 384400e3                        # semi-eje mayor (m)
e = 0.0549                          # excentricidad

# Constantes físicas derivadas
GM_earth = G * mT
GM_moon = G * mL
mu = G * (mT + mL)
n = np.sqrt(mu / a**3)              # movimiento medio (rad/s)

# ===================== RADIOS =====================
R_EARTH = 6.371e6                   # Radio Tierra (m)
R_MOON = 1.737e6                    # Radio Luna (m)

# ===================== SIMULACIÓN =====================
TIME_SCALE = 2000.0                 # Aceleración temporal (2000x)
VEL_FACTOR_SI = 4e5                 # Factor para drag inicial (no usado mucho ahora)

MAX_LUNA_TRAIL = 1200
MAX_ROCKET_TRAIL = 2000

# ===================== VENTANA =====================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 1000

# ===================== COLISIONES =====================
COLLISION_EARTH_MARGIN = 100_000    # metros de margen (permite spawn en superficie)
COLLISION_MOON_MARGIN = 50_000