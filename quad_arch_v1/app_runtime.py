from __future__ import annotations

from .actuator_set import BaseActuatorSink, NullActuatorSink
from .controller_interfaces import BaseController, ControlCoordinator
from .controller_stub import SimpleControlCoordinator, StubController
from .intent_store import IntentStore
from .models import ActuatorCommand, PilotIntent, ProcessedState
from .state_store import StateStore
from .telemetry_get import KrpcTelemetrySource
from .telemetry_processor import TelemetryProcessor


class AppRuntime:
    """Coordinate the read path and write path without exposing boundary details to the UI."""

    def __init__(
        self,
        telemetry_source: KrpcTelemetrySource | None = None,
        telemetry_processor: TelemetryProcessor | None = None,
        state_store: StateStore | None = None,
        intent_store: IntentStore | None = None,
        controller: BaseController | None = None,
        control_coordinator: ControlCoordinator | None = None,
        actuator_sink: BaseActuatorSink | None = None,
    ) -> None:
        self.telemetry_source = telemetry_source or KrpcTelemetrySource()
        self.telemetry_processor = telemetry_processor or TelemetryProcessor()
        self.state_store = state_store or StateStore()
        self.intent_store = intent_store or IntentStore()
        self.controller = controller or StubController()
        self.control_coordinator = control_coordinator or SimpleControlCoordinator(self.controller)
        self.actuator_sink = actuator_sink or NullActuatorSink()
        self.last_command = ActuatorCommand(notes=("runtime not stepped yet",))

    def connect(self) -> None:
        self.telemetry_source.connect()

    def disconnect(self) -> None:
        self.telemetry_source.disconnect()

    def is_connected(self) -> bool:
        return self.telemetry_source.is_connected()

    def telemetry_tick(self) -> ProcessedState:
        raw = self.telemetry_source.read_raw()
        state = self.telemetry_processor.process(raw)
        self.state_store.update(state)
        return state

    def control_tick(self) -> ActuatorCommand:
        state = self.state_store.get_snapshot()
        intent = self.intent_store.get_intent()
        command = self.control_coordinator.step(state, intent)
        self.actuator_sink.send(command)
        self.last_command = command
        return command

    def get_state_snapshot(self) -> ProcessedState:
        return self.state_store.get_snapshot()

    def get_intent(self) -> PilotIntent:
        return self.intent_store.get_intent()

    def set_intent(self, intent: PilotIntent) -> None:
        self.intent_store.set_intent(intent)
