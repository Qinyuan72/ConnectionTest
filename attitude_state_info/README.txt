Requirements:
1. KSP running
2. kRPC server mod running in KSP
3. Python package installed: pip install krpc

Run:
python main.py

Files:
- attitude_state.py : singleton-like attitude/telemetry state + coordinate conversion
- krpc_facade.py    : wraps kRPC connection, streams, reference frame plumbing
- gui.py            : tkinter desktop telemetry panel
- main.py           : program entry point
