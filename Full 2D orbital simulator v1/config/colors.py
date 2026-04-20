# config/colors.py
"""Paleta de colores para el simulador"""

COLORS = {
    # Cuerpos celestes
    "earth": (0.2, 0.5, 1.0, 1.0),      # Azul Tierra
    "moon": (0.85, 0.85, 0.85, 1.0),    # Gris Luna
    
    # Cohetes y trails
    "rocket": (1.0, 0.35, 0.35, 1.0),   # Rojo brillante
    "rocket_trail": (1.0, 0.6, 0.2, 0.9),
    
    # Elementos predictivos / fantasma
    "predictive": (0.4, 1.0, 0.4, 0.6), # Verde translúcido
    "predictive_line": (0.3, 0.9, 0.3, 0.7),
    
    # UI / HUD
    "text": (1.0, 1.0, 1.0, 1.0),
    "hud_background": (0.0, 0.0, 0.0, 0.7),
    "panel_background": (0.1, 0.1, 0.15, 0.95),
    
    # Thrust vector
    "thrust_arrow": (1.0, 0.8, 0.0, 1.0),
}

# Colores por defecto para nuevos cohetes (ciclo)
ROCKET_COLORS = [
    (1.0, 0.3, 0.3),
    (0.3, 1.0, 0.3),
    (0.3, 0.7, 1.0),
    (1.0, 0.8, 0.2),
    (0.8, 0.3, 1.0),
]