# core/physics/control.py
import numpy as np
from config.constants import GM_earth, R_EARTH

class ThrustController:
    """Controladores mejorados para mayor estabilidad"""

    @staticmethod
    def hover(pos: np.ndarray, vel: np.ndarray, target_alt_km: float = 200.0,
              kp: float = 0.008, kd: float = 1.1) -> np.ndarray:
        """
        Hover mucho más estable.
        - Mejor cálculo de gravedad local
        - Ganancias más conservadoras
        - Deadzone y filtro suave
        """
        r = np.linalg.norm(pos)
        if r < R_EARTH * 0.6 or np.isnan(r) or np.isinf(r):
            return np.zeros(2, dtype='f8')

        radial_unit = pos / r

        # Gravedad local exacta
        g_local = GM_earth / r**2
        gravity_vector = -g_local * radial_unit

        # Error de altitud (en metros)
        target_r = R_EARTH + target_alt_km * 1000
        alt_error = target_r - r

        # Velocidad radial (positivo = alejándose del centro)
        radial_vel = np.dot(vel, radial_unit)

        # Deadzone: si está muy cerca del objetivo, no corregir tanto
        if abs(alt_error) < 500:        # menos de 500 metros de error
            kp = kp * 0.3

        # Control PD
        correction = kp * alt_error - kd * radial_vel

        # Filtro suave (evita cambios bruscos)
        correction = np.clip(correction, -8.0, 8.0)

        # Thrust = contrarrestar gravedad + corrección
        thrust = -gravity_vector + correction * radial_unit

        # Límite duro de thrust (seguridad)
        thrust_mag = np.linalg.norm(thrust)
        if thrust_mag > 25.0:
            thrust *= (25.0 / thrust_mag)

        return thrust

    @staticmethod
    def circular_orbit(pos: np.ndarray, vel: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """Mantener órbita circular más suave"""
        r = np.linalg.norm(pos)
        if r < R_EARTH * 1.1:
            return np.zeros(2, dtype='f8')

        v_orbital = np.sqrt(GM_earth / r)
        vel_mag = np.linalg.norm(vel)
        if vel_mag < 5.0:
            return np.zeros(2, dtype='f8')

        prograde = vel / vel_mag
        error = v_orbital - vel_mag

        return strength * error * prograde