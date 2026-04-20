# rendering/renderer.py
import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config.constants import R_EARTH, R_MOON, DIST_SCALE

class Renderer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.prog = self._create_main_program()
        self.text_prog = self._create_text_program()
        
        self.vao_circle = self._create_circle_vao()
        self.line_vbo = ctx.buffer(reserve=8192 * 4)
        self.line_vao = ctx.simple_vertex_array(self.prog, self.line_vbo, 'in_pos')
        
        self.quad_vao = self._create_text_quad()
        self.text_tex = None
        self.last_info = ""

    def _create_main_program(self):
        return self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos;
            uniform vec2 cam_pos; uniform float zoom;
            uniform vec2 offset; uniform float scale;
            void main() {
                vec2 world = in_pos * scale + offset;
                vec2 view = (world - cam_pos) * zoom;
                gl_Position = vec4(view, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330
            uniform vec4 color;
            out vec4 fragColor;
            void main() { fragColor = color; }
            """
        )

    def _create_text_program(self):
        return self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos; in vec2 in_uv; out vec2 uv;
            void main() { uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
            """,
            fragment_shader="""
            #version 330
            in vec2 uv; uniform sampler2D tex; out vec4 fragColor;
            void main() { fragColor = texture(tex, uv); }
            """
        )

    def _create_circle_vao(self):
        verts = []
        for i in range(64):
            a1 = 2*np.pi*i/64
            a2 = 2*np.pi*(i+1)/64
            verts += [0,0, np.cos(a1),np.sin(a1), np.cos(a2),np.sin(a2)]
        vbo = self.ctx.buffer(np.array(verts, dtype='f4'))
        return self.ctx.simple_vertex_array(self.prog, vbo, 'in_pos')

    def _create_text_quad(self):
        quad = np.array([
            -1, 1, 0, 0,
            -1, 0.6, 0, 1,
             1, 0.6, 1, 1,
            -1, 1, 0, 0,
             1, 0.6, 1, 1,
             1, 1, 1, 0
        ], dtype='f4')
        vbo = self.ctx.buffer(quad)
        return self.ctx.vertex_array(self.text_prog, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

    def update_text(self, info: str):
        if self.text_tex:
            self.text_tex.release()

        img = Image.new("RGBA", (900, 300), (0, 0, 0, 180))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((15, 15), info, font=font, fill=(255, 255, 255, 255))

        self.text_tex = self.ctx.texture(img.size, 4, img.tobytes())
        self.text_tex.build_mipmaps()
        self.last_info = info

    def render_body(self, pos, radius, color, cam_pos, zoom):
        self.prog['offset'] = (pos[0]/DIST_SCALE, pos[1]/DIST_SCALE)
        self.prog['scale'] = radius / DIST_SCALE
        self.prog['cam_pos'] = cam_pos
        self.prog['zoom'] = zoom
        self.prog['color'] = color
        self.vao_circle.render()

    def render_rocket(self, rocket, cam_pos, zoom):
        # === TRAIL ===
        if len(rocket.trail) > 1:
            data = np.array(rocket.trail, dtype='f4').flatten()
            self.line_vbo.write(data.tobytes())
            self.prog['offset'] = (0, 0)
            self.prog['scale'] = 1.0
            self.prog['cam_pos'] = cam_pos
            self.prog['zoom'] = zoom
            self.prog['color'] = (*rocket.color, 0.65)
            self.line_vao.render(moderngl.LINE_STRIP, vertices=len(rocket.trail))

        # === COHETE COMO TRIÁNGULO ORIENTADO ===
        if np.linalg.norm(rocket.vel) < 1.0:
            direction = np.array([0.0, 1.0])  # si está quieto, apunta hacia arriba
        else:
            direction = rocket.vel / np.linalg.norm(rocket.vel)

        # Perpendicular para formar el triángulo
        perp = np.array([-direction[1], direction[0]])

        # Tamaño visual del cohete (en metros del mundo)
        length = 1.8e6      # largo del cohete
        width = 0.9e6       # ancho

        # Vértices del triángulo (punta hacia adelante)
        tip = rocket.pos + direction * length * 0.6
        base1 = rocket.pos - direction * length * 0.4 + perp * width * 0.5
        base2 = rocket.pos - direction * length * 0.4 - perp * width * 0.5

        # Convertimos a unidades de DIST_SCALE y preparamos para dibujar
        verts = np.array([
            tip[0]/DIST_SCALE,   tip[1]/DIST_SCALE,
            base1[0]/DIST_SCALE, base1[1]/DIST_SCALE,
            base2[0]/DIST_SCALE, base2[1]/DIST_SCALE,
        ], dtype='f4')

        # Creamos un buffer temporal para este triángulo
        vbo = self.ctx.buffer(verts.tobytes())
        vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_pos')

        # Configuramos uniforms
        self.prog['offset'] = (0.0, 0.0)
        self.prog['scale'] = 1.0
        self.prog['cam_pos'] = cam_pos
        self.prog['zoom'] = zoom
        self.prog['color'] = (*rocket.color, 1.0)

        vao.render(moderngl.TRIANGLES)

        # Liberamos recursos (importante para no acumular buffers)
        vao.release()
        vbo.release()

    def render_hud(self, info: str):
        if info != self.last_info or not self.text_tex:
            self.update_text(info)
        if self.text_tex:
            self.text_tex.use(0)
            self.quad_vao.render()

            
    def render_predictive_trajectory(self, points: list[np.ndarray], cam_pos, zoom):
        """Dibuja la trayectoria fantasma en verde translúcido"""
        if len(points) < 2:
            return

        # Convertir a array plano para el buffer
        data = np.array(points, dtype='f4').flatten()

        self.line_vbo.write(data.tobytes())

        self.prog['offset'] = (0.0, 0.0)
        self.prog['scale'] = 1.0
        self.prog['cam_pos'] = cam_pos
        self.prog['zoom'] = zoom
        self.prog['color'] = (0.3, 1.0, 0.4, 0.65)   # verde fantasma

        self.line_vao.render(moderngl.LINE_STRIP, vertices=len(points))