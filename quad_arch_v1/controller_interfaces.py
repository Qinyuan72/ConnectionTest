from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from .models import ActuatorCommand, PilotIntent, ProcessedState


class BaseController(ABC):
    """Base interface for high-level control policy objects."""

    @abstractmethod
    def compute_command(self, state: ProcessedState, intent: PilotIntent) -> ActuatorCommand:
        """Compute the next actuator command from state and user intent."""


class ModeController(Protocol):
    """Optional mode-specific controller interface for future expansion."""

    def supports_mode(self, mode: str) -> bool:
        ...

    def compute_command(self, state: ProcessedState, intent: PilotIntent) -> ActuatorCommand:
        ...


class Mixer(Protocol):
    """Optional actuator mixer interface."""

    def mix(self, command: ActuatorCommand) -> ActuatorCommand:
        ...


class ControlCoordinator(ABC):
    """Own controller sequencing without leaking control details to the UI."""

    @abstractmethod
    def step(self, state: ProcessedState, intent: PilotIntent) -> ActuatorCommand:
        """Advance the control path by one step."""
