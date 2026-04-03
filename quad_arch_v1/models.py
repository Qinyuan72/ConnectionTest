from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]
ControlMode = Literal["manual", "stabilize", "altitude_hold"]


@dataclass(frozen=True)
class RawTelemetry:
    """Raw values read from the telemetry boundary adapter."""

    lat_deg: float = 0.0
    lon_deg: float = 0.0
    mean_alt_m: float = 0.0
    surface_alt_m: float = 0.0
    pitch_deg: float = 0.0
    heading_deg: float = 0.0
    roll_deg: float = 0.0
    body_rates_rfd_rad_s: Vector3 = (0.0, 0.0, 0.0)
    direction_une: Vector3 = (0.0, 0.0, 0.0)
    velocity_une_m_s: Vector3 = (0.0, 0.0, 0.0)
    speed_surface_m_s: float = 0.0
    horizontal_speed_surface_m_s: float = 0.0
    vertical_speed_surface_m_s: float = 0.0
    quat_surface_xyzw: Quaternion = (0.0, 0.0, 0.0, 1.0)
    situation: str = "-"
    mass_kg: float = 0.0
    thrust_n: float = 0.0
    available_thrust_n: float = 0.0
    timestamp_s: float = 0.0


@dataclass(frozen=True)
class ProcessedState:
    """Processed telemetry state used by the GUI and future controllers."""

    lat_deg: float = 0.0
    lon_deg: float = 0.0
    mean_alt_m: float = 0.0
    surface_alt_m: float = 0.0
    pitch_deg: float = 0.0
    heading_deg: float = 0.0
    roll_deg: float = 0.0
    roll_rate_deg_s: float = 0.0
    pitch_rate_deg_s: float = 0.0
    yaw_rate_deg_s: float = 0.0
    body_rates_rfd_rad_s: Vector3 = (0.0, 0.0, 0.0)
    body_rates_frd_rad_s: Vector3 = (0.0, 0.0, 0.0)
    direction_une: Vector3 = (0.0, 0.0, 0.0)
    direction_ned: Vector3 = (0.0, 0.0, 0.0)
    velocity_une_m_s: Vector3 = (0.0, 0.0, 0.0)
    velocity_ned_m_s: Vector3 = (0.0, 0.0, 0.0)
    speed_surface_m_s: float = 0.0
    horizontal_speed_surface_m_s: float = 0.0
    vertical_speed_surface_m_s: float = 0.0
    quat_surface_xyzw: Quaternion = (0.0, 0.0, 0.0, 1.0)
    situation: str = "-"
    mass_kg: float = 0.0
    thrust_n: float = 0.0
    available_thrust_n: float = 0.0
    timestamp_s: float = 0.0
    dt_s: float = 0.0


@dataclass(frozen=True)
class PilotIntent:
    """User intent submitted from the GUI into the write path."""

    mode: str = "manual"
    roll_cmd_deg: float = 0.0
    pitch_cmd_deg: float = 0.0
    yaw_rate_cmd_deg_s: float = 0.0
    altitude_cmd_m: float | None = None
    throttle_cmd_norm: float | None = None
    armed: bool = False


@dataclass(frozen=True)
class ActuatorCommand:
    """Controller output handed to the actuator sink boundary."""

    motor_throttles: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    collective_throttle_norm: float = 0.0
    enable_output: bool = False
    mode: str = "manual"
    notes: tuple[str, ...] = field(default_factory=tuple)
