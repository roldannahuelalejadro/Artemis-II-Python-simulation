# app.py
import glfw
import moderngl
import time
import numpy as np

from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from config.constants import WINDOW_WIDTH, WINDOW_HEIGHT
from core.simulation import SimulationState
from trajectory.manager import TrajectoryManager
from ui.panel_spawn import SpawnPanel
from ui.hud import HUD
from camera.camera import Camera
from rendering.renderer import Renderer
from input.handler import InputHandler
from ui.thrust_editor_panel import ThrustEditorPanel
from ui.panel_rockets import RocketsPanel
from trajectory.predictor import TrajectoryPredictor

class RocketApp:
    def __init__(self):
        if not glfw.init():
            raise Exception("No se pudo inicializar GLFW")

        self.window = glfw.create_window(
            WINDOW_WIDTH, WINDOW_HEIGHT,
            "Rocket Trajectory Studio v2",
            None, None
        )
        glfw.make_context_current(self.window)

        self.ctx = moderngl.create_context()

        # Core
        self.simulation = SimulationState()
        self.trajectory_manager = TrajectoryManager()

        self.spawn_panel = SpawnPanel(self.simulation, self.trajectory_manager)
        self.hud = HUD()
        self.camera = Camera()
        self.renderer = Renderer(self.ctx)

        # Input
        self.input_handler = InputHandler(
            self.window, self.simulation, 
            self.trajectory_manager, self.spawn_panel
        )
        self.input_handler.setup_callbacks()

        # UI Panels
        self.thrust_editor_panel = ThrustEditorPanel()
        self.rockets_panel = RocketsPanel(
            self.trajectory_manager,
            self.thrust_editor_panel,
            self.simulation,
            self.camera                      # ← Pasamos la cámara aquí
        )

        # Predictor fantasma
        self.trajectory_predictor = TrajectoryPredictor(steps=650, dt_predict=2.8)

        # ImGui
        imgui.create_context()
        self.imgui_renderer = GlfwRenderer(self.window)

        self.t_prev = time.time()

    def run(self):
        while not glfw.window_should_close(self.window):
            glfw.poll_events()

            t_now = time.time()
            dt_real = t_now - self.t_prev
            self.t_prev = t_now

            # Actualizar simulación
            self.simulation.update(dt_real)

            # Actualizar seguimiento de cámara
            self.camera.update_follow(dt_real)

            # Movimiento manual de cámara (solo si no seguimos)
            self.camera.process_keyboard(self.window, dt_real)

            imgui.new_frame()

            self.spawn_panel.render_imgui()
            self.rockets_panel.render_imgui()
            self.thrust_editor_panel.render_imgui()

            # Renderizado
            self.ctx.clear(0.0, 0.0, 0.05)

            cam_pos = tuple(self.camera.pos)
            zoom = self.camera.zoom

            self.renderer.render_body(self.simulation.earth.pos, self.simulation.earth.radius, 
                                    (0.2, 0.5, 1.0, 1.0), cam_pos, zoom)
            self.renderer.render_body(self.simulation.moon.pos, self.simulation.moon.radius, 
                                    (0.85, 0.85, 0.85, 1.0), cam_pos, zoom)

            for rocket in self.simulation.rockets:
                if not rocket.active:
                    continue

                self.renderer.render_rocket(rocket, cam_pos, zoom)

                # === Trayectoria fantasma del cohete seleccionado ===
                selected = self.rockets_panel.trajectory_manager.get_selected()  # o pasarlo como atributo
                
                if selected is rocket:   # solo mostramos predicción del seleccionado
                    ghost_points = self.trajectory_predictor.compute_ghost_trajectory(
                        rocket, self.simulation.moon.pos, self.simulation.sim_time
                    )
                    if ghost_points:
                        self.renderer.render_predictive_trajectory(ghost_points, cam_pos, zoom)

            info = self.hud.get_info_text(self.simulation, self.trajectory_manager)
            self.renderer.render_hud(info)

            imgui.render()
            self.imgui_renderer.render(imgui.get_draw_data())

            glfw.swap_buffers(self.window)

        self.imgui_renderer.shutdown()
        glfw.terminate()