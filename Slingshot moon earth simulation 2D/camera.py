# camera.py
import numpy as np
import glfw
class Camera:
    def __init__(self):
        self.pos = np.array([0.0, 0.0], dtype='f4')
        self.zoom = 1.5

    def process_input(self, window, dt):
        speed = 2e-4 * dt / self.zoom

        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            self.pos[1] += speed
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            self.pos[1] -= speed
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            self.pos[0] -= speed
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            self.pos[0] += speed