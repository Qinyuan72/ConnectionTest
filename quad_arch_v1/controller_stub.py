from __future__ import annotations

from .controller_interfaces import BaseController, ControlCoordinator
from .models import ActuatorCommand, PilotIntent, ProcessedState


class StubController(BaseController):
    """Placeholder controller with explicit, safe output behavior."""

    supported_modes = {"manual", "stabilize", "altitude_hold"}

    def compute_command(self, state: ProcessedState, intent: PilotIntent) -> ActuatorCommand:
        mode = intent.mode if intent.mode in self.supported_modes else "manual"

        if not intent.armed:
            return ActuatorCommand(
                motor_throttles=(0.0, 0.0, 0.0, 0.0),
                collective_throttle_norm=0.0,
                enable_output=False,
                mode=mode,
                notes=("disarmed", "output held at neutral"),
            )

        if mode == "manual":
            throttle = self._clamp(intent.throttle_cmd_norm or 0.0, 0.0, 1.0)
            return ActuatorCommand(
                motor_throttles=(throttle, throttle, throttle, throttle),
                collective_throttle_norm=throttle,
                enable_output=True,
                mode=mode,
                notes=("manual placeholder", "TODO: replace with mixer and rate control"),
            )

        if mode == "stabilize":
            return ActuatorCommand(
                motor_throttles=(0.0, 0.0, 0.0, 0.0),
                collective_throttle_norm=0.0,
                enable_output=False,
                mode=mode,
                notes=(
                    "stabilize placeholder",
                    f"TODO: use roll={intent.roll_cmd_deg:.1f} pitch={intent.pitch_cmd_deg:.1f}",
                ),
            )

        return ActuatorCommand(
            motor_throttles=(0.0, 0.0, 0.0, 0.0),
            collective_throttle_norm=0.0,
            enable_output=False,
            mode=mode,
            notes=(
                "altitude-hold placeholder",
                f"TODO: use altitude={intent.altitude_cmd_m!r} current={state.mean_alt_m:.1f}",
            ),
        )

    def _clamp(self, value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))


class SimpleControlCoordinator(ControlCoordinator):
    """Small coordinator wrapper that leaves room for future orchestration."""

    def __init__(self, controller: BaseController) -> None:
        self._controller = controller

    def step(self, state: ProcessedState, intent: PilotIntent) -> ActuatorCommand:
        return self._controller.compute_command(state, intent)
