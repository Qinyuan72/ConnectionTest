from __future__ import annotations

import math

from .models import ProcessedState, RawTelemetry, Vector3


def rfd_to_frd(vector: Vector3) -> Vector3:
    """Convert kRPC vessel axes from RFD to FRD."""

    x_right, y_forward, z_down = vector
    return (y_forward, x_right, z_down)


def une_to_ned(vector: Vector3) -> Vector3:
    """Convert local surface axes from UNE to NED."""

    x_up, y_north, z_east = vector
    return (y_north, z_east, -x_up)


class TelemetryProcessor:
    """Translate raw telemetry into a processed, controller-friendly state."""

    def __init__(self) -> None:
        self._last_timestamp_s: float | None = None

    def process(self, raw: RawTelemetry) -> ProcessedState:
        """Convert frames, derive rates, and compute sample period."""

        body_rates_frd = rfd_to_frd(self._sanitize_vector(raw.body_rates_rfd_rad_s))
        direction_une = self._sanitize_vector(raw.direction_une)
        velocity_une = self._sanitize_vector(raw.velocity_une_m_s)
        direction_ned = une_to_ned(direction_une)
        velocity_ned = une_to_ned(velocity_une)
        dt_s = self._calculate_dt(raw.timestamp_s)

        roll_rate_deg_s, pitch_rate_deg_s, yaw_rate_deg_s = self._derive_euler_rates(
            roll_deg=raw.roll_deg,
            pitch_deg=raw.pitch_deg,
            body_rates_frd_rad_s=body_rates_frd,
        )

        return ProcessedState(
            lat_deg=self._sanitize_scalar(raw.lat_deg),
            lon_deg=self._sanitize_scalar(raw.lon_deg),
            mean_alt_m=self._sanitize_scalar(raw.mean_alt_m),
            surface_alt_m=self._sanitize_scalar(raw.surface_alt_m),
            pitch_deg=self._sanitize_scalar(raw.pitch_deg),
            heading_deg=self._sanitize_scalar(raw.heading_deg),
            roll_deg=self._sanitize_scalar(raw.roll_deg),
            roll_rate_deg_s=roll_rate_deg_s,
            pitch_rate_deg_s=pitch_rate_deg_s,
            yaw_rate_deg_s=yaw_rate_deg_s,
            body_rates_rfd_rad_s=self._sanitize_vector(raw.body_rates_rfd_rad_s),
            body_rates_frd_rad_s=body_rates_frd,
            direction_une=direction_une,
            direction_ned=direction_ned,
            velocity_une_m_s=velocity_une,
            velocity_ned_m_s=velocity_ned,
            speed_surface_m_s=self._sanitize_scalar(raw.speed_surface_m_s),
            horizontal_speed_surface_m_s=self._sanitize_scalar(raw.horizontal_speed_surface_m_s),
            vertical_speed_surface_m_s=self._sanitize_scalar(raw.vertical_speed_surface_m_s),
            quat_surface_xyzw=self._sanitize_quaternion(raw.quat_surface_xyzw),
            situation=str(raw.situation),
            mass_kg=self._sanitize_scalar(raw.mass_kg),
            thrust_n=self._sanitize_scalar(raw.thrust_n),
            available_thrust_n=self._sanitize_scalar(raw.available_thrust_n),
            timestamp_s=max(0.0, self._sanitize_scalar(raw.timestamp_s)),
            dt_s=dt_s,
        )

    def _calculate_dt(self, timestamp_s: float) -> float:
        timestamp_s = max(0.0, self._sanitize_scalar(timestamp_s))
        if self._last_timestamp_s is None:
            self._last_timestamp_s = timestamp_s
            return 0.0

        dt_s = timestamp_s - self._last_timestamp_s
        self._last_timestamp_s = timestamp_s
        if dt_s < 0.0 or not math.isfinite(dt_s):
            return 0.0
        return dt_s

    def _derive_euler_rates(
        self,
        *,
        roll_deg: float,
        pitch_deg: float,
        body_rates_frd_rad_s: Vector3,
    ) -> tuple[float, float, float]:
        """Estimate Euler angle rates from FRD body rates for display."""

        phi = math.radians(self._sanitize_scalar(roll_deg))
        theta = math.radians(self._sanitize_scalar(pitch_deg))
        p_rate, q_rate, r_rate = body_rates_frd_rad_s

        cos_theta = math.cos(theta)
        if abs(cos_theta) < 1e-6:
            return (0.0, 0.0, 0.0)

        roll_rate = p_rate + math.sin(phi) * math.tan(theta) * q_rate + math.cos(phi) * math.tan(theta) * r_rate
        pitch_rate = math.cos(phi) * q_rate - math.sin(phi) * r_rate
        yaw_rate = (math.sin(phi) / cos_theta) * q_rate + (math.cos(phi) / cos_theta) * r_rate
        return (
            math.degrees(roll_rate),
            math.degrees(pitch_rate),
            math.degrees(yaw_rate),
        )

    def _sanitize_scalar(self, value: float) -> float:
        if not math.isfinite(value):
            return 0.0
        return value

    def _sanitize_vector(self, vector: Vector3) -> Vector3:
        return tuple(self._sanitize_scalar(component) for component in vector)

    def _sanitize_quaternion(self, quat: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        return tuple(self._sanitize_scalar(component) for component in quat)
