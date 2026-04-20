# input/handler.py
import glfw
from ui.panel_spawn import SpawnPanel
from trajectory.manager import TrajectoryManager
from core.simulation import SimulationState

class InputHandler:
    """Maneja TODOS los inputs. NO interactúa directamente con la física."""
    
    def __init__(self, window, simulation: SimulationState, 
                 trajectory_manager: TrajectoryManager, spawn_panel: SpawnPanel):
        
        self.window = window
        self.simulation = simulation
        self.trajectory_manager = trajectory_manager
        self.spawn_panel = spawn_panel

    def setup_callbacks(self):
        glfw.set_key_callback(self.window, self._key_callback)

    def _key_callback(self, window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return

        # Shortcuts globales
        if key == glfw.KEY_SPACE:
            if self.simulation.is_running:
                self.simulation.pause()
            else:
                self.simulation.start()

        elif key == glfw.KEY_R:
            self.simulation.reset()
            self.trajectory_manager.clear()

        elif key == glfw.KEY_C:
            # Centrar cámara (necesitarás pasarle camera más adelante)
            pass

        elif key == glfw.KEY_N:
            # Crear nuevo cohete con valores actuales
            self.spawn_panel.create_rocket()

        elif key == glfw.KEY_DELETE:
            selected = self.trajectory_manager.get_selected()
            if selected:
                idx = self.trajectory_manager.rockets.index(selected)
                self.trajectory_manager.remove_rocket(idx)