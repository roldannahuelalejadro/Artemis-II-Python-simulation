# ui/panel_spawn.py
import numpy as np
from imgui_bundle import imgui   # para ImVec2

from config.defaults import DEFAULTS
from core.entities.rocket import Rocket
from thrust_editor.presets import PRESETS
from thrust_editor.editor import ThrustEditor


class SpawnPanel:
    def __init__(self, simulation, trajectory_manager):
        self.simulation = simulation
        self.trajectory_manager = trajectory_manager
        
        # Valores del formulario
        self.moon_angle_deg = DEFAULTS["moon_initial_angle_deg"]
        self.rocket_name = "Cohete-1"
        self.x0 = DEFAULTS["rocket"]["x0"]
        self.y0 = DEFAULTS["rocket"]["y0"]
        self.vx0 = DEFAULTS["rocket"]["vx0"]
        self.vy0 = DEFAULTS["rocket"]["vy0"]
        
        self.selected_preset = "Ninguno"
        self.thrust_editor = ThrustEditor()

    def render_imgui(self):
        """Panel principal con ImGui"""
        imgui.begin("Nuevo Cohete + Controles", True)

        imgui.text("Configuración Inicial")
        imgui.separator()

        # Ángulo de la Luna
        changed, self.moon_angle_deg = imgui.slider_float(
            "Ángulo Luna (°)", self.moon_angle_deg, -180.0, 180.0
        )
        if changed:
            self.simulation.moon.initial_angle = np.deg2rad(self.moon_angle_deg)

        imgui.separator()

        # Datos del cohete
        imgui.text("Nuevo Cohete")
        _, self.rocket_name = imgui.input_text("Nombre", self.rocket_name, 32)
        
        _, self.x0 = imgui.input_float("Pos X (m)", self.x0, step=1000.0)
        _, self.y0 = imgui.input_float("Pos Y (m)", self.y0, step=1000.0)
        _, self.vx0 = imgui.input_float("Vel X (m/s)", self.vx0, step=10.0)
        _, self.vy0 = imgui.input_float("Vel Y (m/s)", self.vy0, step=10.0)

        imgui.separator()

        # Preset de thrust
        imgui.text("Preset de Thrust")
        preset_names = list(PRESETS.keys())
        current_index = preset_names.index(self.selected_preset) if self.selected_preset in preset_names else 0
        
        changed, new_index = imgui.combo("##Preset", current_index, preset_names)
        if changed:
            self.selected_preset = preset_names[new_index]

        imgui.separator()

        # Botones
        if imgui.button("Crear Cohete", imgui.ImVec2(200, 0)):
            self.create_rocket()

        imgui.same_line()
        if imgui.button("START SIMULATION", imgui.ImVec2(200, 0)):
            self.start_simulation()

        if imgui.button("Reset Todo", imgui.ImVec2(200, 0)):
            self.simulation.reset()
            self.trajectory_manager.clear()

        imgui.end()

    def create_rocket(self):
        pos = np.array([self.x0, self.y0], dtype='f8')
        vel = np.array([self.vx0, self.vy0], dtype='f8')
        
        rocket = Rocket(
            pos=pos,
            vel=vel,
            name=self.rocket_name,
            color=(1.0, 0.35, 0.35)
        )

        # === APLICAR PRESET (versión mejorada) ===
        if self.selected_preset != "Ninguno":
            preset = PRESETS[self.selected_preset]
            
            if preset.get("mode") == "artemis_phases":
                rocket.thrust_profile.set_mode("artemis_phases")
                print(f"🚀 Preset Artemis II Fases Automáticas aplicado a {rocket.name}")
                
            elif preset.get("mode") == "hover":
                rocket.thrust_profile.set_mode("hover")
                if "target_alt_km" in preset:
                    rocket.thrust_profile.set_hover_target(preset["target_alt_km"])
                print(f"✓ Aplicado modo HOVER a {rocket.name}")
                
            elif preset.get("mode") == "circular_orbit":
                rocket.thrust_profile.set_mode("circular_orbit")
                print(f"✓ Aplicado modo ÓRBITA CIRCULAR a {rocket.name}")
                
            else:
                # Preset clásico con expresiones
                x_expr = preset.get("x", "0.0")
                y_expr = preset.get("y", "0.0")
                rocket.thrust_profile.set_expressions(x_expr, y_expr)
                print(f"✓ Preset de expresiones aplicado a {rocket.name}")

        self.trajectory_manager.add_rocket(rocket)
        self.simulation.add_rocket(rocket)

        # Auto incrementar nombre
        try:
            num = int(self.rocket_name.split('-')[-1]) + 1
            self.rocket_name = f"Cohete-{num}"
        except:
            self.rocket_name = "Cohete-2"

        print(f"✓ Cohete creado: {rocket.name}")

    def start_simulation(self):
        if not self.simulation.rockets:
            print("⚠️ Agrega al menos un cohete antes de iniciar")
            return
        
        self.simulation.moon.initial_angle = np.deg2rad(self.moon_angle_deg)
        self.simulation.start()
        print("▶️ Simulación INICIADA")