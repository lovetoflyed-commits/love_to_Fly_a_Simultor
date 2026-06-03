# Architecture

The simulator is organized into small subsystems under `src/`.

- `models/` contains immutable flight and navigation data such as aircraft, position, attitude, and flight plans.
- `fdm/` contains atmosphere, aerodynamics, engine, and the simplified 6-DOF integrator.
- `instruments/` renders a dark-cockpit panel entirely with Pygame drawing primitives.
- `navigation/` provides VOR/ILS, GPS, autopilot, and procedures.
- `environment/` models weather, terrain, and airports.
- `scenarios/` provides failures, ATC messaging, and scripted training exercises.
- `chairflight/` provides checklists, a logbook, and procedure viewing.
- `ui/` composes the instruments and HUD into the 1280x720 cockpit layout.

`src/main.py` initializes all systems, runs the real-time update loop, aggregates state into a shared dictionary, and renders the cockpit each frame.
