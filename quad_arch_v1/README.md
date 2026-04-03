# quad_arch_v1

`quad_arch_v1` is a small experimental architecture for separating telemetry input, telemetry processing, state storage, user intent, controller interfaces, actuator output, and GUI responsibilities in the kRPC/KSP quadcopter project.

## Architecture overview

Read path:

`telemetry_get -> telemetry_processor -> state_store -> gui`

Write path:

`gui -> intent_store -> controller_stub -> actuator_set`

`app_runtime.py` coordinates both paths without letting Tkinter talk directly to kRPC streams or actuator outputs.

## Module responsibilities

- `models.py`: shared dataclasses and type aliases for raw telemetry, processed state, pilot intent, and actuator commands.
- `telemetry_get.py`: kRPC boundary adapter. Owns the connection, reference frames, and raw stream reads only.
- `telemetry_processor.py`: centralized frame conversion and derived-state math, including `RFD -> FRD`, `UNE -> NED`, Euler-rate estimation, and `dt`.
- `state_store.py`: single source of truth for the latest processed telemetry snapshot.
- `intent_store.py`: storage for the latest UI-submitted pilot intent, initialized to a safe neutral default.
- `controller_interfaces.py`: clean extension points for future controllers, coordinators, and optional mixers.
- `controller_stub.py`: safe placeholder controller behavior for `manual`, `stabilize`, and `altitude_hold`.
- `actuator_set.py`: actuator sink boundary with a safe `NullActuatorSink` and a non-implemented kRPC output skeleton.
- `app_runtime.py`: orchestrates telemetry ticks, control ticks, state access, and intent updates.
- `gui.py`: Tkinter GUI that only reads processed state and writes pilot intent.
- `main.py`: application entry point.

## What is implemented

- Self-contained package layout under `quad_arch_v1/`
- Known-good telemetry fields from the current prototype
- Corrected hybrid-frame body-rate read path at the telemetry boundary
- Centralized coordinate conversion and display-oriented Euler-rate derivation
- Safe stores and runtime coordinator
- Tkinter GUI with telemetry panel, intent panel, and reserved 3D visualization area

## What is intentionally left as placeholder

- Real control laws
- Mixer logic
- Real kRPC actuator writes
- Full 3D rendering
- Separate telemetry/control/UI threads

## How to run

From the project root:

```powershell
python -m quad_arch_v1.main
```

If `krpc` is not installed locally, the GUI can still import, but connecting telemetry will fail until the package is available.

## Recommended next steps

1. Replace `StubController` with mode-specific controllers behind `controller_interfaces.py`.
2. Add a dedicated mixer stage and explicit actuator semantics for the target vehicle.
3. Move runtime ticks onto independent schedulers once control-loop timing requirements are clear.
4. Replace the visualization placeholder with a processed-state-driven vector view.
