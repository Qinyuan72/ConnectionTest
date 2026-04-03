from __future__ import annotations

from .models import ProcessedState


class StateStore:
    """Single source of truth for the latest processed telemetry state."""

    def __init__(self) -> None:
        self._state = ProcessedState()

    def update(self, state: ProcessedState) -> None:
        self._state = state

    def get_snapshot(self) -> ProcessedState:
        return self._state
