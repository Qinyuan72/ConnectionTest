from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

import krpc

DEFAULT_CONTROLLER_TAGS: Dict[str, str] = {
    "FL": "ControllerFL",
    "FR": "ControllerFR",
    "RL": "ControllerRL",
    "RR": "ControllerRR",
}

DEFAULT_ROTOR_TAGS: Dict[str, str] = {
    "FL": "rotorFL",
    "FR": "rotorFR",
    "RL": "rotorRL",
    "RR": "rotorRR",
}

RPM_MIN = 0.0
RPM_MAX = 460.0


class BindingError(RuntimeError):
    """Raised when expected tagged parts or modules cannot be found."""


@dataclass(frozen=True)
class ControllerSnapshot:
    key: str
    tag: str
    part_title: str
    part_name: str
    sequence: str
    play_position: float
    play_speed_percent: float
    enabled: bool
    play_pause_raw: str
    play_direction_raw: str
    loop_mode_raw: str
    controller_priority: int
    fields: Mapping[str, str] = field(default_factory=dict)
    actions: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RotorSnapshot:
    key: str
    tag: str
    part_title: str
    part_name: str
    current_rpm: float
    target_rpm: Optional[float]
    torque_limit: float
    motor_engaged: bool
    locked: bool


@dataclass(frozen=True)
class RigSnapshot:
    connected: bool
    vessel_name: str
    controller_tags: Mapping[str, str]
    rotor_tags: Mapping[str, str]
    controllers: Mapping[str, ControllerSnapshot]
    rotors: Mapping[str, RotorSnapshot]


class KALControllerBinding:
    """Thin wrapper around one ModuleRoboticController bound by part tag."""

    def __init__(self, key: str, part: Any, module: Any):
        self.key = key
        self.part = part
        self.module = module

    @property
    def tag(self) -> str:
        return self.part.tag

    def get_fields(self) -> Dict[str, str]:
        return dict(self.module.fields)

    def get_actions(self) -> List[str]:
        return list(self.module.actions)

    def _field(self, name: str, default: str = "") -> str:
        return str(self.get_fields().get(name, default))

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return str(value).strip().lower() in {"true", "1", "yes", "on"}

    @staticmethod
    def _parse_float(value: str, default: float = 0.0) -> float:
        try:
            return float(str(value).strip().replace("%", ""))
        except Exception:
            return default

    @staticmethod
    def _parse_int(value: str, default: int = 0) -> int:
        try:
            return int(float(str(value).strip()))
        except Exception:
            return default

    def snapshot(self) -> ControllerSnapshot:
        fields = self.get_fields()
        return ControllerSnapshot(
            key=self.key,
            tag=self.part.tag,
            part_title=self.part.title,
            part_name=self.part.name,
            sequence=str(fields.get("Sequence", "")),
            play_position=self._parse_float(fields.get("Play Position", "0")),
            play_speed_percent=self._parse_float(fields.get("Play Speed", "0")),
            enabled=self._parse_bool(fields.get("Enabled", "False")),
            play_pause_raw=str(fields.get("Play/Pause", "")),
            play_direction_raw=str(fields.get("Play Direction", "")),
            loop_mode_raw=str(fields.get("Loop Mode", "")),
            controller_priority=self._parse_int(fields.get("Controller Priority", "0")),
            fields=fields,
            actions=tuple(self.get_actions()),
        )

    def set_play_position(self, value: float) -> None:
        self.module.set_field_float("Play Position", float(value))

    def set_play_speed_percent(self, value: float) -> None:
        self.module.set_field_float("Play Speed", float(value))

    def set_enabled(self, enabled: bool) -> None:
        self.module.set_field_bool("Enabled", bool(enabled))

    def set_controller_priority(self, value: int) -> None:
        self.module.set_field_int("Controller Priority", int(value))

    def trigger_action(self, action_name: str) -> None:
        self.module.set_action(action_name)

    def play(self) -> None:
        self.trigger_action("Play Sequence")

    def stop(self) -> None:
        self.trigger_action("Stop Sequence")

    def toggle_play(self) -> None:
        self.trigger_action("Toggle Play")

    def set_direction_forward(self) -> None:
        self.trigger_action("Set Play Direction to Forward")

    def set_direction_reverse(self) -> None:
        self.trigger_action("Set Play Direction to Reverse")

    def set_loop_once(self) -> None:
        self.trigger_action("Set Loop Mode to Once")

    def set_loop_repeat(self) -> None:
        self.trigger_action("Set Loop Mode to Repeat")

    def set_loop_pingpong(self) -> None:
        self.trigger_action("Set Loop Mode to PingPong")

    def set_loop_once_restart(self) -> None:
        self.trigger_action("Set Loop Mode to Once-Restart")

    def set_zero_speed(self) -> None:
        self.trigger_action("Set Play Speed to 0%")

    def set_full_speed(self) -> None:
        self.trigger_action("Set Play Speed to 100%")


class RotorBinding:
    """Thin wrapper around one robotic rotor bound by part tag."""

    def __init__(self, key: str, part: Any, rotor: Any):
        self.key = key
        self.part = part
        self.rotor = rotor

    @property
    def tag(self) -> str:
        return self.part.tag

    @staticmethod
    def _optional_float(getter: Any) -> Optional[float]:
        try:
            return float(getter())
        except Exception:
            return None

    def snapshot(self) -> RotorSnapshot:
        return RotorSnapshot(
            key=self.key,
            tag=self.part.tag,
            part_title=self.part.title,
            part_name=self.part.name,
            current_rpm=float(self.rotor.current_rpm),
            target_rpm=self._optional_float(lambda: self.rotor.target_rpm),
            torque_limit=float(self.rotor.torque_limit),
            motor_engaged=bool(self.rotor.motor_engaged),
            locked=bool(self.rotor.locked),
        )

    def set_torque_limit(self, value: float) -> None:
        self.rotor.torque_limit = float(value)

    def set_motor_engaged(self, engaged: bool) -> None:
        self.rotor.motor_engaged = bool(engaged)

    def set_locked(self, locked: bool) -> None:
        self.rotor.locked = bool(locked)

    def set_target_rpm(self, rpm: float) -> None:
        """Optional direct rotor command path. Do not mix with KAL path unless intentional."""
        self.rotor.target_rpm = float(rpm)


class KALRotorRig:
    """High-level test harness for 4 tagged KAL controllers + 4 tagged rotors."""

    def __init__(
        self,
        controller_tags: Mapping[str, str] | None = None,
        rotor_tags: Mapping[str, str] | None = None,
    ) -> None:
        self.controller_tags: Dict[str, str] = dict(controller_tags or DEFAULT_CONTROLLER_TAGS)
        self.rotor_tags: Dict[str, str] = dict(rotor_tags or DEFAULT_ROTOR_TAGS)
        self.conn: Any | None = None
        self.vessel: Any | None = None
        self.controllers: Dict[str, KALControllerBinding] = {}
        self.rotors: Dict[str, RotorBinding] = {}

    def connect(self, name: str = "KAL Rotor Test Rig") -> None:
        if self.conn is not None:
            return
        self.conn = krpc.connect(name=name)
        self.vessel = self.conn.space_center.active_vessel

    def disconnect(self) -> None:
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
        self.conn = None
        self.vessel = None
        self.controllers.clear()
        self.rotors.clear()

    @property
    def connected(self) -> bool:
        return self.conn is not None and self.vessel is not None

    def bind(self) -> None:
        if not self.connected:
            raise RuntimeError("Not connected to kRPC")
        assert self.vessel is not None
        self.controllers = {
            key: self._find_controller(key, tag) for key, tag in self.controller_tags.items()
        }
        self.rotors = {
            key: self._find_rotor(key, tag) for key, tag in self.rotor_tags.items()
        }

    def _find_controller(self, key: str, tag: str) -> KALControllerBinding:
        assert self.vessel is not None
        parts = self.vessel.parts.with_tag(tag)
        if len(parts) != 1:
            raise BindingError(f"Expected exactly one controller with tag {tag}, got {len(parts)}")
        part = parts[0]
        try:
            module = next(m for m in part.modules if m.name == "ModuleRoboticController")
        except StopIteration as exc:
            raise BindingError(f"Part {tag} does not have ModuleRoboticController") from exc
        return KALControllerBinding(key=key, part=part, module=module)

    def _find_rotor(self, key: str, tag: str) -> RotorBinding:
        assert self.vessel is not None
        parts = self.vessel.parts.with_tag(tag)
        if len(parts) != 1:
            raise BindingError(f"Expected exactly one rotor with tag {tag}, got {len(parts)}")
        part = parts[0]
        rotor = part.robotic_rotor
        if rotor is None:
            raise BindingError(f"Part {tag} is not a robotic rotor")
        return RotorBinding(key=key, part=part, rotor=rotor)

    def initialize_defaults(
        self,
        torque_limit: float = 100.0,
        play_speed_percent: float = 100.0,
        controller_enabled: bool = True,
        play_sequence: bool = True,
        direction_forward: bool = True,
        zero_play_position: bool = True,
        motor_engaged: bool = True,
        unlocked: bool = True,
    ) -> None:
        self.require_bound()
        for rotor in self.rotors.values():
            rotor.set_motor_engaged(motor_engaged)
            rotor.set_torque_limit(torque_limit)
            rotor.set_locked(not unlocked)
        for controller in self.controllers.values():
            controller.set_enabled(controller_enabled)
            controller.set_play_speed_percent(play_speed_percent)
            if direction_forward:
                controller.set_direction_forward()
            else:
                controller.set_direction_reverse()
            if zero_play_position:
                controller.set_play_position(0.0)
            if play_sequence:
                controller.play()
            else:
                controller.stop()

    def require_bound(self) -> None:
        if not self.controllers or not self.rotors:
            raise RuntimeError("Rig is not bound. Call bind() first.")

    @staticmethod
    def clamp_rpm(value: float) -> float:
        return max(RPM_MIN, min(RPM_MAX, float(value)))

    def set_rpm(self, key: str, rpm: float, clamp: bool = True) -> None:
        self.require_bound()
        value = self.clamp_rpm(rpm) if clamp else float(rpm)
        self.controllers[key].set_play_position(value)

    def set_all_rpm(self, rpm: float, clamp: bool = True) -> None:
        for key in self.controllers:
            self.set_rpm(key, rpm, clamp=clamp)

    def set_rpm_map(self, rpm_map: Mapping[str, float], clamp: bool = True) -> None:
        for key, value in rpm_map.items():
            self.set_rpm(key, value, clamp=clamp)

    def zero_all_positions(self) -> None:
        self.set_all_rpm(0.0)

    def play_all(self) -> None:
        for controller in self.controllers.values():
            controller.play()

    def stop_all(self) -> None:
        for controller in self.controllers.values():
            controller.stop()

    def enable_all_controllers(self) -> None:
        for controller in self.controllers.values():
            controller.set_enabled(True)

    def disable_all_controllers(self) -> None:
        for controller in self.controllers.values():
            controller.set_enabled(False)

    def set_all_play_speed_percent(self, value: float) -> None:
        for controller in self.controllers.values():
            controller.set_play_speed_percent(value)

    def set_all_direction_forward(self) -> None:
        for controller in self.controllers.values():
            controller.set_direction_forward()

    def set_all_direction_reverse(self) -> None:
        for controller in self.controllers.values():
            controller.set_direction_reverse()

    def set_all_loop_once(self) -> None:
        for controller in self.controllers.values():
            controller.set_loop_once()

    def set_all_loop_repeat(self) -> None:
        for controller in self.controllers.values():
            controller.set_loop_repeat()

    def set_all_loop_pingpong(self) -> None:
        for controller in self.controllers.values():
            controller.set_loop_pingpong()

    def set_all_loop_once_restart(self) -> None:
        for controller in self.controllers.values():
            controller.set_loop_once_restart()

    def set_all_torque_limit(self, value: float) -> None:
        for rotor in self.rotors.values():
            rotor.set_torque_limit(value)

    def engage_all_rotors(self) -> None:
        for rotor in self.rotors.values():
            rotor.set_motor_engaged(True)

    def disengage_all_rotors(self) -> None:
        for rotor in self.rotors.values():
            rotor.set_motor_engaged(False)

    def unlock_all_rotors(self) -> None:
        for rotor in self.rotors.values():
            rotor.set_locked(False)

    def lock_all_rotors(self) -> None:
        for rotor in self.rotors.values():
            rotor.set_locked(True)

    def emergency_stop(self) -> None:
        self.zero_all_positions()
        self.stop_all()
        self.disengage_all_rotors()

    def controller_snapshot(self, key: str) -> ControllerSnapshot:
        self.require_bound()
        return self.controllers[key].snapshot()

    def rotor_snapshot(self, key: str) -> RotorSnapshot:
        self.require_bound()
        return self.rotors[key].snapshot()

    def snapshot(self) -> RigSnapshot:
        if not self.connected:
            return RigSnapshot(
                connected=False,
                vessel_name="-",
                controller_tags=dict(self.controller_tags),
                rotor_tags=dict(self.rotor_tags),
                controllers={},
                rotors={},
            )
        controller_data: Dict[str, ControllerSnapshot] = {}
        rotor_data: Dict[str, RotorSnapshot] = {}
        if self.controllers and self.rotors:
            controller_data = {k: v.snapshot() for k, v in self.controllers.items()}
            rotor_data = {k: v.snapshot() for k, v in self.rotors.items()}
        vessel_name = self.vessel.name if self.vessel is not None else "-"
        return RigSnapshot(
            connected=True,
            vessel_name=vessel_name,
            controller_tags=dict(self.controller_tags),
            rotor_tags=dict(self.rotor_tags),
            controllers=controller_data,
            rotors=rotor_data,
        )
