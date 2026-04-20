"""Input bindings for camera and simulation controls."""

from __future__ import annotations


class InputHandler:
    def __init__(self, simulation):
        self.simulation = simulation

    def resume_requested(self) -> bool:
        return self.simulation.resume()
