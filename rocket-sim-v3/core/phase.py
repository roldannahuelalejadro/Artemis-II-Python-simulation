"""Mission phase definition: duration, frame, and thrust functions."""

from __future__ import annotations

from dataclasses import dataclass

from coordinates.frame import FrameType


@dataclass(slots=True)
class MissionPhase:
    label: str
    duration_s: float
    frame: FrameType
    primary_expr: str = "0.0"
    secondary_expr: str = "0.0"
    notes: str = ""

    def __post_init__(self) -> None:
        if self.duration_s <= 0.0:
            raise ValueError("Phase duration must be positive")

    @property
    def is_coast(self) -> bool:
        return self.frame == FrameType.NONE

    def component_labels(self) -> tuple[str, str]:
        if self.frame == FrameType.XY:
            return ("fx", "fy")
        if self.frame == FrameType.PROGRADE:
            return ("f_prograde", "f_normal")
        if self.frame == FrameType.POLAR:
            return ("f_r", "f_theta")
        return ("0", "0")
