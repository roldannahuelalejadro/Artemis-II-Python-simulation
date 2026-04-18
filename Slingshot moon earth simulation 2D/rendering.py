# rendering.py
import moderngl
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config import DIST_SCALE, MAX_PARTICLE_TRAIL, MAX_LUNA_TRAIL

class Renderer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.prog = self._create_main_program()
        self.text_prog = self._create_text_program()
        
        self.vao_circle = self._create_circle_vao()
        
        # Buffers dinámicos según MAX_*
        self.line_vbo = ctx.buffer(reserve=16)
        self.line_vao = ctx.simple_vertex_array(self.prog, self.line_vbo, 'in_pos')
        
        self.luna_trail_vbo = ctx.buffer(reserve=MAX_LUNA_TRAIL * 2 * 4)
        self.particle_trail_vbo = ctx.buffer(reserve=MAX_PARTICLE_TRAIL * 2 * 4)

        self.quad_vao = self._create_text_quad()

        self.text_tex = None
        self.last_info = ""

    def _create_main_program(self):
        return self.ctx.program(
            vertex_shader="""
            #version 330
            in vec2 in_pos;
            uniform vec2 offset; uniform float scale;
            uniform vec2 cam_pos; uniform float zoom;
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
        def create_circle(n=64):
            verts = []
            for i in range(n):
                a1 = 2*np.pi*i/n
                a2 = 2*np.pi*(i+1)/n
                verts += [0, 0, np.cos(a1), np.sin(a1), np.cos(a2), np.sin(a2)]
            return np.array(verts, dtype='f4')
        
        vbo = self.ctx.buffer(create_circle())
        return self.ctx.simple_vertex_array(self.prog, vbo, 'in_pos')

    def _create_text_quad(self):
        quad = np.array([
            -1.0, 1.0, 0, 0,
            -1.0, 0.6, 0, 1,
             1.0, 0.6, 1, 1,
            -1.0, 1.0, 0, 0,
             1.0, 0.6, 1, 1,
             1.0, 1.0, 1, 0
        ], dtype='f4')
        vbo = self.ctx.buffer(quad)
        return self.ctx.vertex_array(self.text_prog, [(vbo, '2f 2f', 'in_pos', 'in_uv')])

    def update_text(self, info):
        if self.text_tex:
            self.text_tex.release()

        img = Image.new("RGBA", (860, 280), (0, 0, 0, 170))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 21)
        except:
            font = ImageFont.load_default()

        draw.text((20, 15), info, font=font, fill=(255, 255, 255, 255))

        self.text_tex = self.ctx.texture(img.size, 4, img.tobytes())
        self.text_tex.build_mipmaps()
        self.last_info = info

    def render_luna_trail(self, trail, cam_pos, zoom):
        if len(trail) < 2:
            return
        data = np.array(trail, dtype='f4').flatten()
        self.luna_trail_vbo.write(data.tobytes())

        self.prog['offset'] = (0.0, 0.0)
        self.prog['scale'] = 1.0
        self.prog['cam_pos'] = tuple(cam_pos)
        self.prog['zoom'] = zoom
        self.prog['color'] = (1.0, 0.65, 0.25)

        vao = self.ctx.simple_vertex_array(self.prog, self.luna_trail_vbo, 'in_pos')
        vao.render(moderngl.LINE_STRIP, vertices=len(trail))

    def render_particle_trail(self, trail, cam_pos, zoom):
        if len(trail) < 2:
            return
        
        # ← SOLUCIÓN: Escribimos solo hasta el tamaño actual del trail
        data = np.array(trail, dtype='f4').flatten()
        self.particle_trail_vbo.write(data.tobytes())   # Ahora es seguro porque el buffer es lo suficientemente grande

        self.prog['offset'] = (0.0, 0.0)
        self.prog['scale'] = 1.0
        self.prog['cam_pos'] = tuple(cam_pos)
        self.prog['zoom'] = zoom
        self.prog['color'] = (1.0, 0.45, 0.15)

        vao = self.ctx.simple_vertex_array(self.prog, self.particle_trail_vbo, 'in_pos')
        vao.render(moderngl.LINE_STRIP, vertices=len(trail))