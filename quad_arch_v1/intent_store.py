from __future__ import annotations

from .models import PilotIntent


class IntentStore:
    """Store the latest pilot intent coming from the UI or other clients."""

    def __init__(self) -> None:
        self._intent = PilotIntent()

    def set_intent(self, intent: PilotIntent) -> None:
        self._intent = intent

    def get_intent(self) -> PilotIntent:
        return self._intent
