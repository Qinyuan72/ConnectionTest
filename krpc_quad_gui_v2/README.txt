Requirements:
1. KSP running
2. kRPC server mod running in KSP
3. Python package installed: pip install krpc

Run:
python main.py

Files:
- attitude_state.py : singleton-like attitude/telemetry state + coordinate conversion
- krpc_facade.py    : wraps kRPC connection, streams, reference frame plumbing
- gui.py            : tkinter desktop telemetry panel with the friendlier grouped dashboard layout
- main.py           : program entry point

Notes:
- GUI now follows the user's preferred two-column grouped layout.
- Reconnect no longer spawns duplicate tkinter update loops.
- Euler angle rates are still display/analysis values, not guaranteed controller-ready states.
