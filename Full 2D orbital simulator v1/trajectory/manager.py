# trajectory/manager.py
from core.entities.rocket import Rocket
from typing import Optional

class TrajectoryManager:
    """
    Gestiona la lista de cohetes (agregar, seleccionar, eliminar, renombrar).
    """
    def __init__(self):
        self.rockets: list[Rocket] = []
        self.selected_index: int = -1  # -1 = ninguno seleccionado

    def add_rocket(self, rocket: Rocket):
        self.rockets.append(rocket)
        if len(self.rockets) == 1:
            self.selected_index = 0  # seleccionar automáticamente el primero
        print(f"✓ Cohete añadido: {rocket.name}")

    def remove_rocket(self, index: int):
        if 0 <= index < len(self.rockets):
            removed = self.rockets.pop(index)
            print(f"🗑 Cohete eliminado: {removed.name}")
            if self.selected_index >= len(self.rockets):
                self.selected_index = len(self.rockets) - 1

    def select(self, index: int):
        if 0 <= index < len(self.rockets):
            self.selected_index = index

    def get_selected(self) -> Optional[Rocket]:
        if 0 <= self.selected_index < len(self.rockets):
            return self.rockets[self.selected_index]
        return None

    def clear(self):
        self.rockets.clear()
        self.selected_index = -1