from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ActuatorCommand


class BaseActuatorSink(ABC):
    """Boundary interface for actuator outputs."""

    @abstractmethod
    def send(self, command: ActuatorCommand) -> None:
        """Send a controller command to an output backend."""


class NullActuatorSink(BaseActuatorSink):
    """Safe no-op sink for experiments that should not write real actuators."""

    def __init__(self) -> None:
        self.last_command = ActuatorCommand(notes=("no command sent yet",))

    def send(self, command: ActuatorCommand) -> None:
        self.last_command = command


class KrpcActuatorSink(BaseActuatorSink):
    """Skeleton kRPC actuator sink reserved for future explicit implementation."""

    def __init__(self, connection: object | None = None) -> None:
        self._connection = connection

    def send(self, command: ActuatorCommand) -> None:
        raise NotImplementedError("kRPC actuator writing is intentionally not implemented yet.")
