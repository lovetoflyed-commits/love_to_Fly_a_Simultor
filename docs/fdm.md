# Flight Dynamics Model

The flight dynamics model is intentionally lightweight so it can run in a training-oriented desktop simulator without external assets.

## Atmosphere

`ISAAtmosphere` implements International Standard Atmosphere equations:

- Troposphere lapse rate of `-0.0065 K/m` to 11 km
- Isothermal layer above 11 km with exponential pressure decay
- Density from the ideal gas law
- Speed of sound from `sqrt(gamma * R * T)`

## Forces

Each update step computes:

- **Lift**: `0.5 * rho * V^2 * CL * S`
- **Drag**: `0.5 * rho * V^2 * CD * S`
- **Engine thrust**: max thrust scaled by throttle and density ratio
- **Weight**: `m * g`

The aerodynamic model uses a linear lift curve up to 16 degrees angle of attack and a parabolic drag polar:

`CD = CD0 + CL^2 / (pi * AR * e)`

## Integration Assumptions

The solver uses a simplified body-axis approach:

- Forward speed is integrated from net longitudinal force.
- Vertical speed is integrated from excess lift over weight.
- Roll, pitch, and yaw respond to control deflections through damped first-order rates.
- Heading drives flat-earth latitude and longitude updates.
- Wind and turbulence are applied as perturbations from the weather model.

This is not a certified or research-grade model, but it is stable, testable, and appropriate for IFR chair-flying and scan practice.
