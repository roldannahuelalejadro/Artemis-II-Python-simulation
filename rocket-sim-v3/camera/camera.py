"""Camera movement and follow behavior for the single rocket."""

from __future__ import annotations

from dataclasses import dataclass

from coordinates.frame import Vector


@dataclass(slots=True)
class Camera:
    center_xy: Vector = (0.0, 0.0)
    zoom: float = 1.0
    min_zoom: float = 0.05
    max_zoom: float = 1000.0
    follow_enabled: bool = False
    follow_smooth: float = 0.18

    def follow(self, target_xy: Vector) -> None:
        self.follow_enabled = True
        self.center_xy = target_xy

    def stop_follow(self) -> None:
        self.follow_enabled = False

    def update_follow(self, target_xy: Vector) -> None:
        if not self.follow_enabled:
            return
        self.center_xy = (
            self.center_xy[0] + (target_xy[0] - self.center_xy[0]) * self.follow_smooth,
            self.center_xy[1] + (target_xy[1] - self.center_xy[1]) * self.follow_smooth,
        )

    def pan(self, delta_xy: Vector) -> None:
        self.center_xy = (
            self.center_xy[0] + delta_xy[0],
            self.center_xy[1] + delta_xy[1],
        )

    def set_center(self, center_xy: Vector) -> None:
        self.center_xy = center_xy

    def set_zoom(self, value: float) -> None:
        self.zoom = max(self.min_zoom, min(self.max_zoom, value))

    def zoom_by(self, factor: float) -> None:
        self.set_zoom(self.zoom * factor)
