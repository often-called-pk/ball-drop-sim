# Ball drop simulation

This program simulates a ball that falls in one dimension under gravity and quadratic drag.
It answers the TOYOTA Racing coding challenge for a Simulation Engineer.
It needs Python 3.10 or newer, numpy and matplotlib.

![Height, velocity and acceleration of the tennis ball and the satellite re-entry presets on shared axes](docs/plot_overlay.png)

The plot overlays the two shipped presets.
On shared axes the tennis ball (100 m, about 7 s) is a flat line near zero in the height and velocity panels.
Its curve is clear only in the acceleration panel.

## Quick start

One command sets up a virtual environment, installs the requirements, runs all tests and opens the GUI.

```
./start.sh          # Linux and macOS
start.bat           # Windows
python3 start.py    # any system (python start.py on Windows)
```

Options: `--no-gui` sets up and tests only. `--no-tests` skips the test run.

If `./start.sh` reports "permission denied", your unzip tool dropped the executable bit. Run `sh start.sh` or `python3 start.py` instead.

The script uses the interpreter inside `.venv` itself, so you do not need to activate the environment.
To work by hand, run these commands once:

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

On Debian and Ubuntu, `python -m venv` can need the `python3-venv` package. The GUI needs Tk.
`requirements.txt` sets only a minimum version for pytest.

## Layout

Paths are relative to this folder.

* `ballsim/parameters.py`: `Ball`, `State`, `Parameters`, `validate`, and the name lists `GRAVITY_MODELS` and `INTEGRATOR_NAMES`.
* `ballsim/forces.py`: `Force` and its subclasses `ConstantGravity`, `NewtonianGravity` and `QuadraticDrag`.
* `ballsim/integrators.py`: `simple_step`, `rk4_step` and the `INTEGRATORS` dictionary.
* `ballsim/simulation.py`: `make_forces`, `acceleration`, `run`, `describe` and the `Trajectory` class.
* `ballsim/presets.py`: `from_dict`, `load_preset` and `save_preset`.
* `ballsim/plotting.py`: `make_axes` and `add_trajectory`. It uses `Figure` and not pyplot, so the GUI can embed it.
* `ballsim/__main__.py`: the command line, `write_csv` and `csv_path`.
* `ballsim/gui.py`: the Tk window. Its Animate button imports `extras/animate.py` when you press it.
* `extras/quantities.py`: forces and energies for the animation. It does not use matplotlib.
* `extras/animate.py`: the `Animator` class and its command line entry.
* `tests/` and `extras/tests/`: the core tests and the animation tests.
* `presets/`: the tennis ball and satellite re-entry presets.
* `start.py`, `start.sh`, `start.bat`: the one-command setup. It checks Python and Tk, builds `.venv`, installs, tests and starts the GUI.

The core answers the brief: `ballsim/`, `tests/` and `presets/`.
`extras/` is an optional animation. I added it after the core was complete.
It needed one change in the core: the Animate button in `ballsim/gui.py`.

## What the brief asks and where it is met

Test names are in `tests/` unless the path says otherwise.

| Brief requirement | Where in the code | Test that proves it |
|:--|:--|:--|
| Drag `\|FD\| = CD rho v^2 pi r^2`, opposite to motion | `forces.py`, `QuadraticDrag` | `test_forces.py::test_drag_opposes_motion`, `test_simulation.py::test_terminal_velocity` |
| Constant gravity `FW = m g` | `forces.py`, `ConstantGravity` | `test_forces.py::test_constant_gravity`, `test_simulation.py::test_free_fall_matches_closed_form` |
| Newtonian gravity `-FW = G M m / (R + x)^2` | `forces.py`, `NewtonianGravity` | `test_simulation.py::test_run_uses_chosen_gravity_model` |
| User picks the gravity model | `Parameters.gravity_model`, `make_forces`, GUI menu | `test_simulation.py::test_run_uses_chosen_gravity_model`, `test_presets.py::test_invalid_field_named` |
| `FW + FD = m a` | `simulation.py`, `acceleration` | `test_simulation.py::test_terminal_velocity`, `extras/tests/test_quantities.py::test_vectorised_forces_match_per_sample_loop` |
| Forces at time t from the current x and v, then numerical integration | `run` passes `accel(state)` to the integrator | `test_integrators.py::test_simple_step_matches_brief_formula` |
| The brief scheme, plus a built-in alternative | `integrators.py`, `simple_step` and `rk4_step` | `test_simple_step_matches_brief_formula`, `test_rk4_accurate_on_spring`, `test_simulation.py::test_rk4_more_accurate_and_both_converge` |
| Calculate x, v and a | `Trajectory`, CSV columns `t,x,v,a`, three plot panels | `test_cli.py::test_cli_prints_summary_and_csv`, `test_simulation.py::test_free_fall_matches_closed_form` |
| User varies CD, rho, r, m, g, G, M, R, initial height and velocity, finish time, time step | `Parameters` and `validate`, one preset key and one GUI entry each | `test_presets.py::test_invalid_field_named`, `test_newtonian_needs_positive_planet` |
| Model valid for x > 0, x = 0 is impact, R + x = 0 not handled | `run` stops at the first x <= 0 and interpolates to x = 0. `validate` requires a positive initial height | `test_simulation.py::test_impact_time_interpolated` |
| Tests and visualisations | `ballsim/plotting.py`, `ballsim/gui.py`, `extras/animate.py` | 60 tests in total, `test_plotting.py::test_plot_smoke`, `extras/tests/test_animate.py` |
| Easy to extend, easy to change the input format | `Force` base class, `INTEGRATORS`, `make_forces`, `from_dict` | `test_integrators.py::test_names_match_parameters`, `test_presets.py::test_round_trip`, `test_from_dict_parses_entry_texts` |
| Instructions to compile, run and test | This file, `start.py` | `test_cli.py` (the start scripts have no automated test) |
| One zip named with first and last name | `PrashantKumar.zip`, see the last section | None |

No test checks a negative G or M. `validate` rejects them, but only in the Newtonian model.

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
Weight is always negative (downward). Drag has the opposite sign to v, so it slows a fall.
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

## Run

Run all commands from this folder, with the environment active.

```
python -m ballsim presets/tennis_ball.json
python -m ballsim presets/tennis_ball.json presets/satellite_reentry.json
python -m ballsim presets/tennis_ball.json --integrator rk4
python -m ballsim presets/tennis_ball.json --csv out.csv --no-plot
python -m ballsim --gui
```

Each run prints one summary line. For the two presets, the output is:

```
tennis ball: impact at t = 7.348 s, v = -16.088 m/s, max speed 16.088 m/s
satellite re-entry: impact at t = 144.732 s, v = -1386.184 m/s, max speed 1386.184 m/s
```

A plot window opens unless you give `--no-plot`. With two presets, the window overlays both runs.

Options:

* `--integrator {simple,rk4}` replaces the integrator in every preset.
* `--no-plot` skips the plot window.
* `--csv PATH` writes each trajectory to a CSV file with the columns `t,x,v,a`. With several runs, the program adds the run name to the file name, for example `out_tennis_ball.csv`.

In the GUI window, edit the parameters, load or save a preset, and press Run.
Each run adds to the plots. Clear them with Clear plots, or untick Keep previous runs.

## Preset format

A preset is a flat JSON file. The keys are the field names of `Parameters` in `ballsim/parameters.py`.
`presets/tennis_ball.json` shows every key.
All values are in SI units: metres, kilograms, seconds.
Missing keys take the default values, which are the tennis ball values. Unknown keys raise an error.
The program checks the values and names the field that is wrong.

## Optional animation (extras/)

The animation replays one run. It shows:

* The ball falling beside a height scale, with a blue drag arrow and a red weight arrow.
* Three graphs (height, velocity, acceleration) that grow as time passes.
* A text readout with the current values.

![One animation frame of the tennis ball preset at t = 3 s](docs/animation_frame.png)

The frame shows the tennis ball at t = 3 s.
The dashed line in the velocity graph is the terminal velocity.

Start it with `python -m extras.animate presets/tennis_ball.json`, or press Animate in the GUI.
Every run plays for 10 s, whatever its length.
Pause stops the clock and Resume starts it again. At the end of the run, Resume starts the run again.
The time scrubber moves to any moment of the run.
When the run ends, a banner shows the result.

Terms in the readout:

* **Terminal velocity**: the speed at which the drag force equals the weight force, so the net force is zero. It depends on the height when gravity varies.
* **Energy lost to drag**: the energy that the drag force removes from the ball from the start of the run to the current time. It is never negative.
* **Numerical error**: the start energy minus the sum of kinetic energy, potential energy and energy lost to drag. It is zero for an exact integrator.

## Test

Run this command from the same folder.

```
python -m pytest -q       # 60 tests: 45 core and 15 animation, about 4 s
```

`pyproject.toml` sets `testpaths` to `tests` and `extras/tests`.
`start.py` runs the same command.
The animation tests use the Agg backend, so no window opens.

How the tests show that the physics is correct:

* Closed-form free fall: with no drag, x, v and a match `x0 + v0 t - g t^2 / 2` to 1e-6 m for both integrators.
* Terminal velocity: a long drop reaches `sqrt(m g / (CD rho pi r^2))` within 1 %, and the acceleration goes to zero.
* Integrator convergence: against the `tanh` solution for drag and constant gravity, both errors fall when dt halves, and rk4 is always more accurate. On a spring, 100 rk4 steps match `cos(1)` to 1e-9.
* Energy balance (extra): without drag, the energy stays constant to 1e-9 of the start energy before impact. With drag, kinetic plus potential plus energy lost to drag stays within 1e-3 of the start energy.

The GUI has no automated test. I tested it by hand.

## How to extend

New gravity model:

1. Add a `Force` subclass in `forces.py`.
2. Add one branch for it in `make_forces` in `simulation.py`.
3. Add its name to `GRAVITY_MODELS` in `parameters.py`.
4. Add the parameters it needs to `Parameters` and `validate`.
5. Add a unit label for each new parameter to `UNITS` in `gui.py`.
6. Add its potential energy to `potential_energy` in `extras/quantities.py`. If you do not, Animate fails for the new model.

New atmosphere: write a drag class that finds the density from a `density(x)` method, and use it in `make_forces` in place of `QuadraticDrag`.

New integrator: write a function with the signature of `simple_step`. Add it to `INTEGRATORS` and add its name to `INTEGRATOR_NAMES`.

New input format: write one reader that parses the file into a dict and calls `from_dict`, as `load_preset` does.
Call it where the program loads a file: `main` in `ballsim/__main__.py`, `App.load` in `ballsim/gui.py` and `main` in `extras/animate.py`.
Add the new suffix to `JSON_TYPES` in `gui.py`. The run loop takes only `Parameters`, so a new format does not change the simulation.

2-D motion: `State` holds vectors, each force returns a vector, `run` tests the height component, and `Trajectory`, `write_csv` and `plotting` get one column per component.

## Many users, many purposes: problems to expect

The brief asks me to imagine that many people use this code, from tennis balls to satellite re-entry.
These are the problems I expect, each with my answer.

* **Silent defaults.** A preset that omits a key gets the tennis ball value. A satellite preset without `fluid_density` runs in sea-level air, with no warning. Answer: make the physical inputs required, or log each default.
* **Implicit units.** All values are bare SI numbers. A user who types 100 for a height of 100 km gets a valid but wrong run. Answer: state the units in the preset format, convert at the input boundary, and warn about implausible values.
* **Constant density for re-entry.** The satellite preset uses 1e-5 kg/m^3 from 100 km to the ground, so it hits at 1386 m/s. That is not physical. Answer: add a `density(x)` drag class and keep the constant model as the default.
* **1-D only, no time argument.** Real re-entry and tennis shots move mostly sideways. `Force.force` has no time argument, so wind gusts or thrust need a change to every force. Answer: move `State` to vectors and add `t` to the force signature while few forces exist.

## Limitations

* Future work: an adaptive time step, a Mach-dependent CD, property-based tests and GIF export.
* The code does not handle R + x = 0 in the Newtonian model.
* The impact time and velocity come from linear interpolation, so they are approximate.
* Both integrators are explicit and have no step control. A time step above about 1 s gives wrong values for the tennis ball. Keep the step below about 0.5 s, or add an adaptive step.
* The animation redraws the whole figure for each frame, so the frame rate is low. Playback time stays correct, because time advances by the elapsed wall-clock time.
* I ran the code only on Linux with Python 3.14. I did not run `start.bat` on Windows, and I did not run anything on macOS.
* `requirements.txt` sets a minimum version for pytest only, so a future numpy or matplotlib release can break the code.

## How this was built

I read the brief and settled the design in structured question sessions. I made every decision in those sessions.
AI coding assistants (Claude Code) wrote the code and the tests from those decisions.
The work was test first. A separate AI reviewer checked each task against the plan before the commit.
An independent AI review panel then reviewed the core. Two sceptical verifiers tested each serious finding, and I corrected the findings that held.
A later simplification review removed 553 lines with no loss of brief coverage.
I tested the GUI and the animation by hand on Linux. I am responsible for every line, and I expect to walk through it at the interview.

## What this archive contains

I built the archive with this command:

```
git archive --format=zip --prefix=PrashantKumar/ -o PrashantKumar.zip HEAD
```

It holds exactly the version-controlled files. It holds no virtual environment, no caches and no git history.
