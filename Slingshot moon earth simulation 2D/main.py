# main.py
import glfw
import moderngl
import numpy as np
import time
import sys

from config import *
from entities import Particle
from rendering import Renderer
from camera import Camera, setup_callbacks
from physics import get_moon_pos
from utils import *

# ===================== INIT =====================
if not glfw.init():
    print("Failed to initialize GLFW")
    sys.exit(1)

window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Tierra-Luna 2D - Gravedad Luna", None, None)
if not window:
    glfw.terminate()
    sys.exit(1)

glfw.make_context_current(window)
ctx = moderngl.create_context()

# ===================== OBJETOS =====================
camera = Camera()
renderer = Renderer(ctx)

luna_trail = []
particles = []

dragging = False
drag_start = None
drag_current = None

# Constantes físicas
GM_earth = G * mT
GM_moon = G * mL
mu = G * (mT + mL)
n = np.sqrt(mu / a**3)

# ===================== MANUAL SPAWN =====================
manual_vars = {
    'manual_mode': False,
    'input_str': ["0", "0", "1000", "0"],
    'selected_param': 0,
    'particles': particles
}

# ===================== LÓGICA DE MOUSE =====================
def on_mouse_button(button, action, mods):
    global dragging, drag_start, drag_current
    if button == glfw.MOUSE_BUTTON_LEFT:
        if manual_vars.get('manual_mode', False):
            return

        x, y = glfw.get_cursor_pos(window)
        world_pos = get_world_coords(x, y, camera, WINDOW_WIDTH, WINDOW_HEIGHT)

        if action == glfw.PRESS:
            dragging = True
            drag_start = world_pos
            drag_current = world_pos
        elif action == glfw.RELEASE and dragging:
            vel = (drag_start - world_pos) / (0.016 * VEL_FACTOR_SI)
            particles.append(Particle(drag_start, vel))
            dragging = False
            drag_start = None

def on_cursor_pos(x, y):
    global drag_current
    if dragging:
        drag_current = get_world_coords(x, y, camera, WINDOW_WIDTH, WINDOW_HEIGHT)

# ===================== SETUP CALLBACKS =====================
mouse_logic = {'button': on_mouse_button, 'cursor': on_cursor_pos}
setup_callbacks(window, camera, mouse_logic, manual_vars=manual_vars, utils=None)   # utils=None por ahora

# ===================== MAIN LOOP =====================
t0 = time.time()
t_prev = t0
sim_time = 0.0

while not glfw.window_should_close(window):
    glfw.poll_events()

    ctx.clear(0, 0, 0)
    t_now = time.time()
    dt_real = t_now - t_prev
    t_prev = t_now

    camera.process_keyboard(window, dt_real, TIME_SCALE)

    # Actualización Física
    if not camera.paused and not manual_vars['manual_mode']:
        dt = dt_real * TIME_SCALE
        sim_time += dt
        mp = get_moon_pos(sim_time, n)

        luna_trail.append(mp / DIST_SCALE)
        if len(luna_trail) > MAX_LUNA_TRAIL:
            luna_trail.pop(0)

        for p in particles[:]:
            p.update(dt, np.zeros(2), mp, GM_earth, GM_moon)
            if p.is_colliding_earth() or p.is_colliding_moon(mp):
                particles.remove(p)
    else:
        mp = get_moon_pos(sim_time, n)

    # Renderizado
    renderer.render_luna_trail(luna_trail, camera.pos, camera.zoom)
    for p in particles:
        renderer.render_particle_trail(p.trail, camera.pos, camera.zoom)

    # Tierra
    renderer.prog['offset'] = (0.0, 0.0)
    renderer.prog['scale'] = 6.371e6 / DIST_SCALE
    renderer.prog['cam_pos'] = tuple(camera.pos)
    renderer.prog['zoom'] = camera.zoom
    renderer.prog['color'] = (0.2, 0.5, 1.0)
    renderer.vao_circle.render()

    # Luna
    renderer.prog['offset'] = tuple(mp / DIST_SCALE)
    renderer.prog['scale'] = 1.737e6 / DIST_SCALE
    renderer.prog['cam_pos'] = tuple(camera.pos)
    renderer.prog['zoom'] = camera.zoom
    renderer.prog['color'] = (0.85, 0.85, 0.85)
    renderer.vao_circle.render()

    # Partículas
    for p in particles:
        renderer.prog['offset'] = tuple(p.pos / DIST_SCALE)
        renderer.prog['scale'] = 2.0e6 / DIST_SCALE
        renderer.prog['cam_pos'] = tuple(camera.pos)
        renderer.prog['zoom'] = camera.zoom
        renderer.prog['color'] = (1.0, 0.3, 0.3)
        renderer.vao_circle.render()

    # Preview de arrastre
    if dragging and drag_start is not None and drag_current is not None and not manual_vars['manual_mode']:
        line_points = np.array([
            drag_start[0] / DIST_SCALE, drag_start[1] / DIST_SCALE,
            drag_current[0] / DIST_SCALE, drag_current[1] / DIST_SCALE
        ], dtype='f4')
        renderer.line_vbo.write(line_points.tobytes())
        renderer.prog['offset'] = (0.0, 0.0)
        renderer.prog['scale'] = 1.0
        renderer.prog['cam_pos'] = tuple(camera.pos)
        renderer.prog['zoom'] = camera.zoom
        renderer.prog['color'] = (0.3, 1.0, 0.3)
        renderer.line_vao.render(moderngl.LINES, vertices=2)

    # ===================== UI TEXTO =====================
    status = " [PAUSA]" if camera.paused else ""
    info = f"t = {sim_time/86400:.2f} días  ({sim_time:,.0f} s){status}\n"
    info += f"Luna: {format_vec(mp)}\n"
    info += f"Partículas: {len(particles)}\n\n"

    if manual_vars['manual_mode']:
        fields = ["x₀", "y₀", "vx₀", "vy₀"]
        units = ["m", " m", " m/s", " m/s"]
        values = manual_vars['input_str']

        info += "╔════════════════════════════════════════════╗\n"
        info += "║           MANUAL SPAWN MODE                ║\n"
        info += "╠════════════════════════════════════════════╣\n"
        for i in range(4):
            prefix = "→ " if i == manual_vars['selected_param'] else "   "
            display_val = values[i] if values[i] else "0"
            info += f"║ {prefix}{fields[i]:<3} = {display_val:>12}{units[i]:<8} ║\n"
        info += "╚════════════════════════════════════════════╝\n\n"
        info += "TAB      → Cambiar campo\n"
        info += "0-9 .    → Número / decimal\n"
        info += "-        → Signo negativo\n"
        info += "BACKSPACE→ Borrar\n"
        info += "ENTER    → Lanzar partícula\n"
        info += "ESC      → Salir del modo\n"
    else:
        for i, p in enumerate(particles[:5]):
            speed = np.linalg.norm(p.vel)
            info += f"P{i+1}: {format_vec(p.pos)}  |  v = {speed:,.0f} m/s\n"
        if len(particles) > 5:
            info += f"... y {len(particles)-5} más\n"

    if info != renderer.last_info or renderer.text_tex is None:
        renderer.update_text(info)

    if renderer.text_tex is not None:
        renderer.text_tex.use(0)
        renderer.quad_vao.render()

    glfw.swap_buffers(window)

if renderer.text_tex is not None:
    renderer.text_tex.release()
glfw.terminate()