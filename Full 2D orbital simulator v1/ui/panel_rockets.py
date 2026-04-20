# ui/panel_rockets.py
from imgui_bundle import imgui
from trajectory.manager import TrajectoryManager
from ui.thrust_editor_panel import ThrustEditorPanel
from core.simulation import SimulationState


class RocketsPanel:
    def __init__(self, 
                 trajectory_manager: TrajectoryManager, 
                 thrust_editor_panel: ThrustEditorPanel,
                 simulation: SimulationState,
                 camera):                     # ← Nuevo: pasamos la cámara
        self.trajectory_manager = trajectory_manager
        self.thrust_editor_panel = thrust_editor_panel
        self.simulation = simulation
        self.camera = camera

    def render_imgui(self):
        imgui.begin("Cohetes Activos", True)

        if not self.trajectory_manager.rockets:
            imgui.text("No hay cohetes aún.\nCrea uno desde el panel 'Nuevo Cohete + Controles'")
            imgui.end()
            return

        imgui.text(f"Total: {len(self.trajectory_manager.rockets)} cohetes")
        imgui.separator()

        for i, rocket in enumerate(self.trajectory_manager.rockets):
            is_selected = (i == self.trajectory_manager.selected_index)
            status = "🟢" if rocket.active else "🔴"
            label = f"{status} [{i}] {rocket.name}"

            if imgui.selectable(label, is_selected)[0]:
                self.trajectory_manager.select(i)

            imgui.same_line()

            if imgui.button(f"Editar Thrust##{i}"):
                self.thrust_editor_panel.edit_rocket(rocket)

            imgui.same_line()
            col = imgui.ImVec4(rocket.color[0], rocket.color[1], rocket.color[2], 1.0)
            imgui.color_button(f"##color{i}", col, size=imgui.ImVec2(20, 20))

        imgui.separator()

        # === CONTROLES DE SEGUIMIENTO ===
        selected = self.trajectory_manager.get_selected()

        if selected:
            imgui.text(f"Seleccionado: {selected.name}")

            button_width = imgui.get_content_region_avail().x * 0.49

            if imgui.button("📍 Seguir Cohete", imgui.ImVec2(button_width, 0)):
                self.camera.set_follow_target(selected)

            imgui.same_line()
            if imgui.button("🛑 Detener", imgui.ImVec2(button_width, 0)):
                self.camera.stop_follow()

        imgui.separator()

        # Botón eliminar
        if imgui.button("🗑 Eliminar seleccionado", imgui.ImVec2(-1, 32)):
            if selected:
                idx = self.trajectory_manager.rockets.index(selected)
                self.trajectory_manager.remove_rocket(idx)
                if selected in self.simulation.rockets:
                    self.simulation.rockets.remove(selected)

        imgui.end()