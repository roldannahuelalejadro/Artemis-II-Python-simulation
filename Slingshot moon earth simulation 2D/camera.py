# camera.py
import glfw
import numpy as np
from entities import Particle

class Camera:
    def __init__(self):
        self.pos = np.array([0.0, 0.0], dtype='f4')
        self.zoom = 1.5
        self.paused = False

    def process_keyboard(self, window, dt_real, TIME_SCALE):
        """Movimiento WASD"""
        if self.paused:
            return

        speed = 2e-4 * dt_real * TIME_SCALE / self.zoom

        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            self.pos[1] += speed
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            self.pos[1] -= speed
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            self.pos[0] -= speed
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            self.pos[0] += speed

    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

    def reset(self):
        self.pos = np.array([0.0, 0.0], dtype='f4')

    def center_on_earth(self):
        self.pos = np.array([0.0, 0.0], dtype='f4')


# ===================== CALLBACKS =====================
def setup_callbacks(window, camera, mouse_logic=None, manual_vars=None, utils=None):

    def scroll_callback(window, xoff, yoff):
        camera.zoom *= (1 + yoff * 0.1)
        camera.zoom = max(0.1, min(camera.zoom, 20.0))

    def key_callback(window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return

        # ==================== MODO MANUAL ====================
        if manual_vars and key == glfw.KEY_N:
            manual_vars['manual_mode'] = not manual_vars['manual_mode']
            if manual_vars['manual_mode']:
                if not camera.paused:
                    camera.toggle_pause()
                manual_vars['input_str'] = ["0", "0", "1000", "0"]
                manual_vars['selected_param'] = 0
                print("→ MODO MANUAL ACTIVADO (simulación pausada)")
            else:
                print("→ MODO MANUAL DESACTIVADO")
            return

        # Procesar teclas dentro del modo manual
        if manual_vars and manual_vars.get('manual_mode', False):
            current = manual_vars['selected_param']
            input_strs = manual_vars['input_str']

            if key == glfw.KEY_TAB:
                manual_vars['selected_param'] = (manual_vars['selected_param'] + 1) % 4
                return

            elif key == glfw.KEY_ENTER or key == glfw.KEY_KP_ENTER:
                try:
                    x0 = float(input_strs[0])
                    y0 = float(input_strs[1])
                    vx0 = float(input_strs[2])
                    vy0 = float(input_strs[3])
                    particles = manual_vars['particles']
                    particles.append(Particle(
                        np.array([x0, y0], dtype='f4'),
                        np.array([vx0, vy0], dtype='f4')
                    ))
                    print(f"✓ Partícula lanzada → x={x0/1000:,.0f} km, y={y0/1000:,.0f} km | v=({vx0:,.0f}, {vy0:,.0f}) m/s")
                except ValueError:
                    print("Error: Valores numéricos inválidos")
                return

            elif key == glfw.KEY_ESCAPE:
                manual_vars['manual_mode'] = False
                print("→ Saliendo del modo manual")
                return

            elif key == glfw.KEY_BACKSPACE:
                if input_strs[current]:
                    input_strs[current] = input_strs[current][:-1]
                if not input_strs[current]:
                    input_strs[current] = "0"
                return

            # Números
            elif glfw.KEY_0 <= key <= glfw.KEY_9 or glfw.KEY_KP_0 <= key <= glfw.KEY_KP_9:
                digit = str(key - glfw.KEY_0) if glfw.KEY_0 <= key <= glfw.KEY_9 else str(key - glfw.KEY_KP_0)
                if input_strs[current] == "0" and digit != "0":
                    input_strs[current] = digit
                else:
                    input_strs[current] += digit
                return

            # Punto decimal
            elif key == glfw.KEY_PERIOD or key == glfw.KEY_KP_DECIMAL:
                if '.' not in input_strs[current]:
                    input_strs[current] += '.'
                return

            # Signo negativo
            elif key == glfw.KEY_MINUS or key == glfw.KEY_KP_SUBTRACT:
                if input_strs[current] in ("0", ""):
                    input_strs[current] = "-"
                elif input_strs[current] == "-":
                    input_strs[current] = "0"
                return

            return  # No procesar otras teclas mientras estamos en modo manual

        # ==================== TECLAS NORMALES ====================
        if key == glfw.KEY_SPACE:
            is_paused = camera.toggle_pause()
            print("PAUSA" if is_paused else "Simulación reanudada")

        elif key == glfw.KEY_C:
            camera.center_on_earth()
            print("Cámara centrada en la Tierra")

        elif key == glfw.KEY_R:
            if utils and 'reset' in utils:
                utils['reset']()

        # ==================== CONTROL DE THRUST ====================
        elif key == glfw.KEY_T:
            if particles:  # si hay partículas
                # Tomamos la última partícula lanzada
                p = particles[-1]
                p.thrust_active = not p.thrust_active
                print(f"Thrust {'ACTIVADO' if p.thrust_active else 'DESACTIVADO'} en partícula {len(particles)}")
            return

        # Control de dirección y potencia del thrust (solo si hay partículas)
        if particles and particles[-1].thrust_active:
            p = particles[-1]
            thrust_mag = 0.5   # m/s² base (podés ajustarlo)

            if key == glfw.KEY_UP:
                p.set_thrust(0, thrust_mag)
            elif key == glfw.KEY_DOWN:
                p.set_thrust(0, -thrust_mag)
            elif key == glfw.KEY_LEFT:
                p.set_thrust(-thrust_mag, 0)
            elif key == glfw.KEY_RIGHT:
                p.set_thrust(thrust_mag, 0)
            elif key == glfw.KEY_KP_ADD or key == glfw.KEY_EQUAL:
                # aumentar potencia
                p.thrust *= 1.5
                print(f"Thrust aumentado → {np.linalg.norm(p.thrust):.2f} m/s²")
            elif key == glfw.KEY_KP_SUBTRACT or key == glfw.KEY_MINUS:
                p.thrust *= 0.7
                print(f"Thrust reducido → {np.linalg.norm(p.thrust):.2f} m/s²")
                
    # ==================== Mouse Callbacks ====================
    def mouse_button_callback(window, button, action, mods):
        if mouse_logic and 'button' in mouse_logic:
            mouse_logic['button'](button, action, mods)

    def cursor_pos_callback(window, x, y):
        if mouse_logic and 'cursor' in mouse_logic:
            mouse_logic['cursor'](x, y)

    # Asignar los callbacks
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    
    return key_callback
