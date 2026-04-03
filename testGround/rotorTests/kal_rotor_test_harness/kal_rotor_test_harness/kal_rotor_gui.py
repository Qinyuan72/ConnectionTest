from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Dict

from kal_rotor_api import KALRotorRig, RPM_MAX

_KEYS = ("FL", "FR", "RL", "RR")


class KALRotorTestGUI:
    def __init__(self, root: tk.Tk, rig: KALRotorRig) -> None:
        self.root = root
        self.rig = rig
        self.root.title("KAL + Rotor Test Harness")
        self.root.geometry("1180x760")
        self.root.minsize(1040, 680)
        self.refresh_ms = 500

        self.status_var = tk.StringVar(value="Disconnected")
        self.vessel_var = tk.StringVar(value="Vessel: -")
        self.auto_refresh_var = tk.BooleanVar(value=True)

        self.global_rpm_var = tk.StringVar(value="0")
        self.torque_var = tk.StringVar(value="100")
        self.play_speed_var = tk.StringVar(value="100")

        self.per_key_rpm_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="0") for k in _KEYS}
        self.per_key_cmd_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}
        self.per_key_actual_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}
        self.per_key_torque_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}
        self.per_key_enabled_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}
        self.per_key_engaged_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}
        self.per_key_loop_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}
        self.per_key_direction_vars: Dict[str, tk.StringVar] = {k: tk.StringVar(value="-") for k in _KEYS}

        self.selected_key_var = tk.StringVar(value="FL")
        self.selected_tag_var = tk.StringVar(value="-")
        self.selected_rotor_tag_var = tk.StringVar(value="-")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._schedule_refresh()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(outer)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, textvariable=self.status_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.vessel_var).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(top, text="Auto Refresh", variable=self.auto_refresh_var).pack(side="right")

        main = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, padding=4)
        right = ttk.Frame(main, padding=4)
        main.add(left, weight=5)
        main.add(right, weight=4)

        self._build_connection_panel(left)
        self._build_overview_panel(left)
        self._build_global_actions_panel(left)
        self._build_per_motor_panel(left)

        self._build_selected_detail_panel(right)
        self._build_log_panel(right)

    def _build_connection_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Connection / Binding", padding=8)
        frame.pack(fill="x", pady=4)
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Button(row, text="Connect", command=self.connect).pack(side="left", padx=2)
        ttk.Button(row, text="Bind Tags", command=self.bind).pack(side="left", padx=2)
        ttk.Button(row, text="Disconnect", command=self.disconnect).pack(side="left", padx=2)
        ttk.Button(row, text="Refresh Now", command=self.refresh_view).pack(side="left", padx=2)

    def _build_overview_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Live Overview", padding=8)
        frame.pack(fill="x", pady=4)
        header = ttk.Frame(frame)
        header.pack(fill="x")
        cols = [
            ("Key", 6),
            ("Cmd RPM", 12),
            ("Actual RPM", 12),
            ("Torque", 10),
            ("Ctrl Enabled", 12),
            ("Rotor Engaged", 12),
            ("Loop", 10),
            ("Dir", 8),
        ]
        for title, width in cols:
            ttk.Label(header, text=title, width=width).pack(side="left", padx=2)

        for key in _KEYS:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=1)
            ttk.Radiobutton(
                row,
                text=key,
                value=key,
                variable=self.selected_key_var,
                command=self._update_selected_detail,
                width=6,
            ).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_cmd_vars[key], width=12).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_actual_vars[key], width=12).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_torque_vars[key], width=10).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_enabled_vars[key], width=12).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_engaged_vars[key], width=12).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_loop_vars[key], width=10).pack(side="left", padx=2)
            ttk.Label(row, textvariable=self.per_key_direction_vars[key], width=8).pack(side="left", padx=2)

    def _build_global_actions_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Global Test Actions", padding=8)
        frame.pack(fill="x", pady=4)

        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="All RPM").pack(side="left")
        ttk.Entry(row1, textvariable=self.global_rpm_var, width=10).pack(side="left", padx=4)
        ttk.Button(row1, text="Apply All RPM", command=self.apply_all_rpm).pack(side="left", padx=2)
        ttk.Button(row1, text="Zero All", command=self.zero_all).pack(side="left", padx=2)
        ttk.Button(row1, text="Emergency Stop", command=self.emergency_stop).pack(side="left", padx=2)

        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Torque %").pack(side="left")
        ttk.Entry(row2, textvariable=self.torque_var, width=10).pack(side="left", padx=4)
        ttk.Button(row2, text="Set All Torque", command=self.set_all_torque).pack(side="left", padx=2)
        ttk.Label(row2, text="Play Speed %").pack(side="left", padx=(12, 0))
        ttk.Entry(row2, textvariable=self.play_speed_var, width=10).pack(side="left", padx=4)
        ttk.Button(row2, text="Set All Play Speed", command=self.set_all_play_speed).pack(side="left", padx=2)

        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=2)
        for text, cmd in [
            ("Init Defaults", self.initialize_defaults),
            ("Play All", self.play_all),
            ("Stop All", self.stop_all),
            ("Enable Ctrl", self.enable_all),
            ("Disable Ctrl", self.disable_all),
            ("Engage Rotors", self.engage_all_rotors),
            ("Disengage Rotors", self.disengage_all_rotors),
        ]:
            ttk.Button(row3, text=text, command=cmd).pack(side="left", padx=2)

        row4 = ttk.Frame(frame)
        row4.pack(fill="x", pady=2)
        ttk.Button(row4, text="Forward", command=self.set_forward).pack(side="left", padx=2)
        ttk.Button(row4, text="Reverse", command=self.set_reverse).pack(side="left", padx=2)
        ttk.Button(row4, text="Loop Once", command=self.set_loop_once).pack(side="left", padx=2)
        ttk.Button(row4, text="Loop Repeat", command=self.set_loop_repeat).pack(side="left", padx=2)
        ttk.Button(row4, text="Loop PingPong", command=self.set_loop_pingpong).pack(side="left", padx=2)
        ttk.Button(row4, text="Loop Once-Restart", command=self.set_loop_once_restart).pack(side="left", padx=2)

    def _build_per_motor_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Per-Motor RPM Tests", padding=8)
        frame.pack(fill="x", pady=4)
        for key in _KEYS:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{key} RPM", width=8).pack(side="left")
            ttk.Entry(row, textvariable=self.per_key_rpm_vars[key], width=10).pack(side="left", padx=4)
            ttk.Button(row, text="Apply", command=lambda k=key: self.apply_single_rpm(k)).pack(side="left", padx=2)
            ttk.Button(row, text="Read", command=lambda k=key: self.read_single(k)).pack(side="left", padx=2)

    def _build_selected_detail_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Selected Binding Detail", padding=8)
        frame.pack(fill="both", expand=True, pady=4)

        info = ttk.Frame(frame)
        info.pack(fill="x", pady=(0, 8))
        ttk.Label(info, text="Selected:").grid(row=0, column=0, sticky="w")
        ttk.Label(info, textvariable=self.selected_key_var).grid(row=0, column=1, sticky="w")
        ttk.Label(info, text="Controller Tag:").grid(row=1, column=0, sticky="w")
        ttk.Label(info, textvariable=self.selected_tag_var).grid(row=1, column=1, sticky="w")
        ttk.Label(info, text="Rotor Tag:").grid(row=2, column=0, sticky="w")
        ttk.Label(info, textvariable=self.selected_rotor_tag_var).grid(row=2, column=1, sticky="w")

        self.detail_text = scrolledtext.ScrolledText(frame, height=20, wrap=tk.WORD)
        self.detail_text.pack(fill="both", expand=True)

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Event Log", padding=8)
        frame.pack(fill="both", expand=True, pady=4)
        self.log_text = scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _safe_call(self, label: str, func) -> None:
        try:
            func()
            self.status_var.set(f"OK: {label}")
            self.log(label)
            self.refresh_view()
        except Exception as exc:
            self.status_var.set(f"ERR: {exc}")
            self.log(f"ERROR during {label}: {exc}")
            messagebox.showerror("KAL Rotor Test", f"{label}\n\n{exc}")

    def connect(self) -> None:
        self._safe_call("Connected to kRPC", lambda: self.rig.connect())

    def bind(self) -> None:
        self._safe_call("Bound controller and rotor tags", lambda: self.rig.bind())

    def disconnect(self) -> None:
        try:
            self.rig.disconnect()
            self.status_var.set("Disconnected")
            self.vessel_var.set("Vessel: -")
            self.log("Disconnected")
            self.refresh_view()
        except Exception as exc:
            messagebox.showerror("KAL Rotor Test", str(exc))

    def initialize_defaults(self) -> None:
        self._safe_call(
            "Initialized defaults",
            lambda: self.rig.initialize_defaults(
                torque_limit=float(self.torque_var.get()),
                play_speed_percent=float(self.play_speed_var.get()),
                controller_enabled=True,
                play_sequence=True,
                direction_forward=True,
                zero_play_position=True,
                motor_engaged=True,
                unlocked=True,
            ),
        )

    def apply_all_rpm(self) -> None:
        self._safe_call(
            f"Applied all RPM = {self.global_rpm_var.get()}",
            lambda: self.rig.set_all_rpm(float(self.global_rpm_var.get())),
        )

    def apply_single_rpm(self, key: str) -> None:
        self._safe_call(
            f"Applied {key} RPM = {self.per_key_rpm_vars[key].get()}",
            lambda: self.rig.set_rpm(key, float(self.per_key_rpm_vars[key].get())),
        )

    def read_single(self, key: str) -> None:
        def _read() -> None:
            snap = self.rig.controller_snapshot(key)
            rot = self.rig.rotor_snapshot(key)
            self.log(
                f"{key}: cmd={snap.play_position:.1f}, actual={rot.current_rpm:.1f}, torque={rot.torque_limit:.1f}, enabled={snap.enabled}, engaged={rot.motor_engaged}"
            )
            self.selected_key_var.set(key)
            self._update_selected_detail()

        self._safe_call(f"Read snapshot for {key}", _read)

    def zero_all(self) -> None:
        self._safe_call("Zeroed all play positions", self.rig.zero_all_positions)

    def emergency_stop(self) -> None:
        self._safe_call("Emergency stop", self.rig.emergency_stop)

    def set_all_torque(self) -> None:
        self._safe_call(
            f"Set all torque = {self.torque_var.get()}",
            lambda: self.rig.set_all_torque_limit(float(self.torque_var.get())),
        )

    def set_all_play_speed(self) -> None:
        self._safe_call(
            f"Set all play speed = {self.play_speed_var.get()}",
            lambda: self.rig.set_all_play_speed_percent(float(self.play_speed_var.get())),
        )

    def play_all(self) -> None:
        self._safe_call("Play all sequences", self.rig.play_all)

    def stop_all(self) -> None:
        self._safe_call("Stop all sequences", self.rig.stop_all)

    def enable_all(self) -> None:
        self._safe_call("Enabled all controllers", self.rig.enable_all_controllers)

    def disable_all(self) -> None:
        self._safe_call("Disabled all controllers", self.rig.disable_all_controllers)

    def engage_all_rotors(self) -> None:
        self._safe_call("Engaged all rotors", self.rig.engage_all_rotors)

    def disengage_all_rotors(self) -> None:
        self._safe_call("Disengaged all rotors", self.rig.disengage_all_rotors)

    def set_forward(self) -> None:
        self._safe_call("Set all forward", self.rig.set_all_direction_forward)

    def set_reverse(self) -> None:
        self._safe_call("Set all reverse", self.rig.set_all_direction_reverse)

    def set_loop_once(self) -> None:
        self._safe_call("Set loop once", self.rig.set_all_loop_once)

    def set_loop_repeat(self) -> None:
        self._safe_call("Set loop repeat", self.rig.set_all_loop_repeat)

    def set_loop_pingpong(self) -> None:
        self._safe_call("Set loop pingpong", self.rig.set_all_loop_pingpong)

    def set_loop_once_restart(self) -> None:
        self._safe_call("Set loop once-restart", self.rig.set_all_loop_once_restart)

    def refresh_view(self) -> None:
        snap = self.rig.snapshot()
        if not snap.connected:
            self.vessel_var.set("Vessel: -")
            for key in _KEYS:
                for var_dict in (
                    self.per_key_cmd_vars,
                    self.per_key_actual_vars,
                    self.per_key_torque_vars,
                    self.per_key_enabled_vars,
                    self.per_key_engaged_vars,
                    self.per_key_loop_vars,
                    self.per_key_direction_vars,
                ):
                    var_dict[key].set("-")
            self._update_selected_detail()
            return

        self.vessel_var.set(f"Vessel: {snap.vessel_name}")
        for key in _KEYS:
            cs = snap.controllers.get(key)
            rs = snap.rotors.get(key)
            if cs is not None:
                self.per_key_cmd_vars[key].set(f"{cs.play_position:.1f}")
                self.per_key_enabled_vars[key].set("On" if cs.enabled else "Off")
                self.per_key_loop_vars[key].set(cs.loop_mode_raw)
                self.per_key_direction_vars[key].set(cs.play_direction_raw)
            if rs is not None:
                self.per_key_actual_vars[key].set(f"{rs.current_rpm:.1f}")
                self.per_key_torque_vars[key].set(f"{rs.torque_limit:.1f}")
                self.per_key_engaged_vars[key].set("On" if rs.motor_engaged else "Off")
        self._update_selected_detail()

    def _update_selected_detail(self) -> None:
        key = self.selected_key_var.get()
        snap = self.rig.snapshot()
        self.detail_text.delete("1.0", tk.END)
        if key not in _KEYS or not snap.connected:
            self.selected_tag_var.set("-")
            self.selected_rotor_tag_var.set("-")
            self.detail_text.insert(tk.END, "Not connected / not bound.")
            return

        cs = snap.controllers.get(key)
        rs = snap.rotors.get(key)
        self.selected_tag_var.set(cs.tag if cs else "-")
        self.selected_rotor_tag_var.set(rs.tag if rs else "-")

        if cs is not None:
            self.detail_text.insert(tk.END, f"Controller {key}\n")
            self.detail_text.insert(tk.END, f"  tag: {cs.tag}\n")
            self.detail_text.insert(tk.END, f"  sequence: {cs.sequence}\n")
            self.detail_text.insert(tk.END, f"  play_position: {cs.play_position:.2f}\n")
            self.detail_text.insert(tk.END, f"  play_speed_percent: {cs.play_speed_percent:.2f}\n")
            self.detail_text.insert(tk.END, f"  enabled: {cs.enabled}\n")
            self.detail_text.insert(tk.END, f"  priority: {cs.controller_priority}\n")
            self.detail_text.insert(tk.END, f"  loop_mode_raw: {cs.loop_mode_raw}\n")
            self.detail_text.insert(tk.END, f"  play_direction_raw: {cs.play_direction_raw}\n")
            self.detail_text.insert(tk.END, "  fields:\n")
            for k, v in cs.fields.items():
                self.detail_text.insert(tk.END, f"    {k}: {v}\n")
            self.detail_text.insert(tk.END, "  actions:\n")
            for action in cs.actions:
                self.detail_text.insert(tk.END, f"    - {action}\n")

        if rs is not None:
            self.detail_text.insert(tk.END, "\nRotor\n")
            self.detail_text.insert(tk.END, f"  tag: {rs.tag}\n")
            self.detail_text.insert(tk.END, f"  current_rpm: {rs.current_rpm:.2f}\n")
            self.detail_text.insert(tk.END, f"  target_rpm: {rs.target_rpm}\n")
            self.detail_text.insert(tk.END, f"  torque_limit: {rs.torque_limit:.2f}\n")
            self.detail_text.insert(tk.END, f"  motor_engaged: {rs.motor_engaged}\n")
            self.detail_text.insert(tk.END, f"  locked: {rs.locked}\n")

    def _schedule_refresh(self) -> None:
        if self.auto_refresh_var.get():
            try:
                self.refresh_view()
            except Exception as exc:
                self.status_var.set(f"ERR: {exc}")
        self.root.after(self.refresh_ms, self._schedule_refresh)

    def on_close(self) -> None:
        try:
            self.rig.disconnect()
        finally:
            self.root.destroy()
