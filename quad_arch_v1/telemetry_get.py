from __future__ import annotations

import time
from typing import Any

try:
    import krpc
except ImportError:  # pragma: no cover - depends on local environment
    krpc = None

from .models import RawTelemetry


class KrpcTelemetrySource:
    """kRPC input adapter that owns the connection and raw streams."""

    def __init__(self) -> None:
        self.conn: Any | None = None
        self.vessel: Any | None = None
        self.body: Any | None = None
        self.streams: dict[str, Any] = {}
        self._connected = False

    def connect(self) -> None:
        if self._connected:
            return
        if krpc is None:
            raise RuntimeError("kRPC Python package is not installed.")

        self.conn = krpc.connect(name="quad_arch_v1 telemetry")
        space_center = self.conn.space_center
        self.vessel = space_center.active_vessel
        self.body = self.vessel.orbit.body

        vessel_rf = self.vessel.reference_frame
        surface_rf = self.vessel.surface_reference_frame
        body_rf = self.body.reference_frame

        local_surface_velocity_rf = self.conn.space_center.ReferenceFrame.create_hybrid(
            position=body_rf,
            rotation=surface_rf,
        )

        # IMPORTANT:
        # A vessel-aligned frame that also rotates with the vessel makes angular
        # velocity collapse toward zero. The hybrid frame below keeps the vessel
        # axes but measures angular velocity relative to the body/surface frame.
        body_axes_surface_rate_rf = self.conn.space_center.ReferenceFrame.create_hybrid(
            position=vessel_rf,
            rotation=vessel_rf,
            velocity=body_rf,
            angular_velocity=body_rf,
        )

        flight_default = self.vessel.flight()
        flight_surface_speed = self.vessel.flight(body_rf)
        flight_local_velocity = self.vessel.flight(local_surface_velocity_rf)

        self.streams = {
            "lat_deg": self.conn.add_stream(getattr, flight_default, "latitude"),
            "lon_deg": self.conn.add_stream(getattr, flight_default, "longitude"),
            "mean_alt_m": self.conn.add_stream(getattr, flight_default, "mean_altitude"),
            "surface_alt_m": self.conn.add_stream(getattr, flight_default, "surface_altitude"),
            "pitch_deg": self.conn.add_stream(getattr, flight_default, "pitch"),
            "heading_deg": self.conn.add_stream(getattr, flight_default, "heading"),
            "roll_deg": self.conn.add_stream(getattr, flight_default, "roll"),
            "body_rates_rfd_rad_s": self.conn.add_stream(self.vessel.angular_velocity, body_axes_surface_rate_rf),
            "direction_une": self.conn.add_stream(self.vessel.direction, surface_rf),
            "velocity_une_m_s": self.conn.add_stream(getattr, flight_local_velocity, "velocity"),
            "speed_surface_m_s": self.conn.add_stream(getattr, flight_surface_speed, "speed"),
            "horizontal_speed_surface_m_s": self.conn.add_stream(getattr, flight_surface_speed, "horizontal_speed"),
            "vertical_speed_surface_m_s": self.conn.add_stream(getattr, flight_surface_speed, "vertical_speed"),
            "quat_surface_xyzw": self.conn.add_stream(self.vessel.rotation, surface_rf),
            "situation": self.conn.add_stream(getattr, self.vessel, "situation"),
            "mass_kg": self.conn.add_stream(getattr, self.vessel, "mass"),
            "thrust_n": self.conn.add_stream(getattr, self.vessel, "thrust"),
            "available_thrust_n": self.conn.add_stream(getattr, self.vessel, "available_thrust"),
        }
        self._connected = True

    def disconnect(self) -> None:
        for stream in self.streams.values():
            try:
                stream.remove()
            except Exception:
                pass
        self.streams.clear()

        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass

        self.conn = None
        self.vessel = None
        self.body = None
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_raw(self) -> RawTelemetry:
        if not self._connected:
            raise RuntimeError("Telemetry source is not connected.")

        return RawTelemetry(
            lat_deg=float(self.streams["lat_deg"]()),
            lon_deg=float(self.streams["lon_deg"]()),
            mean_alt_m=float(self.streams["mean_alt_m"]()),
            surface_alt_m=float(self.streams["surface_alt_m"]()),
            pitch_deg=float(self.streams["pitch_deg"]()),
            heading_deg=float(self.streams["heading_deg"]()),
            roll_deg=float(self.streams["roll_deg"]()),
            body_rates_rfd_rad_s=tuple(self.streams["body_rates_rfd_rad_s"]()),
            direction_une=tuple(self.streams["direction_une"]()),
            velocity_une_m_s=tuple(self.streams["velocity_une_m_s"]()),
            speed_surface_m_s=float(self.streams["speed_surface_m_s"]()),
            horizontal_speed_surface_m_s=float(self.streams["horizontal_speed_surface_m_s"]()),
            vertical_speed_surface_m_s=float(self.streams["vertical_speed_surface_m_s"]()),
            quat_surface_xyzw=tuple(self.streams["quat_surface_xyzw"]()),
            situation=str(self.streams["situation"]()),
            mass_kg=float(self.streams["mass_kg"]()),
            thrust_n=float(self.streams["thrust_n"]()),
            available_thrust_n=float(self.streams["available_thrust_n"]()),
            timestamp_s=time.monotonic(),
        )
