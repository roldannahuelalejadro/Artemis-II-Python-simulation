# main.py
import glfw
import moderngl
import numpy as np
import time
import sys

from config import *
from entities import Particle
from rendering import Renderer

# ===================== INIT =====================
if not glfw.init():
    print("Failed to initialize GLFW")
    sys.exit(1)

window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Tierra-Luna 2D - Trails", None, None)
if not window:
    glfw.terminate()
    sys.exit(1)

glfw.make_context_current(window)

ctx = moderngl.create_context()

# ===================== OBJETOS =====================
camera = type('Camera', (), {'pos': np.array([0.0, 0.0], dtype='f4'), 'zoom': 1.5})()
renderer = Renderer(ctx)

luna_trail = []
particles = []

dragging = False
drag_start = None
drag_current = None

GM = G * mT
mu = G * (mT + mL)
n = np.sqrt(mu / a**3)

def solve_kepler(M, e):
    E = M
    for _ in range(10):
        E -= (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E

def moon_pos(t):
    M = n * t
    E = solve_kepler(M, e)
    r = a * (1 - e * np.cos(E))
    th = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    return np.array([r * np.cos(th), r * np.sin(th)])

# ===================== CALLBACKS =====================
def scroll_callback(window, xoff, yoff):
    camera.zoom *= (1 + yoff * 0.1)
    camera.zoom = max(0.1, min(camera.zoom, 20.0))

glfw.set_scroll_callback(window, scroll_callback)

def mouse_click(window, button, action, mods):
    global dragging, drag_start, drag_current

    if button == glfw.MOUSE_BUTTON_LEFT:
        x, y = glfw.get_cursor_pos(window)
        w, h = glfw.get_window_size(window)

        nx = (x / w) * 2 - 1
        ny = 1 - (y / h) * 2
        world_pos = (np.array([nx, ny]) / camera.zoom + camera.pos) * DIST_SCALE

        if action == glfw.PRESS:
            dragging = True
            drag_start = world_pos.copy()
            drag_current = world_pos.copy()

        elif action == glfw.RELEASE and drag_start is not None:
            dragging = False
            x, y = glfw.get_cursor_pos(window)
            nx = (x / w) * 2 - 1
            ny = 1 - (y / h) * 2
            release_pos = (np.array([nx, ny]) / camera.zoom + camera.pos) * DIST_SCALE

            delta = (release_pos - drag_start) / DIST_SCALE
            v0 = -delta * VEL_FACTOR_SI * camera.zoom

            particles.append(Particle(drag_start, v0))
            print(f"Partícula lanzada | Vel: {v0}")

            drag_start = None
            drag_current = None

glfw.set_mouse_button_callback(window, mouse_click)

def cursor_pos_callback(window, x, y):
    global drag_current
    if dragging and drag_start is not None:
        w, h = glfw.get_window_size(window)
        nx = (x / w) * 2 - 1
        ny = 1 - (y / h) * 2
        drag_current = (np.array([nx, ny]) / camera.zoom + camera.pos) * DIST_SCALE

glfw.set_cursor_pos_callback(window, cursor_pos_callback)

# ===================== MAIN LOOP =====================
t0 = time.time()
t_prev = t0

def format_vec(v):
    return f"({v[0]/1000:,.0f}, {v[1]/1000:,.0f}) km"

while not glfw.window_should_close(window):
    glfw.poll_events()
    ctx.clear(0, 0, 0)

    t_now = time.time()
    dt_real = t_now - t_prev
    dt = dt_real * TIME_SCALE
    t_prev = t_now

    # Input cámara
    speed = 2e-4 * dt / camera.zoom
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS: camera.pos[1] += speed
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS: camera.pos[1] -= speed
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS: camera.pos[0] -= speed
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS: camera.pos[0] += speed

    sim_t = (t_now - t0) * 5000
    mp = moon_pos(sim_t)

    # Trail Luna
    luna_trail.append(mp / DIST_SCALE)
    if len(luna_trail) > MAX_LUNA_TRAIL:
        luna_trail.pop(0)

    # Actualizar partículas
    for p in particles[:]:
        p.update(dt, GM)
        if p.is_colliding_earth():
            particles.remove(p)

    # ===================== RENDER =====================

    # Trail Luna
    renderer.render_luna_trail(luna_trail, camera.pos, camera.zoom)

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

    # Preview de arrastre
    if dragging and drag_start is not None and drag_current is not None:
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

    # Trails de partículas
    for p in particles:
        renderer.render_particle_trail(p.trail, camera.pos, camera.zoom)

    # Partículas (círculos)
    for p in particles:
        renderer.prog['offset'] = tuple(p.pos / DIST_SCALE)
        renderer.prog['scale'] = 2.0e6 / DIST_SCALE
        renderer.prog['cam_pos'] = tuple(camera.pos)
        renderer.prog['zoom'] = camera.zoom
        renderer.prog['color'] = (1.0, 0.3, 0.3)
        renderer.vao_circle.render()

    # ===================== TEXTO =====================
    info = f"t = {sim_t/86400:.2f} días  ({sim_t:,.0f} s)\n"
    info += f"Luna: {format_vec(mp)}\n"
    info += f"Partículas: {len(particles)}\n\n"

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

# Cleanup
if renderer.text_tex is not None:
    renderer.text_tex.release()
glfw.terminate()