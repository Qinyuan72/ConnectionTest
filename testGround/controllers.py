import time

import krpc

CTRL_TAGS = {
    "FL": "ControllerFL",
    "FR": "ControllerFR",
    "RL": "ControllerRL",
    "RR": "ControllerRR",
}

ROTOR_TAGS = {
    "FL": "rotorFL",
    "FR": "rotorFR",
    "RL": "rotorRL",
    "RR": "rotorRR",
}


def get_kal_module(vessel, tag: str):
    part = vessel.parts.with_tag(tag)[0]
    return next(m for m in part.modules if m.name == "ModuleRoboticController")


def get_rotor(vessel, tag: str):
    part = vessel.parts.with_tag(tag)[0]
    rotor = part.robotic_rotor
    if rotor is None:
        raise RuntimeError(f"Part with tag {tag} is not a robotic rotor")
    return rotor


conn = krpc.connect(name="KAL + Rotor Init")
vessel = conn.space_center.active_vessel

controllers = {k: get_kal_module(vessel, tag) for k, tag in CTRL_TAGS.items()}
rotors = {k: get_rotor(vessel, tag) for k, tag in ROTOR_TAGS.items()}

# ---- Rotor init ----
for key, rotor in rotors.items():
    rotor.motor_engaged = True
    rotor.torque_limit = 100.0
    rotor.locked = False
    print(f"{key}: torque={rotor.torque_limit}, engaged={rotor.motor_engaged}, rpm={rotor.current_rpm}")

# ---- KAL init ----
for key, mod in controllers.items():
    for cmd in [100.0, 200.0, 300.0, 460.0, 0.0]:
        print("Setting rpm cmd =", cmd)
        mod.set_field_float("Play Position", cmd)
        time.sleep(1)
        print(f"{key}:  Tested")
print(f"{key}: KAL initialized")