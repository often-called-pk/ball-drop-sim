# Ball Drop Simulation

A one-dimensional simulation of a spherical ball falling through a fluid under gravity and aerodynamic drag. The same model serves a tennis ball and a satellite re-entry, so the vocabulary stays neutral about scale.

## Language

### The ball and its state

**Ball**:
The spherical body being simulated, defined by its mass and radius.
_Avoid_: object, particle, projectile

**Height**:
The ball's distance above the ground along the vertical axis, positive upward. Written x.
_Avoid_: altitude, position

**Velocity**:
The rate of change of height, positive upward. A falling ball has negative velocity. Written v.
_Avoid_: speed (speed is the magnitude only)

**Acceleration**:
The rate of change of velocity, from the net force divided by the ball's mass. Written a.

**State**:
The height and velocity of the ball at one instant.

### Forces

**Weight force**:
The gravitational force on the ball, acting toward the ground. Written FW.
_Avoid_: gravity force, weight

**Gravity model**:
The rule that gives the weight force for a given height: a constant field, or the Newtonian law around a planet.
_Avoid_: gravity mode, g-model

**Planet**:
The body whose gravity acts on the ball in the Newtonian model, defined by its mass M and radius R.
_Avoid_: Earth, body

**Drag force**:
The aerodynamic force opposing the ball's motion. Written FD.
_Avoid_: air resistance, friction

**Drag coefficient**:
The dimensionless factor CD in the drag law.

**Fluid density**:
The density of the medium around the ball, written ρ, constant for a run.
_Avoid_: air density (the medium is not always air)

### The ground

**Ground**:
The surface at height zero. In the Newtonian model it lies at distance R from the planet's centre.
_Avoid_: floor, surface

**Impact**:
The moment the ball's height first reaches the ground. A run ends at impact.
_Avoid_: landing, collision, touchdown

### Running the simulation

**Run**:
One simulation from the initial state to impact or to the finish time, with one set of parameters.
_Avoid_: simulation (that word names the whole program), case, scenario

**Parameters**:
The full set of user-chosen values that define a run: ball, fluid, gravity model, initial state, time settings.
_Avoid_: config, settings, inputs

**Preset**:
A named, saved set of parameters, for example "tennis ball".
_Avoid_: profile, template

**Integrator**:
The numerical scheme that advances the state by one time step.
_Avoid_: solver, stepper

**Time step**:
The fixed interval between two successive states. Written dt.

**Finish time**:
The latest time a run may reach when impact does not come first.
_Avoid_: end time, duration

**Trajectory**:
The time history of height, velocity and acceleration produced by a run, with the impact time when there is one.
_Avoid_: results, output, log

### The animation extra

**Terminal velocity**:
The speed at which the drag force equals the weight force, so the net force is zero. It depends on the height when gravity varies.
_Avoid_: limiting velocity, settling velocity

**Energy lost to drag**:
The energy that the drag force removes from the ball from the start of a run to the current time. It is minus the work that the drag force does, so it is never negative.
_Avoid_: lost energy, dissipated energy, drag loss

**Numerical error**:
The start energy minus the sum of kinetic, potential and energy lost to drag. It is zero for an exact integrator.
_Avoid_: energy error, energy drift, residual
