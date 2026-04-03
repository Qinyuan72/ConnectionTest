from __future__ import annotations

from typing import Any, Dict

import krpc

from attitude_state import AttitudeState, AttitudeSnapshot


class KrpcFacade:
    """Facade over kRPC connection + streams + reference frame plumbing."""

    def __init__(self) -> None:
        self.conn = None
        self.vessel = None
        self.body = None
        self.state = AttitudeState()
        self.streams: Dict[str, Any] = {}
        self.connected = False

    def connect(self) -> None:
        if self.connected:
            return

        self.conn = krpc.connect(name="Quad Telemetry Facade")
        sc = self.conn.space_center
        self.vessel = sc.active_vessel
        self.body = self.vessel.orbit.body

        vessel_rf = self.vessel.reference_frame
        surface_rf = self.vessel.surface_reference_frame
        body_rf = self.body.reference_frame

        # Hybrid frame: centered and moving with the ground/body frame, but axes aligned with
        # the vessel's local surface frame, per kRPC reference-frame tutorial.
        local_surface_velocity_rf = self.conn.space_center.ReferenceFrame.create_hybrid(
            position=body_rf,
            rotation=surface_rf,
        )

        flight_default = self.vessel.flight()  # default surface RF; fine for lat/lon/alt/pitch/heading/roll
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
            "quat_surface_xyzw": self.conn.add_stream(self.vessel.rotation, surface_rf),
            "direction_une": self.conn.add_stream(self.vessel.direction, surface_rf),
            "velocity_une_m_s": self.conn.add_stream(getattr, flight_local_velocity, "velocity"),
            "body_rates_rfd_rad_s": self.conn.add_stream(self.vessel.angular_velocity, vessel_rf),
            "speed_surface_m_s": self.conn.add_stream(getattr, flight_surface_speed, "speed"),
            "horizontal_speed_surface_m_s": self.conn.add_stream(getattr, flight_surface_speed, "horizontal_speed"),
            "vertical_speed_surface_m_s": self.conn.add_stream(getattr, flight_surface_speed, "vertical_speed"),
        }

        self.connected = True

    def refresh(self) -> None:
        if not self.connected:
            raise RuntimeError("kRPC is not connected")

        self.state.update_from_raw(
            lat_deg=self.streams["lat_deg"](),
            lon_deg=self.streams["lon_deg"](),
            mean_alt_m=self.streams["mean_alt_m"](),
            surface_alt_m=self.streams["surface_alt_m"](),
            pitch_deg=self.streams["pitch_deg"](),
            heading_deg=self.streams["heading_deg"](),
            roll_deg=self.streams["roll_deg"](),
            quat_surface_xyzw=self.streams["quat_surface_xyzw"](),
            direction_une=self.streams["direction_une"](),
            velocity_une_m_s=self.streams["velocity_une_m_s"](),
            body_rates_rfd_rad_s=self.streams["body_rates_rfd_rad_s"](),
            speed_surface_m_s=self.streams["speed_surface_m_s"](),
            horizontal_speed_surface_m_s=self.streams["horizontal_speed_surface_m_s"](),
            vertical_speed_surface_m_s=self.streams["vertical_speed_surface_m_s"](),
        )

    def get_snapshot(self) -> AttitudeSnapshot:
        return self.state.snapshot

    def close(self) -> None:
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
        self.connected = False
