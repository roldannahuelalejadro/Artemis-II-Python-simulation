import glfw
import moderngl
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

# ===================== INIT =====================
glfw.init()
window = glfw.create_window(1000, 1000, "Tierra-Luna 2D (SI)", None, None)
glfw.make_context_current(window)

ctx = moderngl.create_context()

# ===================== VIEW =====================
camera_pos = np.array([0.0, 0.0], dtype='f4')
zoom = 1.5

def process_input(window, dt):
    global camera_pos
    speed = 2e-5 * dt / zoom   # velocidad en metros

    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        camera_pos[1] += speed
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        camera_pos[1] -= speed
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        camera_pos[0] -= speed
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        camera_pos[0] += speed

def scroll_callback(window, xoff, yoff):
    global zoom
    zoom *= (1 + yoff * 0.1)
    zoom = max(0.1, min(zoom, 20.0))

glfw.set_scroll_callback(window, scroll_callback)

# ===================== SHADER =====================
prog = ctx.program(
    vertex_shader="""
    #version 330
    in vec2 in_pos;

    uniform vec2 offset;
    uniform float scale;
    uniform vec2 cam_pos;
    uniform float zoom;

    void main() {
        vec2 world = in_pos * scale + offset;
        vec2 view = (world - cam_pos) * zoom;
        gl_Position = vec4(view, 0.0, 1.0);
    }
    """,
    fragment_shader="""
    #version 330
    uniform vec3 color;
    out vec4 fragColor;
    void main() {
        fragColor = vec4(color, 1.0);
    }
    """
)

# =================== TEXT SHADER =======================

text_prog = ctx.program(
    vertex_shader="""
    #version 330
    in vec2 in_pos;
    in vec2 in_uv;

    out vec2 uv;

    void main() {
        uv = in_uv;
        gl_Position = vec4(in_pos, 0.0, 1.0);
    }
    """,
    fragment_shader="""
    #version 330
    in vec2 uv;
    uniform sampler2D tex;
    out vec4 fragColor;

    void main() {
        fragColor = texture(tex, uv);
    }
    """
)
quad = np.array([
    -1,  1,  0, 0,
    -1,  0.7, 0, 1,
     1,  0.7, 1, 1,

    -1,  1,  0, 0,
     1,  0.7, 1, 1,
     1,  1,  1, 0,
], dtype='f4')

quad_vbo = ctx.buffer(quad)
quad_vao = ctx.vertex_array(
    text_prog,
    [(quad_vbo, '2f 2f', 'in_pos', 'in_uv')]
)
def create_text_texture(text, ctx, size=(800, 200)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.load_default()
    draw.text((10, 10), text, font=font, fill=(255,255,255,255))

    tex = ctx.texture(img.size, 4, img.tobytes())
    tex.build_mipmaps()
    return tex
# ===================== GEOMETRÍA =====================
def create_circle(n=64):
    vertices = []
    for i in range(n):
        a1 = 2*np.pi*i/n
        a2 = 2*np.pi*(i+1)/n

        vertices += [0, 0]
        vertices += [np.cos(a1), np.sin(a1)]
        vertices += [np.cos(a2), np.sin(a2)]

    return np.array(vertices, dtype='f4')

circle = create_circle(64)
vbo = ctx.buffer(circle)
vao = ctx.simple_vertex_array(prog, vbo, 'in_pos')

# ===================== ESCALA =====================
DIST_SCALE = 1e9  # 1 unidad = 1e9 metros

# ===================== FÍSICA =====================
G = 6.67430e-11
mT = 5.972e24
GM = G * mT

# ===================== LUNA =====================
mL = 7.348e22
a = 384400e3
e = 0.0549
mu = G * (mT + mL)
n = np.sqrt(mu / a**3)

def solve_kepler(M, e):
    E = M
    for _ in range(10):
        E -= (E - e*np.sin(E) - M) / (1 - e*np.cos(E))
    return E

def moon_pos(t):
    M = n * t
    E = solve_kepler(M, e)
    r = a * (1 - e*np.cos(E))

    th = 2 * np.arctan2(
        np.sqrt(1+e) * np.sin(E/2),
        np.sqrt(1-e) * np.cos(E/2)
    )

    return np.array([r*np.cos(th), r*np.sin(th)])  # SI

# ===================== TRAIL =====================
trail = []
MAX_TRAIL = 800

trail_vbo = ctx.buffer(reserve=MAX_TRAIL * 2 * 4)
trail_vao = ctx.simple_vertex_array(prog, trail_vbo, 'in_pos')

# ===================== PARTÍCULAS =====================
particles = []

dragging = False
drag_start = None
drag_current = None
VEL_FACTOR_SI = 20000  # m/s típico
def screen_to_world(x, y, width, height):
    nx = (x / width) * 2 - 1
    ny = 1 - (y / height) * 2

    world_render = np.array([nx, ny]) / zoom + camera_pos
    return world_render * DIST_SCALE  # ← SI

def mouse_click(window, button, action, mods):
    global dragging, drag_start, drag_current

    if button == glfw.MOUSE_BUTTON_LEFT:
        x, y = glfw.get_cursor_pos(window)
        w, h = glfw.get_window_size(window)

        world_pos = screen_to_world(x, y, w, h)

        if action == glfw.PRESS:
            dragging = True
            drag_start = world_pos.copy()
            drag_current = world_pos.copy()

        elif action == glfw.RELEASE:
            dragging = False

            x, y = glfw.get_cursor_pos(window)
            release_pos = screen_to_world(x, y, w, h)

            if drag_start is not None:
                drag_render = (release_pos - drag_start) / DIST_SCALE
                v0 = -drag_render * VEL_FACTOR_SI * zoom

                particles.append({
                    "pos": drag_start.copy(),
                    "vel": v0
                })

            drag_start = None
            drag_current = None
            print(v0)

glfw.set_mouse_button_callback(window, mouse_click)

def cursor_pos(window, x, y):
    global drag_current
    if dragging:
        w, h = glfw.get_window_size(window)
        drag_current = screen_to_world(x, y, w, h)

glfw.set_cursor_pos_callback(window, cursor_pos)

# ===================== LOOP =====================
t0 = time.time()
t_prev = t0
TIME_SCALE = 2000
def format_vec(v):
    return f"({v[0]/1000:.1f}, {v[1]/1000:.1f}) km"

while not glfw.window_should_close(window):
    glfw.poll_events()
    ctx.clear(0, 0, 0)

    # tiempo
    t_now = time.time()
    dt_real = t_now - t_prev
    dt = dt_real * TIME_SCALE
    t_prev = t_now

    process_input(window, dt)

    # luna (SI)
    t = (t_now - t0) * 5000
    mp = moon_pos(t)

    # ===================== TRAIL =====================
    trail.append(mp / DIST_SCALE)
    if len(trail) > MAX_TRAIL:
        trail.pop(0)

    if len(trail) > 1:
        data = np.array(trail, dtype='f4').flatten()
        trail_vbo.write(data.tobytes())

        prog['offset'].value = (0.0, 0.0)
        prog['scale'].value = 1.0
        prog['cam_pos'].value = tuple(camera_pos)
        prog['zoom'].value = zoom
        prog['color'].value = (1.0, 0.5, 0.2)

        trail_vao.render(mode=moderngl.LINE_STRIP, vertices=len(trail))

    # ===================== TIERRA =====================
    prog['offset'].value = (0.0, 0.0)
    prog['scale'].value = 6.371e6 / DIST_SCALE
    prog['cam_pos'].value = tuple(camera_pos)
    prog['zoom'].value = zoom
    prog['color'].value = (0.2, 0.5, 1.0)
    vao.render()

    # ===================== LUNA =====================
    prog['offset'].value = tuple(mp / DIST_SCALE)
    prog['scale'].value = 1.737e6 / DIST_SCALE
    prog['cam_pos'].value = tuple(camera_pos)
    prog['zoom'].value = zoom
    prog['color'].value = (0.8, 0.8, 0.8)
    vao.render()

    # ===================== PREVIEW DRAG =====================
    if dragging and drag_start is not None and drag_current is not None:
        line = np.array([
            *(drag_start / DIST_SCALE),
            *(drag_current / DIST_SCALE)
        ], dtype='f4')

        line_vbo = ctx.buffer(line.tobytes())
        line_vao = ctx.simple_vertex_array(prog, line_vbo, 'in_pos')

        prog['offset'].value = (0.0, 0.0)
        prog['scale'].value = 1.0
        prog['cam_pos'].value = tuple(camera_pos)
        prog['zoom'].value = zoom
        prog['color'].value = (0.2, 1.0, 0.2)

        line_vao.render(mode=moderngl.LINES)

    # ===================== FÍSICA =====================
    for p in particles:
        r = p["pos"]
        dist = np.linalg.norm(r)

        if dist > 1e3:
            acc = -GM * r / dist**3
        else:
            acc = np.array([0.0, 0.0])

        # symplectic Euler
        p["vel"] += acc * dt
        p["pos"] += p["vel"] * dt

    # ===================== RENDER PARTÍCULAS =====================
    for p in particles:
        prog['offset'].value = tuple(p["pos"] / DIST_SCALE)
        prog['scale'].value = 2e6 / DIST_SCALE
        prog['cam_pos'].value = tuple(camera_pos)
        prog['zoom'].value = zoom
        prog['color'].value = (1.0, 0.2, 0.2)

        vao.render()
    def format_vec(v):
        return f"({v[0]/1000:.0f}, {v[1]/1000:.0f}) km"

    sim_time = (t_now - t0) * 5000

    info = f"t = {sim_time:.0f} s\n"
    info += f"Luna: {format_vec(mp)}\n"

    for i, p in enumerate(particles[:3]):
        info += f"P{i}: {format_vec(p['pos'])}\n"
    
    text_tex = create_text_texture(info, ctx)
    text_tex.use()
    quad_vao.render()
    
    text_tex.release() 
    
    glfw.swap_buffers(window)

glfw.terminate()