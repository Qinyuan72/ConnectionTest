from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Tuple

Vector3 = Tuple[float, float, float]
Quaternion = Tuple[float, float, float, float]


def rfd_to_frd(v: Vector3) -> Vector3:
    """Convert kRPC vessel RF axes (Right, Forward, Down) -> (Forward, Right, Down)."""
    x_r, y_f, z_d = v
    return (y_f, x_r, z_d)


def une_to_ned(v: Vector3) -> Vector3:
    """Convert kRPC surface RF axes (Up, North, East) -> (North, East, Down)."""
    x_u, y_n, z_e = v
    return (y_n, z_e, -x_u)


@dataclass(frozen=True)
class AttitudeSnapshot:
    lat_deg: float = 0.0
    lon_deg: float = 0.0
    mean_alt_m: float = 0.0
    surface_alt_m: float = 0.0

    pitch_deg: float = 0.0
    heading_deg: float = 0.0
    roll_deg: float = 0.0

    # Display / analysis convenience only. Do not treat as a rigorous control state
    # without checking the exact Euler convention against your controller.
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


class AttitudeState:
    """Singleton-like shared attitude state."""

    _instance: "AttitudeState | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._snapshot = AttitudeSnapshot()
        return cls._instance

    @property
    def snapshot(self) -> AttitudeSnapshot:
        return self._snapshot

    def update_from_raw(
        self,
        *,
        lat_deg: float,
        lon_deg: float,
        mean_alt_m: float,
        surface_alt_m: float,
        pitch_deg: float,
        heading_deg: float,
        roll_deg: float,
        quat_surface_xyzw: Quaternion,
        direction_une: Vector3,
        velocity_une_m_s: Vector3,
        body_rates_rfd_rad_s: Vector3,
        speed_surface_m_s: float,
        horizontal_speed_surface_m_s: float,
        vertical_speed_surface_m_s: float,
        situation: str,
        mass_kg: float,
        thrust_n: float,
        available_thrust_n: float,
    ) -> None:
        body_rates_frd = rfd_to_frd(body_rates_rfd_rad_s)
        direction_ned = une_to_ned(direction_une)
        velocity_ned = une_to_ned(velocity_une_m_s)

        # Derived Euler angle rates for display/analysis.
        # Assumes standard aerospace FRD body rates:
        #   p about Forward (roll axis)
        #   q about Right   (pitch axis)
        #   r about Down    (yaw axis)
        phi = math.radians(roll_deg)
        theta = math.radians(pitch_deg)
        p, q, r = body_rates_frd

        cos_theta = math.cos(theta)
        if abs(cos_theta) < 1e-6:
            roll_rate = 0.0
            pitch_rate = 0.0
            yaw_rate = 0.0
        else:
            roll_rate = p + math.sin(phi) * math.tan(theta) * q + math.cos(phi) * math.tan(theta) * r
            pitch_rate = math.cos(phi) * q - math.sin(phi) * r
            yaw_rate = (math.sin(phi) / cos_theta) * q + (math.cos(phi) / cos_theta) * r

        self._snapshot = AttitudeSnapshot(
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            mean_alt_m=mean_alt_m,
            surface_alt_m=surface_alt_m,
            pitch_deg=pitch_deg,
            heading_deg=heading_deg,
            roll_deg=roll_deg,
            roll_rate_deg_s=math.degrees(roll_rate),
            pitch_rate_deg_s=math.degrees(pitch_rate),
            yaw_rate_deg_s=math.degrees(yaw_rate),
            body_rates_rfd_rad_s=body_rates_rfd_rad_s,
            body_rates_frd_rad_s=body_rates_frd,
            direction_une=direction_une,
            direction_ned=direction_ned,
            velocity_une_m_s=velocity_une_m_s,
            velocity_ned_m_s=velocity_ned,
            speed_surface_m_s=speed_surface_m_s,
            horizontal_speed_surface_m_s=horizontal_speed_surface_m_s,
            vertical_speed_surface_m_s=vertical_speed_surface_m_s,
            quat_surface_xyzw=quat_surface_xyzw,
            situation=situation,
            mass_kg=mass_kg,
            thrust_n=thrust_n,
            available_thrust_n=available_thrust_n,
        )
