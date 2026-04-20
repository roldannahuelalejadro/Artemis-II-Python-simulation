# camera/camera.py
import glfw
import numpy as np

class Camera:
    def __init__(self):
        self.pos = np.array([0.0, 0.0], dtype='f4')
        self.zoom = 1.8
        self.move_speed = 1.0
        self.zoom_speed = 0.8

        # Modo seguimiento
        self.follow_target = None      # Rocket que se está siguiendo
        self.follow_zoom = 12.0        # Zoom ideal cuando seguimos un cohete (ajustable)
        self.follow_smooth = 0.12      # Factor de suavizado (más bajo = más suave)

    def process_keyboard(self, window, dt_real: float):
        """Movimiento manual WASD + Zoom Q/E (solo si NO estamos siguiendo)"""
        if self.follow_target is not None:
            return  # El seguimiento tiene prioridad

        speed = self.move_speed * dt_real / self.zoom

        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            self.pos[1] += speed
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            self.pos[1] -= speed
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            self.pos[0] -= speed
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            self.pos[0] += speed

        if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
            self.zoom *= (1 + self.zoom_speed * dt_real)
        if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
            self.zoom /= (1 + self.zoom_speed * dt_real)

        self.zoom = max(0.05, min(self.zoom, 50.0))

    def update_follow(self, dt_real: float):
        """Actualiza la cámara para seguir al cohete seleccionado"""
        if self.follow_target is None:
            return

        # Seguir la posición del cohete de forma suave
        target_pos = self.follow_target.pos.copy() / 1e9   # convertir a unidades DIST_SCALE
        self.pos += (target_pos - self.pos) * self.follow_smooth

        # Zoom suave hacia el valor ideal
        self.zoom += (self.follow_zoom - self.zoom) * 0.08

    def set_follow_target(self, rocket):
        """Activa el seguimiento de un cohete"""
        self.follow_target = rocket
        if rocket is not None:
            print(f"📍 Siguiendo cohete: {rocket.name}")
        else:
            print("📍 Seguimiento desactivado")

    def stop_follow(self):
        """Desactiva el seguimiento"""
        self.follow_target = None