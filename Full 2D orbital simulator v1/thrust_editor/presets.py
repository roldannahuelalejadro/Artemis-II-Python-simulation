# thrust_editor/presets.py
"""Presets mejorados y estables"""

PRESETS = {
    "Ninguno": {"x": "0.0", "y": "0.0"},

    "Ascenso Vertical Suave": {
        "x": "0.0",
        "y": "25 * (t < 200)"
    },

    "Ascenso Vertical Realista": {
        "x": "0.0",
        "y": "35 * (t < 150)"
    },

    # Preset recomendado - más estable
    "→ Órbita Circular Baja (LEO)": {
        "x": "0.0",
        "y": "25 * (t < 160) + 1600 * (vel[1] / (np.linalg.norm(vel) + 50)) * (altitude_km > 150)"
    },

    "Burn Prograde Suave": {
        "x": "1200 * (vel[0] / (np.linalg.norm(vel) + 20))",
        "y": "1200 * (vel[1] / (np.linalg.norm(vel) + 20))"
    },

    "Burn Prograde Fuerte": {
        "x": "2800 * (vel[0] / (np.linalg.norm(vel) + 20))",
        "y": "2800 * (vel[1] / (np.linalg.norm(vel) + 20))"
    },

    "Burn Radial (hacia afuera)": {
        "x": "800 * (pos[0] / (np.linalg.norm(pos) + 100000))",
        "y": "800 * (pos[1] / (np.linalg.norm(pos) + 100000))"
    },

    "Sinusoidal Suave": {
        "x": "300 * sin(2 * np.pi * t / 600)",
        "y": "250 * cos(2 * np.pi * t / 800)"
    },

    "Hover Estable (200 km)": {
        "mode": "hover",
        "target_alt_km": 200.0
    },

    "Hover Bajo (50 km)": {
        "mode": "hover",
        "target_alt_km": 50.0
    },

    "Mantener Órbita Circular": {
        "mode": "circular_orbit"
    },
        "Artemis II - Fases Automáticas": {
        "mode": "artemis_phases"
    },

}