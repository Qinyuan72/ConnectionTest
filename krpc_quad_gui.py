import math
import tkinter as tk
from tkinter import ttk
import krpc


# -----------------------------
# 坐标转换
# -----------------------------
def rfd_to_frd(v):
    # kRPC vessel.reference_frame: x=Right, y=Forward, z=Down
    x_r, y_f, z_d = v
    return (y_f, x_r, z_d)


def une_to_ned(v):
    # kRPC surface_reference_frame: x=Up, y=North, z=East
    x_u, y_n, z_e = v
    return (y_n, z_e, -x_u)


def fmt3(v, digits=3):
    return f"({v[0]: .{digits}f}, {v[1]: .{digits}f}, {v[2]: .{digits}f})"


def fmt4(q, digits=4):
    return f"({q[0]: .{digits}f}, {q[1]: .{digits}f}, {q[2]: .{digits}f}, {q[3]: .{digits}f})"


# -----------------------------
# 主 GUI
# -----------------------------
class KRPCQuadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("kRPC Quadcopter Telemetry")
        self.root.geometry("920x620")
        self.root.minsize(820, 540)

        self.conn = None
        self.vessel = None
        self.body = None
        self.streams = []
        self.connected = False
        self.update_ms = 100

        self._build_ui()
        self._connect()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)

        # 顶部控制区
        top = ttk.Frame(container)
        top.pack(fill="x", pady=(0, 8))

        self.status_var = tk.StringVar(value="Status: Connecting...")
        self.vessel_var = tk.StringVar(value="Vessel: -")
        self.body_var = tk.StringVar(value="Body: -")

        ttk.Label(top, textvariable=self.status_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.vessel_var).pack(side="left", padx=(0, 16))
        ttk.Label(top, textvariable=self.body_var).pack(side="left", padx=(0, 16))

        ttk.Button(top, text="Reconnect", command=self.reconnect).pack(side="right")

        # 主体左右两列
        main = ttk.Frame(container)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # 变量
        self.vars = {}
        keys = [
            "lat", "lon", "mean_alt", "surf_alt",
            "pitch", "heading", "roll",
            "dir_une", "dir_ned",
            "quat_surface",
            "vel_local_une", "vel_local_ned",
            "speed_surface", "hspeed_surface", "vspeed_surface",
            "omega_rfd", "omega_frd",
            "situation", "mass", "thrust", "avail_thrust"
        ]
        for k in keys:
            self.vars[k] = tk.StringVar(value="-")

        # 左列
        self._make_group(
            left, "Basic / Flight Info",
            [
                ("Situation", "situation"),
                ("Latitude", "lat"),
                ("Longitude", "lon"),
                ("Mean Altitude (m)", "mean_alt"),
                ("Surface Altitude (m)", "surf_alt"),
                ("Mass (kg)", "mass"),
                ("Current Thrust (N)", "thrust"),
                ("Available Thrust (N)", "avail_thrust"),
            ]
        ).pack(fill="x", pady=4)

        self._make_group(
            left, "Attitude",
            [
                ("Pitch (deg)", "pitch"),
                ("Heading (deg)", "heading"),
                ("Roll (deg)", "roll"),
                ("Direction in surface RF [UNE]", "dir_une"),
                ("Direction converted [NED]", "dir_ned"),
                ("Quaternion in surface RF", "quat_surface"),
            ]
        ).pack(fill="x", pady=4)

        # 右列
        self._make_group(
            right, "Velocity",
            [
                ("Local surface velocity [UNE]", "vel_local_une"),
                ("Local surface velocity [NED]", "vel_local_ned"),
                ("Surface Speed (m/s)", "speed_surface"),
                ("Horizontal Speed (m/s)", "hspeed_surface"),
                ("Vertical Speed (m/s)", "vspeed_surface"),
            ]
        ).pack(fill="x", pady=4)

        self._make_group(
            right, "Angular Velocity",
            [
                ("Body rate raw [RFD] (rad/s)", "omega_rfd"),
                ("Body rate converted [FRD] (rad/s)", "omega_frd"),
            ]
        ).pack(fill="x", pady=4)

        note = ttk.Label(
            container,
            text=(
                "坐标说明：\n"
                "  Body raw = RFD (Right, Forward, Down)\n"
                "  Surface raw = UNE (Up, North, East)\n"
                "  Converted body = FRD (Forward, Right, Down)\n"
                "  Converted local = NED (North, East, Down)"
            ),
            justify="left"
        )
        note.pack(fill="x", pady=(8, 0))

    def _make_group(self, parent, title, rows):
        labelframe = ttk.LabelFrame(parent, text=title, padding=10)
        for i, (label_text, key) in enumerate(rows):
            ttk.Label(labelframe, text=label_text).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=4)
            ttk.Label(
                labelframe,
                textvariable=self.vars[key],
                font=("Consolas", 10)
            ).grid(row=i, column=1, sticky="w", pady=4)
        return labelframe

    def _connect(self):
        try:
            self.conn = krpc.connect(name="Quad Telemetry GUI")
            sc = self.conn.space_center
            self.vessel = sc.active_vessel
            self.body = self.vessel.orbit.body

            vessel_rf = self.vessel.reference_frame
            surface_rf = self.vessel.surface_reference_frame
            body_rf = self.body.reference_frame

            # 用 hybrid frame 读取“表面速度向量，但坐标轴按本地 surface RF 排”
            local_surface_vel_rf = self.conn.space_center.ReferenceFrame.create_hybrid(
                position=body_rf,
                rotation=surface_rf
            )

            # Flight objects
            flight_default = self.vessel.flight()  # pitch/heading/roll、经纬高可直接读
            flight_surface_speed = self.vessel.flight(body_rf)
            flight_local_vec = self.vessel.flight(local_surface_vel_rf)

            # 保存对象，避免被 GC 或后续用不到
            self.flight_default = flight_default
            self.flight_surface_speed = flight_surface_speed
            self.flight_local_vec = flight_local_vec
            self.vessel_rf = vessel_rf
            self.surface_rf = surface_rf
            self.body_rf = body_rf
            self.local_surface_vel_rf = local_surface_vel_rf

            # 建 stream
            self.streams = [
                ("lat", self.conn.add_stream(getattr, flight_default, "latitude")),
                ("lon", self.conn.add_stream(getattr, flight_default, "longitude")),
                ("mean_alt", self.conn.add_stream(getattr, flight_default, "mean_altitude")),
                ("surf_alt", self.conn.add_stream(getattr, flight_default, "surface_altitude")),

                ("pitch", self.conn.add_stream(getattr, flight_default, "pitch")),
                ("heading", self.conn.add_stream(getattr, flight_default, "heading")),
                ("roll", self.conn.add_stream(getattr, flight_default, "roll")),

                ("dir_une_raw", self.conn.add_stream(self.vessel.direction, surface_rf)),
                ("quat_surface_raw", self.conn.add_stream(self.vessel.rotation, surface_rf)),

                ("vel_local_une_raw", self.conn.add_stream(getattr, flight_local_vec, "velocity")),
                ("speed_surface", self.conn.add_stream(getattr, flight_surface_speed, "speed")),
                ("hspeed_surface", self.conn.add_stream(getattr, flight_surface_speed, "horizontal_speed")),
                ("vspeed_surface", self.conn.add_stream(getattr, flight_surface_speed, "vertical_speed")),

                ("omega_rfd_raw", self.conn.add_stream(self.vessel.angular_velocity, vessel_rf)),

                ("mass", self.conn.add_stream(getattr, self.vessel, "mass")),
                ("thrust", self.conn.add_stream(getattr, self.vessel, "thrust")),
                ("avail_thrust", self.conn.add_stream(getattr, self.vessel, "available_thrust")),
                ("situation", self.conn.add_stream(getattr, self.vessel, "situation")),
            ]

            self.stream_map = dict(self.streams)

            self.connected = True
            self.status_var.set("Status: Connected")
            self.vessel_var.set(f"Vessel: {self.vessel.name}")
            self.body_var.set(f"Body: {self.body.name}")

            self._update_loop()

        except Exception as e:
            self.connected = False
            self.status_var.set(f"Status: Connection failed - {e}")

    def _safe_call(self, name):
        return self.stream_map[name]()

    def _update_loop(self):
        if not self.connected:
            return

        try:
            lat = self._safe_call("lat")
            lon = self._safe_call("lon")
            mean_alt = self._safe_call("mean_alt")
            surf_alt = self._safe_call("surf_alt")

            pitch = self._safe_call("pitch")
            heading = self._safe_call("heading")
            roll = self._safe_call("roll")

            dir_une = self._safe_call("dir_une_raw")
            dir_ned = une_to_ned(dir_une)

            quat_surface = self._safe_call("quat_surface_raw")

            vel_local_une = self._safe_call("vel_local_une_raw")
            vel_local_ned = une_to_ned(vel_local_une)

            speed_surface = self._safe_call("speed_surface")
            hspeed_surface = self._safe_call("hspeed_surface")
            vspeed_surface = self._safe_call("vspeed_surface")

            omega_rfd = self._safe_call("omega_rfd_raw")
            omega_frd = rfd_to_frd(omega_rfd)

            mass = self._safe_call("mass")
            thrust = self._safe_call("thrust")
            avail_thrust = self._safe_call("avail_thrust")
            situation = self._safe_call("situation")

            self.vars["lat"].set(f"{lat:.6f}")
            self.vars["lon"].set(f"{lon:.6f}")
            self.vars["mean_alt"].set(f"{mean_alt:.3f}")
            self.vars["surf_alt"].set(f"{surf_alt:.3f}")

            self.vars["pitch"].set(f"{pitch:.3f}")
            self.vars["heading"].set(f"{heading:.3f}")
            self.vars["roll"].set(f"{roll:.3f}")

            self.vars["dir_une"].set(fmt3(dir_une))
            self.vars["dir_ned"].set(fmt3(dir_ned))
            self.vars["quat_surface"].set(fmt4(quat_surface))

            self.vars["vel_local_une"].set(fmt3(vel_local_une))
            self.vars["vel_local_ned"].set(fmt3(vel_local_ned))

            self.vars["speed_surface"].set(f"{speed_surface:.3f}")
            self.vars["hspeed_surface"].set(f"{hspeed_surface:.3f}")
            self.vars["vspeed_surface"].set(f"{vspeed_surface:.3f}")

            self.vars["omega_rfd"].set(fmt3(omega_rfd, digits=4))
            self.vars["omega_frd"].set(fmt3(omega_frd, digits=4))

            self.vars["mass"].set(f"{mass:.3f}")
            self.vars["thrust"].set(f"{thrust:.3f}")
            self.vars["avail_thrust"].set(f"{avail_thrust:.3f}")
            self.vars["situation"].set(str(situation))

            self.status_var.set("Status: Connected / Updating")

        except Exception as e:
            self.status_var.set(f"Status: Update error - {e}")

        self.root.after(self.update_ms, self._update_loop)

    def reconnect(self):
        self._cleanup()
        self.status_var.set("Status: Reconnecting...")
        self._connect()

    def _cleanup(self):
        for _, s in getattr(self, "streams", []):
            try:
                s.remove()
            except Exception:
                pass
        self.streams = []

        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

        self.connected = False

    def on_close(self):
        self._cleanup()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = KRPCQuadGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()