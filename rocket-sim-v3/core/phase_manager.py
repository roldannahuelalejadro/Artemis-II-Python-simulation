"""Coordinates sequential thrust phases and pauses between them."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.phase import MissionPhase


@dataclass(slots=True)
class PhaseManager:
    pending: list[MissionPhase] = field(default_factory=list)
    completed: list[MissionPhase] = field(default_factory=list)
    active: MissionPhase | None = None
    elapsed_in_phase_s: float = 0.0
    paused_waiting_next_phase: bool = True

    def queue_phase(self, phase: MissionPhase) -> None:
        self.pending.append(phase)
        if self.active is None and self.paused_waiting_next_phase:
            self.start_next_phase()

    def start_next_phase(self) -> MissionPhase | None:
        if not self.pending:
            self.active = None
            self.elapsed_in_phase_s = 0.0
            self.paused_waiting_next_phase = True
            return None
        self.active = self.pending.pop(0)
        self.elapsed_in_phase_s = 0.0
        self.paused_waiting_next_phase = False
        return self.active

    def advance(self, dt_s: float) -> MissionPhase | None:
        if self.active is None:
            return None
        self.elapsed_in_phase_s += dt_s
        if self.elapsed_in_phase_s + 1e-9 < self.active.duration_s:
            return None
        finished = self.active
        self.completed.append(finished)
        self.active = None
        self.elapsed_in_phase_s = 0.0
        self.paused_waiting_next_phase = True
        return finished
