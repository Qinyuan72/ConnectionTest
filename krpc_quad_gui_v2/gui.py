from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from krpc_facade import KrpcFacade


def fmt3(v, digits: int = 3) -> str:
    return f"({v[0]: .{digits}f}, {v[1]: .{digits}f}, {v[2]: .{digits}f})"


def fmt4(v, digits: int = 4) -> str:
    return f"({v[0]: .{digits}f}, {v[1]: .{digits}f}, {v[2]: .{digits}f}, {v[3]: .{digits}f})"


class TelemetryGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("kRPC Quadcopter Telemetry")
        self.root.geometry("920x620")
        self.root.minsize(820, 540)

        self.facade = KrpcFacade()
        self.update_ms = 100
        self._after_id: str | None = None

        self.status_var = tk.StringVar(value="Status: Connecting...")
        self.vessel_var = tk.StringVar(value="Vessel: -")
        self.body_var = tk.StringVar(value="Body: -")

        self.vars = {
            "lat": tk.StringVar(value="-"),
            "lon": tk.StringVar(value="-"),
            "mean_alt": tk.StringVar(value="-"),
            "surf_alt": tk.StringVar(value="-"),
            "pitch": tk.StringVar(value="-"),
            "heading": tk.StringVar(value="-"),
            "roll": tk.StringVar(value="-"),
            "roll_rate": tk.StringVar(value="-"),
            "pitch_rate": tk.StringVar(value="-"),
            "yaw_rate": tk.StringVar(value="-"),
            "dir_une": tk.StringVar(value="-"),
            "dir_ned": tk.StringVar(value="-"),
            "quat_surface": tk.StringVar(value="-"),
            "vel_local_une": tk.StringVar(value="-"),
            "vel_local_ned": tk.StringVar(value="-"),
            "speed_surface": tk.StringVar(value="-"),
            "hspeed_surface": tk.StringVar(value="-"),
            "vspeed_surface": tk.StringVar(value="-"),
            "omega_rfd": tk.StringVar(value="-"),
            "omega_frd": tk.StringVar(value="-"),
            "situation": tk.StringVar(value="-"),
            "mass": tk.StringVar(value="-"),
            "thrust": tk.StringVar(value="-"),
            "avail_thrust": tk.StringVar(value="-"),
        }

        self._build_ui()
        self.reconnect()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container)
        top.pack(fill="x", pady=(0, 8))

        ttk.Label(top, textvariable=self.status_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.vessel_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.body_var).pack(side="left", padx=(0, 16))
        ttk.Button(top, text="Reconnect", command=self.reconnect).pack(side="right")

        main = ttk.Frame(container)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self._make_group(
            left,
            "Basic / Flight Info",
            [
                ("Situation", "situation"),
                ("Latitude", "lat"),
                ("Longitude", "lon"),
                ("Mean Altitude (m)", "mean_alt"),
                ("Surface Altitude (m)", "surf_alt"),
                ("Mass (kg)", "mass"),
                ("Current Thrust (N)", "thrust"),
                ("Available Thrust (N)", "avail_thrust"),
            ],
        ).pack(fill="x", pady=4)

        self._make_group(
            left,
            "Attitude",
            [
                ("Pitch (deg)", "pitch"),
                ("Heading (deg)", "heading"),
                ("Roll (deg)", "roll"),
                ("Roll rate (deg/s)", "roll_rate"),
                ("Pitch rate (deg/s)", "pitch_rate"),
                ("Yaw rate (deg/s)", "yaw_rate"),
                ("Direction in surface RF [UNE]", "dir_une"),
                ("Direction converted [NED]", "dir_ned"),
                ("Quaternion in surface RF", "quat_surface"),
            ],
        ).pack(fill="x", pady=4)

        self._make_group(
            right,
            "Velocity",
            [
                ("Local surface velocity [UNE]", "vel_local_une"),
                ("Local surface velocity [NED]", "vel_local_ned"),
                ("Surface Speed (m/s)", "speed_surface"),
                ("Horizontal Speed (m/s)", "hspeed_surface"),
                ("Vertical Speed (m/s)", "vspeed_surface"),
            ],
        ).pack(fill="x", pady=4)

        self._make_group(
            right,
            "Angular Velocity",
            [
                ("Body rate [RFD, rel body] (rad/s)", "omega_rfd"),
                ("Body rate [FRD, rel body] (rad/s)", "omega_frd"),
            ],
        ).pack(fill="x", pady=4)

        note = ttk.Label(
            container,
            text=(
                "坐标说明：\n"
                "  Body raw = RFD (Right, Forward, Down)\n"
                "  Surface raw = UNE (Up, North, East)\n"
                "  Converted body = FRD (Forward, Right, Down)\n"
                "  Converted local = NED (North, East, Down)\n"
                "  欧拉角速度仅用于显示/分析；做控制前请再核对你的欧拉定义。"
            ),
            justify="left",
        )
        note.pack(fill="x", pady=(8, 0))

    def _make_group(self, parent, title, rows):
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        for i, (label_text, key) in enumerate(rows):
            ttk.Label(frame, text=label_text).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=4)
            ttk.Label(frame, textvariable=self.vars[key], font=("Consolas", 10)).grid(
                row=i, column=1, sticky="w", pady=4
            )
        return frame

    def _cancel_update_loop(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def reconnect(self) -> None:
        self._cancel_update_loop()
        try:
            self.facade.close()
        except Exception:
            pass

        try:
            self.facade = KrpcFacade()
            self.facade.connect()
            vessel_name = self.facade.vessel.name if self.facade.vessel else "-"
            body_name = self.facade.body.name if self.facade.body else "-"
            self.status_var.set("Status: Connected")
            self.vessel_var.set(f"Vessel: {vessel_name}")
            self.body_var.set(f"Body: {body_name}")
            self._update_loop()
        except Exception as exc:
            self.status_var.set(f"Status: Connection failed - {exc}")
            self.vessel_var.set("Vessel: -")
            self.body_var.set("Body: -")

    def _update_loop(self) -> None:
        try:
            self.facade.refresh()
            s = self.facade.get_snapshot()

            self.vars["lat"].set(f"{s.lat_deg:.6f}")
            self.vars["lon"].set(f"{s.lon_deg:.6f}")
            self.vars["mean_alt"].set(f"{s.mean_alt_m:.3f}")
            self.vars["surf_alt"].set(f"{s.surface_alt_m:.3f}")

            self.vars["pitch"].set(f"{s.pitch_deg:.3f}")
            self.vars["heading"].set(f"{s.heading_deg:.3f}")
            self.vars["roll"].set(f"{s.roll_deg:.3f}")
            self.vars["roll_rate"].set(f"{s.roll_rate_deg_s:.3f}")
            self.vars["pitch_rate"].set(f"{s.pitch_rate_deg_s:.3f}")
            self.vars["yaw_rate"].set(f"{s.yaw_rate_deg_s:.3f}")

            self.vars["dir_une"].set(fmt3(s.direction_une))
            self.vars["dir_ned"].set(fmt3(s.direction_ned))
            self.vars["quat_surface"].set(fmt4(s.quat_surface_xyzw))

            self.vars["vel_local_une"].set(fmt3(s.velocity_une_m_s))
            self.vars["vel_local_ned"].set(fmt3(s.velocity_ned_m_s))
            self.vars["speed_surface"].set(f"{s.speed_surface_m_s:.3f}")
            self.vars["hspeed_surface"].set(f"{s.horizontal_speed_surface_m_s:.3f}")
            self.vars["vspeed_surface"].set(f"{s.vertical_speed_surface_m_s:.3f}")

            self.vars["omega_rfd"].set(fmt3(s.body_rates_rfd_rad_s, digits=4))
            self.vars["omega_frd"].set(fmt3(s.body_rates_frd_rad_s, digits=4))

            self.vars["situation"].set(s.situation)
            self.vars["mass"].set(f"{s.mass_kg:.3f}")
            self.vars["thrust"].set(f"{s.thrust_n:.3f}")
            self.vars["avail_thrust"].set(f"{s.available_thrust_n:.3f}")

            self.status_var.set("Status: Connected / Updating")
        except Exception as exc:
            self.status_var.set(f"Status: Update error - {exc}")

        self._after_id = self.root.after(self.update_ms, self._update_loop)

    def on_close(self) -> None:
        self._cancel_update_loop()
        try:
            self.facade.close()
        finally:
            self.root.destroy()
