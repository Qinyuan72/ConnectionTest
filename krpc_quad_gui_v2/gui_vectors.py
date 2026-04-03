from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

from krpc_facade import KrpcFacade

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    FigureCanvasTkAgg = None
    NavigationToolbar2Tk = None
    Figure = None
    MATPLOTLIB_AVAILABLE = False


def fmt3(v, digits: int = 3) -> str:
    return f"({v[0]: .{digits}f}, {v[1]: .{digits}f}, {v[2]: .{digits}f})"


def fmt4(v, digits: int = 4) -> str:
    return f"({v[0]: .{digits}f}, {v[1]: .{digits}f}, {v[2]: .{digits}f}, {v[3]: .{digits}f})"


def vec_norm(v) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def normalize_or_zero(v):
    n = vec_norm(v)
    if n < 1e-9:
        return (0.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


class TelemetryGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("kRPC Quadcopter Telemetry + 3D Vector View")
        self.root.geometry("1320x760")
        self.root.minsize(1080, 680)

        self.facade = KrpcFacade()
        self.update_ms = 100
        self.plot_every = 2  # redraw heavy 3D view every N telemetry updates
        self._plot_counter = 0
        self._after_id: str | None = None

        self.status_var = tk.StringVar(value="Status: Connecting...")
        self.vessel_var = tk.StringVar(value="Vessel: -")
        self.body_var = tk.StringVar(value="Body: -")
        self.normalize_vectors_var = tk.BooleanVar(value=True)
        self.show_reference_axes_var = tk.BooleanVar(value=True)

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
            "dir_mag": tk.StringVar(value="-"),
            "vel_mag": tk.StringVar(value="-"),
            "omega_mag": tk.StringVar(value="-"),
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

        splitter = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        splitter.pack(fill="both", expand=True)

        left = ttk.Frame(splitter, padding=(0, 0, 6, 0))
        right = ttk.Frame(splitter, padding=(6, 0, 0, 0))
        splitter.add(left, weight=1)
        splitter.add(right, weight=2)

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
            left,
            "Velocity / Angular Velocity",
            [
                ("Local surface velocity [UNE]", "vel_local_une"),
                ("Local surface velocity [NED]", "vel_local_ned"),
                ("Surface Speed (m/s)", "speed_surface"),
                ("Horizontal Speed (m/s)", "hspeed_surface"),
                ("Vertical Speed (m/s)", "vspeed_surface"),
                ("Body rate [RFD, rel body] (rad/s)", "omega_rfd"),
                ("Body rate [FRD, rel body] (rad/s)", "omega_frd"),
            ],
        ).pack(fill="x", pady=4)

        self._make_group(
            left,
            "Vector Magnitudes",
            [
                ("Direction |NED|", "dir_mag"),
                ("Velocity |NED| (m/s)", "vel_mag"),
                ("Body rate |FRD| (rad/s)", "omega_mag"),
            ],
        ).pack(fill="x", pady=4)

        note = ttk.Label(
            left,
            text=(
                "坐标说明：\n"
                "  Body raw = RFD (Right, Forward, Down)\n"
                "  Surface raw = UNE (Up, North, East)\n"
                "  Converted body = FRD (Forward, Right, Down)\n"
                "  Converted local = NED (North, East, Down)\n"
                "  欧拉角速度仅用于显示/分析；做控制前请再核对定义。"
            ),
            justify="left",
        )
        note.pack(fill="x", pady=(8, 0))

        self._build_visualization_ui(right)

    def _build_visualization_ui(self, parent) -> None:
        control_frame = ttk.LabelFrame(parent, text="3D View Controls", padding=10)
        control_frame.pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(
            control_frame,
            text="Normalize vectors for display",
            variable=self.normalize_vectors_var,
            command=self._force_redraw,
        ).pack(side="left", padx=(0, 16))

        ttk.Checkbutton(
            control_frame,
            text="Show reference axes",
            variable=self.show_reference_axes_var,
            command=self._force_redraw,
        ).pack(side="left")

        vis_frame = ttk.LabelFrame(parent, text="3D Vector Visualization", padding=8)
        vis_frame.pack(fill="both", expand=True)

        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(
                vis_frame,
                text="Matplotlib is not installed. Install it with: pip install matplotlib",
                justify="center",
            ).pack(fill="both", expand=True, padx=20, pady=20)
            self.figure = None
            self.canvas = None
            self.ax_local = None
            self.ax_body = None
            return

        self.figure = Figure(figsize=(8.2, 5.2), dpi=100)
        self.ax_local = self.figure.add_subplot(121, projection="3d")
        self.ax_body = self.figure.add_subplot(122, projection="3d")
        self.figure.tight_layout(pad=2.0)

        self.canvas = FigureCanvasTkAgg(self.figure, master=vis_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, vis_frame, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(fill="x", pady=(6, 0))

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
            self._plot_counter = 0
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

            self.vars["dir_mag"].set(f"{vec_norm(s.direction_ned):.3f}")
            self.vars["vel_mag"].set(f"{vec_norm(s.velocity_ned_m_s):.3f}")
            self.vars["omega_mag"].set(f"{vec_norm(s.body_rates_frd_rad_s):.4f}")

            self.status_var.set("Status: Connected / Updating")

            self._plot_counter += 1
            if self._plot_counter >= self.plot_every:
                self._plot_counter = 0
                self._draw_3d_vectors(s)
        except Exception as exc:
            self.status_var.set(f"Status: Update error - {exc}")

        self._after_id = self.root.after(self.update_ms, self._update_loop)

    def _force_redraw(self) -> None:
        try:
            self._draw_3d_vectors(self.facade.get_snapshot())
        except Exception:
            pass

    def _draw_reference_axes(self, ax, axis_len: float, labels: tuple[str, str, str]) -> None:
        if not self.show_reference_axes_var.get():
            return
        ax.quiver(0, 0, 0, axis_len, 0, 0, arrow_length_ratio=0.12, linewidth=1.4, color="0.55")
        ax.quiver(0, 0, 0, 0, axis_len, 0, arrow_length_ratio=0.12, linewidth=1.4, color="0.55")
        ax.quiver(0, 0, 0, 0, 0, axis_len, arrow_length_ratio=0.12, linewidth=1.4, color="0.55")
        ax.text(axis_len * 1.08, 0, 0, labels[0], color="0.35")
        ax.text(0, axis_len * 1.08, 0, labels[1], color="0.35")
        ax.text(0, 0, axis_len * 1.08, labels[2], color="0.35")

    def _vector_for_display(self, v, *, normalized: bool):
        if normalized:
            return normalize_or_zero(v)
        return v

    def _configure_axes(self, ax, title: str, labels: tuple[str, str, str], max_extent: float) -> None:
        ax.set_title(title, pad=14)
        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])
        ax.set_zlabel(labels[2])
        ax.set_xlim(-max_extent, max_extent)
        ax.set_ylim(-max_extent, max_extent)
        ax.set_zlim(-max_extent, max_extent)
        try:
            ax.set_box_aspect((1, 1, 1))
        except Exception:
            pass
        ax.grid(True)

    def _draw_3d_vectors(self, snapshot) -> None:
        if not MATPLOTLIB_AVAILABLE or self.ax_local is None or self.ax_body is None or self.canvas is None:
            return

        normalize = self.normalize_vectors_var.get()

        self.ax_local.cla()
        self.ax_body.cla()

        direction_ned = snapshot.direction_ned
        velocity_ned = snapshot.velocity_ned_m_s
        body_rate_frd = snapshot.body_rates_frd_rad_s

        dir_draw = self._vector_for_display(direction_ned, normalized=normalize)
        vel_draw = self._vector_for_display(velocity_ned, normalized=normalize)
        body_draw = self._vector_for_display(body_rate_frd, normalized=normalize)

        local_max = max(1.2, vec_norm(dir_draw), vec_norm(vel_draw), vec_norm(direction_ned), vec_norm(velocity_ned))
        body_max = max(1.2, vec_norm(body_draw), vec_norm(body_rate_frd))

        self._configure_axes(self.ax_local, "Local NED Vectors", ("North", "East", "Down"), local_max)
        self._configure_axes(self.ax_body, "Body FRD Vectors", ("Forward", "Right", "Down"), body_max)

        self._draw_reference_axes(self.ax_local, local_max * 0.9, ("N", "E", "D"))
        self._draw_reference_axes(self.ax_body, body_max * 0.9, ("F", "R", "D"))

        self.ax_local.quiver(
            0, 0, 0,
            dir_draw[0], dir_draw[1], dir_draw[2],
            arrow_length_ratio=0.12,
            linewidth=2.2,
            color="tab:blue",
        )
        self.ax_local.quiver(
            0, 0, 0,
            vel_draw[0], vel_draw[1], vel_draw[2],
            arrow_length_ratio=0.12,
            linewidth=2.2,
            color="tab:orange",
        )
        self.ax_local.text(dir_draw[0], dir_draw[1], dir_draw[2], "Dir", color="tab:blue")
        self.ax_local.text(vel_draw[0], vel_draw[1], vel_draw[2], "Vel", color="tab:orange")

        self.ax_body.quiver(
            0, 0, 0,
            body_draw[0], body_draw[1], body_draw[2],
            arrow_length_ratio=0.12,
            linewidth=2.4,
            color="tab:green",
        )
        self.ax_body.text(body_draw[0], body_draw[1], body_draw[2], "Body rate", color="tab:green")

        self.ax_body.quiver(
            0, 0, 0,
            1.0, 0.0, 0.0,
            arrow_length_ratio=0.10,
            linewidth=1.6,
            color="tab:red",
            alpha=0.6,
        )
        self.ax_body.text(1.05, 0.0, 0.0, "Forward", color="tab:red")

        local_title_suffix = "(normalized)" if normalize else "(raw magnitude)"
        body_title_suffix = "(normalized)" if normalize else "(raw magnitude)"
        self.ax_local.set_title(f"Local NED Vectors {local_title_suffix}", pad=14)
        self.ax_body.set_title(f"Body FRD Vectors {body_title_suffix}", pad=14)

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw_idle()

    def on_close(self) -> None:
        self._cancel_update_loop()
        try:
            self.facade.close()
        finally:
            self.root.destroy()
