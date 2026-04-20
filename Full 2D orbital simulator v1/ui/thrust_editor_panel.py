# ui/thrust_editor_panel.py
from imgui_bundle import imgui
import numpy as np
from thrust_editor.presets import PRESETS

class ThrustEditorPanel:
    def __init__(self):
        self.current_rocket = None
        
        # Thrust expresión
        self.thrust_x_input = "0.0"
        self.thrust_y_input = "0.0"
        self.last_x = "0.0"
        self.last_y = "0.0"

        # Modos inteligentes
        self.selected_mode = "expression"
        self.hover_alt_km = 200.0
        self.kp = 0.015
        self.kd = 0.8

        # Posición y velocidad
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0

        # NUEVO: Límite de thrust
        self.max_thrust_acc = 30.0

    def edit_rocket(self, rocket):
        self.current_rocket = rocket
        
        self.pos_x = float(rocket.pos[0])
        self.pos_y = float(rocket.pos[1])
        self.vel_x = float(rocket.vel[0])
        self.vel_y = float(rocket.vel[1])
        self.max_thrust_acc = rocket.thrust_profile.max_thrust_acc

        if rocket.thrust_profile.mode == "hover":
            self.selected_mode = "hover"
            self.hover_alt_km = rocket.thrust_profile.hover_target_alt_km
            self.kp = rocket.thrust_profile.kp
            self.kd = rocket.thrust_profile.kd
            self.thrust_x_input = "// Modo Hover"
            self.thrust_y_input = "// Usa sliders abajo"
        elif rocket.thrust_profile.mode == "circular_orbit":
            self.selected_mode = "circular_orbit"
            self.thrust_x_input = "// Órbita Circular"
            self.thrust_y_input = ""
        else:
            self.selected_mode = "expression"
            self.thrust_x_input = rocket.thrust_profile.thrust_x_expr
            self.thrust_y_input = rocket.thrust_profile.thrust_y_expr

        self.last_x = self.thrust_x_input
        self.last_y = self.thrust_y_input

    def render_imgui(self):
        if not self.current_rocket:
            imgui.begin("Editor Thrust", True)
            imgui.text("Selecciona un cohete y presiona 'Editar Thrust'")
            imgui.end()
            return

        imgui.begin(f"Editor Thrust - {self.current_rocket.name}", True)

        # Posición y Velocidad (ya lo tenías)
        imgui.text_colored(imgui.ImVec4(1.0, 0.8, 0.0, 1.0), "📍 Posición y Velocidad (Teleport)")
        imgui.separator()
        _, self.pos_x = imgui.input_float("Pos X (m)", self.pos_x, step=10000.0, format="%.0f")
        _, self.pos_y = imgui.input_float("Pos Y (m)", self.pos_y, step=10000.0, format="%.0f")
        _, self.vel_x = imgui.input_float("Vel X (m/s)", self.vel_x, step=10.0)
        _, self.vel_y = imgui.input_float("Vel Y (m/s)", self.vel_y, step=10.0)

        if imgui.button("🚀 Teleport Cohete", imgui.ImVec2(-1, 0)):
            self.current_rocket.pos = np.array([self.pos_x, self.pos_y], dtype='f8')
            self.current_rocket.vel = np.array([self.vel_x, self.vel_y], dtype='f8')
            self.current_rocket.trail = [self.current_rocket.pos.copy() / 1e9]
            print(f"📍 Teleport realizado en {self.current_rocket.name}")

        imgui.separator()

        # Modo de control
        imgui.text("Modo de Control:")
        modes = ["expression", "hover", "circular_orbit", "artemis_phases"]
        mode_names = [
            "Expresiones (Desmos)",
            "Hover Estable",
            "Mantener Órbita Circular",
            "Artemis II - Fases Automáticas"
        ]
        current_idx = modes.index(self.selected_mode)
        changed, new_idx = imgui.combo("##mode", current_idx, mode_names)
        if changed:
            self.selected_mode = modes[new_idx]
            self.current_rocket.thrust_profile.set_mode(self.selected_mode)

        imgui.separator()

        # === NUEVO: Límite de Thrust Máximo ===
        imgui.text_colored(imgui.ImVec4(1.0, 0.4, 0.4, 1.0), "⚡ Límite de Thrust Máximo")
        _, self.max_thrust_acc = imgui.slider_float(
            "Max Thrust (m/s²)", self.max_thrust_acc, 1.0, 100.0, "%.1f"
        )
        self.current_rocket.thrust_profile.max_thrust_acc = self.max_thrust_acc
        imgui.text(f"Valor actual: {self.max_thrust_acc:.1f} m/s² ≈ {self.max_thrust_acc/9.81:.1f} g")

        imgui.separator()

        # Resto del thrust (expresiones / hover / orbit)
        if self.selected_mode == "expression":
            imgui.text("Expresiones de Thrust (estilo Desmos)")
            changed_x, self.thrust_x_input = imgui.input_text_multiline("##thrust_x", self.thrust_x_input, imgui.ImVec2(400, 90))
            changed_y, self.thrust_y_input = imgui.input_text_multiline("##thrust_y", self.thrust_y_input, imgui.ImVec2(400, 90))

            if changed_x or changed_y:
                if self.thrust_x_input != self.last_x or self.thrust_y_input != self.last_y:
                    self.current_rocket.thrust_profile.set_expressions(self.thrust_x_input, self.thrust_y_input)
                    self.last_x = self.thrust_x_input
                    self.last_y = self.thrust_y_input

        elif self.selected_mode == "hover":
            imgui.text("Modo Hover Estable")
            _, self.hover_alt_km = imgui.slider_float("Altura objetivo (km)", self.hover_alt_km, 50.0, 800.0, "%.1f")
            _, self.kp = imgui.slider_float("Kp (posición)", self.kp, 0.001, 0.02, "%.4f")
            _, self.kd = imgui.slider_float("Kd (velocidad)", self.kd, 0.5, 2.5, "%.2f")
            if self.current_rocket:
                self.current_rocket.thrust_profile.set_hover_target(self.hover_alt_km)
                self.current_rocket.thrust_profile.kp = self.kp
                self.current_rocket.thrust_profile.kd = self.kd

        elif self.selected_mode == "circular_orbit":
            imgui.text("Modo Órbita Circular")
            _, self.current_rocket.thrust_profile.orbit_strength = imgui.slider_float(
                "Fuerza", self.current_rocket.thrust_profile.orbit_strength, 0.1, 2.0, "%.2f"
            )

        imgui.separator()

        button_width = imgui.get_content_region_avail().x * 0.49
        if imgui.button("✅ Aplicar Thrust", imgui.ImVec2(button_width, 0)):
            if self.selected_mode == "expression":
                self.current_rocket.thrust_profile.set_expressions(self.thrust_x_input, self.thrust_y_input)

        imgui.same_line()
        if imgui.button("❌ Cerrar", imgui.ImVec2(button_width, 0)):
            self.current_rocket = None

        imgui.end()