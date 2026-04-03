# KAL + Rotor Test Harness

Small standalone test harness for a KSP craft that uses:
- 4 tagged `KAL-1000 Controller` parts
- 4 tagged robotic rotors

## Expected tags
Controllers:
- `ControllerFL`
- `ControllerFR`
- `ControllerRL`
- `ControllerRR`

Rotors:
- `rotorFL`
- `rotorFR`
- `rotorRL`
- `rotorRR`

## Files
- `kal_rotor_api.py` : set/get wrapper layer with many useful calls
- `kal_rotor_gui.py` : Tkinter GUI for testing
- `main.py` : app entry point

## What the API covers
### Controller-side useful set calls
- connect / disconnect / bind
- set play position
- set play speed
- enable / disable
- play / stop / toggle
- forward / reverse
- loop once / repeat / pingpong / once-restart
- zero all / emergency stop

### Controller-side useful get calls
- full raw field dump
- raw action list
- play position
- play speed
- enabled state
- loop mode raw value
- play direction raw value
- controller priority

### Rotor-side useful set calls
- engage / disengage motor
- torque limit
- lock / unlock rotor
- optional direct target_rpm path (kept separate from the KAL path)

### Rotor-side useful get calls
- current rpm
- target rpm (if available)
- torque limit
- motor engaged
- locked

## Run
```bash
pip install krpc
python main.py
```

## Suggested use
1. Start KSP and the kRPC server.
2. Open this folder.
3. Run `python main.py`.
4. Press:
   - `Connect`
   - `Bind Tags`
   - `Init Defaults`
5. Use:
   - `Apply All RPM`
   - individual `Apply`
   - `Play/Stop`
   - `Forward/Reverse`
   - `Loop` buttons
   - torque and play-speed controls
6. Watch commanded RPM vs actual rotor RPM in the live overview.

## Important note
This harness treats:
- KAL controllers as the command path
- rotor objects as initialization + feedback path

So the normal test path is:
- write controller `Play Position`
- read rotor `current_rpm`

Avoid mixing KAL control and direct rotor `target_rpm` in the same test unless that is intentional.
