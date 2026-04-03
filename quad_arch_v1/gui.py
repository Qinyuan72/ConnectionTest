from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .app_runtime import AppRuntime
from .models import PilotIntent


def fmt3(vector: tuple[float, float, float], digits: int = 3) -> str:
    return f"({vector[0]: .{digits}f}, {vector[1]: .{digits}f}, {vector[2]: .{digits}f})"


class QuadArchGUI:
    """Tkinter GUI that observes processed state and submits pilot intent."""

    def __init__(self, root: tk.Tk, runtime: AppRuntime) -> None:
        self.root = root
        self.runtime = runtime
        self.update_ms = 100
        self._after_id: str | None = None

        self.root.title("quad_arch_v1 telemetry and control shell")
        self.root.geometry("1280x760")
        self.root.minsize(1080, 680)

        self.status_var = tk.StringVar(value="Status: Disconnected")
        self.connection_var = tk.StringVar(value="Telemetry: not connected")
        self.command_status_var = tk.StringVar(value="Last command: none")

        self.mode_var = tk.StringVar(value=self.runtime.get_intent().mode)
        self.armed_var = tk.BooleanVar(value=self.runtime.get_intent().armed)
        self.roll_cmd_var = tk.StringVar(value="0.0")
        self.pitch_cmd_var = tk.StringVar(value="0.0")
        self.yaw_rate_cmd_var = tk.StringVar(value="0.0")
        self.altitude_cmd_var = tk.StringVar(value="")
        self.throttle_cmd_var = tk.StringVar(value="")

        self.state_vars = {
            "pitch_deg": tk.StringVar(value="-"),
            "heading_deg": tk.StringVar(value="-"),
            "roll_deg": tk.StringVar(value="-"),
            "roll_rate_deg_s": tk.StringVar(value="-"),
            "pitch_rate_deg_s": tk.StringVar(value="-"),
            "yaw_rate_deg_s": tk.StringVar(value="-"),
            "body_rates_frd_rad_s": tk.StringVar(value="-"),
            "velocity_ned_m_s": tk.StringVar(value="-"),
            "mean_alt_m": tk.StringVar(value="-"),
            "surface_alt_m": tk.StringVar(value="-"),
            "vertical_speed_surface_m_s": tk.StringVar(value="-"),
            "thrust_n": tk.StringVar(value="-"),
            "mass_kg": tk.StringVar(value="-"),
            "situation": tk.StringVar(value="-"),
            "dt_s": tk.StringVar(value="-"),
            "timestamp_s": tk.StringVar(value="-"),
        }

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(outer)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, textvariable=self.status_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.connection_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.command_status_var).pack(side="left", padx=(0, 16))

        splitter = ttk.Panedwindow(outer, orient=tk.HORIZONTAL)
        splitter.pack(fill="both", expand=True)

        left = ttk.Frame(splitter, padding=(0, 0, 8, 0))
        right = ttk.Frame(splitter, padding=(8, 0, 0, 0))
        splitter.add(left, weight=3)
        splitter.add(right, weight=2)

        self._build_telemetry_panel(left)
        self._build_control_panel(right)
        self._build_visual_placeholder(right)

    def _build_telemetry_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Telemetry / Processed State", padding=10)
        frame.pack(fill="both", expand=True)

        rows = [
            ("Pitch (deg)", "pitch_deg"),
            ("Heading (deg)", "heading_deg"),
            ("Roll (deg)", "roll_deg"),
            ("Roll rate (deg/s)", "roll_rate_deg_s"),
            ("Pitch rate (deg/s)", "pitch_rate_deg_s"),
            ("Yaw rate (deg/s)", "yaw_rate_deg_s"),
            ("Body rates FRD (rad/s)", "body_rates_frd_rad_s"),
            ("Velocity NED (m/s)", "velocity_ned_m_s"),
            ("Mean altitude (m)", "mean_alt_m"),
            ("Surface altitude (m)", "surface_alt_m"),
            ("Vertical speed (m/s)", "vertical_speed_surface_m_s"),
            ("Thrust (N)", "thrust_n"),
            ("Mass (kg)", "mass_kg"),
            ("Situation", "situation"),
            ("dt (s)", "dt_s"),
            ("Timestamp (s)", "timestamp_s"),
        ]

        for row_index, (label, key) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=row_index, column=0, sticky="w", padx=(0, 12), pady=4)
            ttk.Label(frame, textvariable=self.state_vars[key], font=("Consolas", 10)).grid(
                row=row_index,
                column=1,
                sticky="w",
                pady=4,
            )

        note = ttk.Label(
            frame,
            justify="left",
            text=(
                "Reference-frame note:\n"
                "  Raw kRPC body rates arrive in RFD and raw local vectors arrive in UNE.\n"
                "  This GUI only consumes processed FRD and NED values from the runtime."
            ),
        )
        note.grid(row=len(rows), column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_control_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="User Intent / Control Placeholders", padding=10)
        frame.pack(fill="x", expand=False, pady=(0, 8))

        ttk.Label(frame, text="Mode").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Combobox(
            frame,
            textvariable=self.mode_var,
            values=("manual", "stabilize", "altitude_hold"),
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(frame, text="Armed", variable=self.armed_var).grid(row=1, column=1, sticky="w", pady=4)

        self._add_entry_row(frame, 2, "Roll command (deg)", self.roll_cmd_var)
        self._add_entry_row(frame, 3, "Pitch command (deg)", self.pitch_cmd_var)
        self._add_entry_row(frame, 4, "Yaw rate command (deg/s)", self.yaw_rate_cmd_var)
        self._add_entry_row(frame, 5, "Altitude command (m)", self.altitude_cmd_var)
        self._add_entry_row(frame, 6, "Throttle command (0..1)", self.throttle_cmd_var)

        button_row = ttk.Frame(frame)
        button_row.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(button_row, text="Connect", command=self.connect).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Disconnect", command=self.disconnect).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Apply Intent", command=self.apply_intent).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Neutral Intent", command=self.apply_neutral_intent).pack(side="left")

        frame.columnconfigure(1, weight=1)

    def _build_visual_placeholder(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Reserved 3D Visualization Area", padding=10)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text=(
                "Reserved for 3D vector visualization\n\n"
                "Future work can render direction, velocity, and body-rate vectors here\n"
                "without changing the GUI/runtime boundary."
            ),
            justify="center",
            anchor="center",
        ).pack(fill="both", expand=True)

    def _add_entry_row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Entry(parent, textvariable=variable, width=18).grid(row=row, column=1, sticky="ew", pady=4)

    def connect(self) -> None:
        try:
            self.runtime.connect()
            self.status_var.set("Status: Connected")
            self.connection_var.set("Telemetry: connected")
            self._schedule_update_loop()
        except Exception as exc:
            self.status_var.set(f"Status: Connection failed - {exc}")
            self.connection_var.set("Telemetry: disconnected")

    def disconnect(self) -> None:
        self._cancel_update_loop()
        try:
            self.runtime.disconnect()
        except Exception as exc:
            self.status_var.set(f"Status: Disconnect error - {exc}")
        else:
            self.status_var.set("Status: Disconnected")
            self.connection_var.set("Telemetry: not connected")

    def apply_intent(self) -> None:
        intent = PilotIntent(
            mode=self.mode_var.get(),
            roll_cmd_deg=self._parse_float(self.roll_cmd_var.get(), default=0.0),
            pitch_cmd_deg=self._parse_float(self.pitch_cmd_var.get(), default=0.0),
            yaw_rate_cmd_deg_s=self._parse_float(self.yaw_rate_cmd_var.get(), default=0.0),
            altitude_cmd_m=self._parse_optional_float(self.altitude_cmd_var.get()),
            throttle_cmd_norm=self._parse_optional_float(self.throttle_cmd_var.get()),
            armed=self.armed_var.get(),
        )
        self.runtime.set_intent(intent)
        command = self.runtime.control_tick()
        self.command_status_var.set(
            f"Last command: mode={command.mode} enabled={command.enable_output} throttle={command.collective_throttle_norm:.2f}"
        )

    def apply_neutral_intent(self) -> None:
        neutral = PilotIntent()
        self.mode_var.set(neutral.mode)
        self.armed_var.set(neutral.armed)
        self.roll_cmd_var.set("0.0")
        self.pitch_cmd_var.set("0.0")
        self.yaw_rate_cmd_var.set("0.0")
        self.altitude_cmd_var.set("")
        self.throttle_cmd_var.set("")
        self.runtime.set_intent(neutral)
        self.command_status_var.set("Last command: neutral intent staged")

    def _schedule_update_loop(self) -> None:
        self._cancel_update_loop()
        self._update_loop()

    def _update_loop(self) -> None:
        try:
            state = self.runtime.telemetry_tick()
            self._render_state(state)
            self.status_var.set("Status: Connected / Updating")
            self.connection_var.set("Telemetry: connected")
        except Exception as exc:
            self.status_var.set(f"Status: Update error - {exc}")
            self.connection_var.set("Telemetry: update failed")

        if self.runtime.is_connected():
            self._after_id = self.root.after(self.update_ms, self._update_loop)

    def _render_state(self, state) -> None:
        self.state_vars["pitch_deg"].set(f"{state.pitch_deg:.3f}")
        self.state_vars["heading_deg"].set(f"{state.heading_deg:.3f}")
        self.state_vars["roll_deg"].set(f"{state.roll_deg:.3f}")
        self.state_vars["roll_rate_deg_s"].set(f"{state.roll_rate_deg_s:.3f}")
        self.state_vars["pitch_rate_deg_s"].set(f"{state.pitch_rate_deg_s:.3f}")
        self.state_vars["yaw_rate_deg_s"].set(f"{state.yaw_rate_deg_s:.3f}")
        self.state_vars["body_rates_frd_rad_s"].set(fmt3(state.body_rates_frd_rad_s, digits=4))
        self.state_vars["velocity_ned_m_s"].set(fmt3(state.velocity_ned_m_s))
        self.state_vars["mean_alt_m"].set(f"{state.mean_alt_m:.3f}")
        self.state_vars["surface_alt_m"].set(f"{state.surface_alt_m:.3f}")
        self.state_vars["vertical_speed_surface_m_s"].set(f"{state.vertical_speed_surface_m_s:.3f}")
        self.state_vars["thrust_n"].set(f"{state.thrust_n:.3f}")
        self.state_vars["mass_kg"].set(f"{state.mass_kg:.3f}")
        self.state_vars["situation"].set(state.situation)
        self.state_vars["dt_s"].set(f"{state.dt_s:.4f}")
        self.state_vars["timestamp_s"].set(f"{state.timestamp_s:.3f}")

    def _cancel_update_loop(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _parse_float(self, text: str, *, default: float) -> float:
        try:
            return float(text.strip())
        except ValueError:
            return default

    def _parse_optional_float(self, text: str) -> float | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None

    def on_close(self) -> None:
        self._cancel_update_loop()
        try:
            self.runtime.disconnect()
        except Exception:
            pass
        self.root.destroy()
