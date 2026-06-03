# User Guide

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/main.py
```

## Controls

| Function | Key |
| --- | --- |
| Pitch down / up | Down / Up arrow |
| Roll right / left | Right / Left arrow |
| Rudder right / left | X / Z |
| Throttle up / down | = / - |
| Engage HDG mode | H |
| Engage LNAV mode | L |
| Engage VS mode | V |
| Engage ALT hold | A |
| Autopilot off | O |
| Advance checklist | Space |
| Toggle master switch | M |
| Toggle avionics switch | N |
| Cycle magnetos (OFF→R→L→BOTH) | R |
| Engage starter | S |
| Mixture richer / leaner | . / , |
| Toggle carb heat | C |

## Usage Notes

- The simulator starts with a simple IFR route for the SBGR ILS 10R.
- The simulator now starts in a cold-and-dark style cockpit state (master OFF, avionics OFF, magnetos OFF, throttle idle).
- The moving map shows the active waypoint and leg.
- The HUD shows active autopilot modes, next waypoint, and ETE.
- ATC scenario messages appear along the bottom panel.
- Checklist progress is displayed on the right side of the message strip.

## Startup and run-up flow (Phase 1 C152 cockpit)

1. Press `M` to switch master ON.
2. Set mixture rich with `.` (or lean with `,` as needed).
3. Cycle magnetos with `R` until `BOTH`.
4. Press `S` to engage starter.
5. Turn avionics ON with `N`.
6. Use throttle (`=` / `-`) and perform run-up checks while monitoring RPM, oil pressure, oil temperature, vacuum, and bus voltage indications.
