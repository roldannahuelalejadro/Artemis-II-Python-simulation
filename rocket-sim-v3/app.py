"""Application composition root for rocket-sim-v3."""

from __future__ import annotations

import tkinter as tk

from core.simulation import SimulationState
from ui.mission_panel import MissionControlPanel


class RocketApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rocket Sim v3")
        self.root.geometry("1500x940")
        self.root.minsize(1280, 820)
        self.simulation = SimulationState()
        self.panel = MissionControlPanel(self.root, self.simulation)

    def run(self):
        self.root.mainloop()
