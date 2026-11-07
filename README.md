# Ball drop simulation

## What it does

This program simulates a ball that falls in one dimension. Gravity and quadratic drag act on the ball.
The program runs from an initial height and velocity until impact or until the finish time.
It plots height, velocity and acceleration against time.
You can run it from the command line or from a small Tk window.
Two presets ship with it: a tennis ball (constant gravity) and a satellite re-entry (Newtonian gravity).

`CONTEXT.md` defines the terms in this file (run, preset, trajectory and so on).

## Quick start

One command sets up a virtual environment, installs the requirements, runs the tests and opens the GUI.

```
./start.sh          # Linux and macOS
start.bat           # Windows
python3 start.py    # any system (python start.py on Windows)
```

Options: `--no-gui` sets up and tests only. `--no-tests` skips the test run.

The script uses the interpreter inside `.venv` itself, so you do not need to activate the environment.
To work by hand later, activate it (`source .venv/bin/activate` on Linux and macOS, `.venv\Scripts\activate` on Windows) and run `python -m ballsim --gui`.

## Physics

Height x points up. Velocity v points up. A falling ball has negative v.

Drag force, with no one-half factor because the brief defines the law this way:

```
|FD| = CD * rho * v^2 * pi * r^2
FD   = -CD * rho * pi * r^2 * v * |v|     (always opposes v)
```

Weight force, with constant gravity or with Newtonian gravity:

```
FW = -m * g
FW = -G * M * m / (R + x)^2
```

Newton's second law gives the acceleration:

```
FW + FD = m * a
```

The code adds the forces and divides by the mass.
Weight is always negative (downward). Drag has the opposite sign to v.
A falling ball has negative v, so drag points up and slows the fall.

The ground is at x = 0. In the Newtonian model it lies at distance R from the planet centre.

Integrators (set with the `integrator` key in a preset or with `--integrator`):

* `simple` is the scheme from the brief. It uses one acceleration a_{i-1} for both updates:

```
v_i = v_{i-1} + a_{i-1} * dt
x_i = x_{i-1} + v_{i-1} * dt + 0.5 * a_{i-1} * dt^2
```

* `rk4` is classic fourth-order Runge-Kutta. It is more accurate at larger time steps.

A run ends at the first step that takes the height to zero or below.
The program then interpolates linearly between the two samples to find the impact time and velocity.

## Install

You need Python 3.10 or later. Only the GUI needs Tk.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `source` line is for Linux and macOS. On Windows, use `.venv\Scripts\activate` instead.

The dependencies are numpy, matplotlib and pytest.

## Run

Run all commands from this folder.

```
python -m ballsim presets/tennis_ball.json
python -m ballsim presets/tennis_ball.json presets/satellite_reentry.json
python -m ballsim presets/tennis_ball.json --integrator rk4
python -m ballsim presets/tennis_ball.json --csv out.csv --no-plot
python -m ballsim presets/tennis_ball.json presets/satellite_reentry.json --csv out.csv --no-plot
```

Each command prints one summary line per run.
A plot window opens unless you give `--no-plot`.
With two presets, the plot window overlays both runs.

Options:

* `--integrator {simple,rk4}` replaces the integrator in every preset.
* `--csv PATH` writes each trajectory to a CSV file with the columns `t,x,v,a`.
* `--no-plot` skips the plot window.
* `--gui` opens the graphical interface.

With one run, `--csv out.csv` writes `out.csv`.
With several runs, the program adds the run name to the file name.
The example above writes `out_tennis_ball.csv` and `out_satellite_re-entry.csv`.

GUI (two equivalent commands):

```
python -m ballsim --gui
python -m ballsim.gui
```

In the window, edit the parameters, load or save a preset, and press Run.
Each run adds to the plots. Clear them with Clear plots, or untick Keep previous runs.

## Optional animation (extras/)

The animation replays one run. It shows:

* The ball falling beside a height scale, with a blue drag arrow and a red weight arrow.
* Three graphs (height, velocity, acceleration) that grow as time passes.
* Gauges for drag, weight, speed and energy.
* A text readout with the current values, such as terminal velocity, energy lost to drag and numerical error.

Start it in one of two ways:

```
python -m extras.animate presets/tennis_ball.json
```

or press Animate in the GUI.

Controls:

* Pause and Resume, or press space. At the end of the run, Resume starts the run again.
* Restart, or press r.
* The speed slider has the steps x0.25, x0.5, x1, x2, x5, x10, x20, x50 and x100. The animation starts at the fastest step that still plays for about 10 s.
* The time slider moves to any moment of the run.

When the ball reaches the ground, a banner shows the impact time and velocity.

Run the tests of the extra with:

```
pytest -q extras/tests
```

The extra adds a feature without changing the run loop, the data model or the core tests.
The GUI imports it only when you press Animate.

Module map of the extra:

* `extras/quantities.py`: `Quantities`, `potential_energy` and `compute`. They find forces and energies for the animation from a trajectory. This file does not use matplotlib.
* `extras/animate.py`: the `Animator` class, helpers such as `start_speed_index` and `format_readout`, and the command line entry `main`.
* `extras/tests/`: the tests for both files. They use the Agg backend, so no window opens.

## Preset format

A preset is a flat JSON file. The keys are the field names of `Parameters` in `ballsim/parameters.py`.
Missing keys take the default values. Unknown keys raise an error.
The program checks the values and names the field that is wrong.

## Test

```
pytest -q
```

* `tests/test_forces.py` proves that drag opposes motion and that both gravity models give the expected force.
* `tests/test_integrators.py` proves that `simple_step` follows the brief formula and that `rk4_step` is exact for constant acceleration.
* `tests/test_simulation.py` proves free fall against the closed form, impact interpolation, terminal velocity and the Newtonian limit.
* `tests/test_presets.py` proves the JSON round trip, the shipped presets and the validation errors.
* `tests/test_plotting.py` proves that plotting a trajectory runs without error.
* `tests/test_cli.py` proves the printed summary and the CSV files for one and two presets.

## Module map

* `ballsim/parameters.py`: `Ball`, `State`, `Parameters`, `validate`, and the name lists `GRAVITY_MODELS` and `INTEGRATOR_NAMES`.
* `ballsim/forces.py`: `Force` and its subclasses `ConstantGravity`, `NewtonianGravity` and `QuadraticDrag`.
* `ballsim/integrators.py`: `simple_step`, `rk4_step` and the `INTEGRATORS` dictionary.
* `ballsim/simulation.py`: `make_forces`, `acceleration`, `run`, `describe` and the `Trajectory` class.
* `ballsim/presets.py`: `load_preset` and `save_preset`.
* `ballsim/plotting.py`: `make_axes` and `add_trajectory`. It uses `Figure` and not pyplot, so the GUI can embed it.
* `ballsim/__main__.py`: the command line, `write_csv` and `csv_path`.
* `ballsim/gui.py`: the Tk window.
* `start.py`: the one-command setup script. It checks Python and Tk, builds `.venv`, installs, tests and starts the GUI.
* `start.sh`: Linux and macOS wrapper that calls `python3 start.py`.
* `start.bat`: Windows wrapper that calls `start.py` through the `py` launcher or `python`.
* `presets/`: the two shipped presets.

## How to extend

New gravity model:

1. Add a `Force` subclass in `forces.py`.
2. Add one branch for it in `make_forces` in `simulation.py`.
3. Add its name to `GRAVITY_MODELS` in `parameters.py`.
4. Add the parameters it needs to `Parameters` and `validate`.

New atmosphere: write a new drag class that finds the density from a `density(x)` method.
An exponential atmosphere is one example.
Use it in `make_forces` in place of `QuadraticDrag`.

New integrator:

1. Write a function with the signature of `simple_step`.
2. Add it to the `INTEGRATORS` dictionary.
3. Add its name to `INTEGRATOR_NAMES`.

New input format:

1. Write one reader that returns `Parameters`, as `load_preset` does. A `load_csv_preset` function is one example.
2. Call it where the program loads a file: `main` in `__main__.py` and `App.load` in `gui.py`. Pick the reader by file suffix.
3. Add the new suffix to `JSON_TYPES` in `gui.py` so the file dialog shows the file.

2-D motion, about four small edits:

1. `State` holds position and velocity as numpy vectors, and each force returns a vector. Drag uses the speed `norm(v)` in place of `abs(v)`. The integrators work unchanged, they only add and scale.
2. `run` tests the height component for the ground and interpolates on it.
3. `Trajectory` and `write_csv` get one column per component.
4. `plotting` picks the components to draw.

## With more time

* Adaptive time step.
* Height-dependent fluid density.
* Mach-dependent drag coefficient.
* Property-based tests.
* GIF or MP4 export of the animation.
* A pip-installable package (build metadata in `pyproject.toml`).

## Limitations

* The fluid density is constant for a run.
* The motion is one-dimensional.
* The code does not handle R + x = 0 in the Newtonian model.
* The impact time and velocity come from linear interpolation, so they are approximate.
* Both integrators are explicit and have no step control. A time step above about 1 s gives wrong values for the tennis ball with either scheme. At very large steps rk4 is not safer than simple: at dt = 5 s it reports an upward impact. Keep the step below about 0.5 s for the tennis ball, or add an adaptive step (see With more time).
* The GUI has no automated test. Check it by hand.
