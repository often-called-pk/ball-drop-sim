# Ball drop simulation

This program simulates a ball that falls in one dimension under gravity and quadratic drag.
It answers the TOYOTA Racing coding challenge for a Simulation Engineer.
It needs Python 3.10 or newer, numpy and matplotlib.

![The GUI form with the tennis ball preset after a run](docs/gui.png)

![Height, velocity and acceleration of the tennis ball preset](docs/plot_tennis_ball.png)

The tennis ball reaches its terminal velocity of 16.09 m/s and its acceleration falls to almost zero before it lands at 7.35 s.

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
* `ballsim/simulation.py`: `make_forces`, `acceleration`, `run`, `describe`, `write_csv` and the `Trajectory` class.
* `ballsim/presets.py`: `from_dict`, `load_preset` and `save_preset`.
* `ballsim/plotting.py`: `make_axes` and `add_trajectory`. It uses `Figure` and not pyplot, so the GUI can embed it.
* `ballsim/__main__.py`: the command line and `csv_path`.
* `ballsim/gui.py`: the Tk window.
* `tests/`: the tests.
* `presets/`: the tennis ball and satellite re-entry presets.
* `start.py`, `start.sh`, `start.bat`: the one-command setup. It checks Python and Tk, builds `.venv`, installs, tests and starts the GUI.

The solution keeps to the core that the brief asks for, plus a small GUI to run it, and stops there.

## What the brief asks and where it is met

Test names are in `tests/`.

| Brief requirement | Where in the code | Test that proves it |
|:--|:--|:--|
| Drag `\|FD\| = CD rho v^2 pi r^2`, opposite to motion | `forces.py`, `QuadraticDrag` | `test_forces.py::test_drag_opposes_motion`, `test_simulation.py::test_terminal_velocity` |
| Constant gravity `FW = m g` | `forces.py`, `ConstantGravity` | `test_forces.py::test_constant_gravity`, `test_simulation.py::test_free_fall_matches_closed_form` |
| Newtonian gravity `-FW = G M m / (R + x)^2` | `forces.py`, `NewtonianGravity` | `test_simulation.py::test_run_uses_chosen_gravity_model` |
| User picks the gravity model | `Parameters.gravity_model`, `make_forces`, GUI menu | `test_simulation.py::test_run_uses_chosen_gravity_model`, `test_presets.py::test_invalid_field_named` |
| `FW + FD = m a` | `simulation.py`, `acceleration` | `test_simulation.py::test_free_fall_matches_closed_form`, `test_terminal_velocity`, `test_rk4_more_accurate_and_both_converge` |
| Forces at time t from the current x and v, then numerical integration | `run` passes `accel(state)` to the integrator | `test_integrators.py::test_simple_step_matches_brief_formula` |
| The brief scheme, plus a built-in alternative | `integrators.py`, `simple_step` and `rk4_step` | `test_simple_step_matches_brief_formula`, `test_rk4_accurate_on_spring`, `test_simulation.py::test_rk4_more_accurate_and_both_converge` |
| Calculate x, v and a | `Trajectory`, CSV columns `t,x,v,a` (also the GUI Save CSV button), three plot panels | `test_cli.py::test_cli_prints_summary_and_csv`, `test_simulation.py::test_free_fall_matches_closed_form` |
| User varies CD, rho, r, m, g, G, M, R, initial height and velocity, finish time, time step | `Parameters` and `validate`, one preset key and one GUI entry each | `test_presets.py::test_invalid_field_named`, `test_newtonian_needs_positive_planet` |
| Model valid for x > 0, x = 0 is impact, R + x = 0 not handled | `run` stops at the first x <= 0 and interpolates to x = 0. `validate` requires a positive initial height | `test_simulation.py::test_impact_time_interpolated` |
| Tests and visualisations | `ballsim/plotting.py`, `ballsim/gui.py` | 45 tests in total, `test_plotting.py::test_plot_smoke` |
| Easy to extend, easy to change the input format | `Force` base class, `INTEGRATORS`, `make_forces`, `from_dict` | `test_integrators.py::test_names_match_parameters`, `test_presets.py::test_round_trip`, `test_from_dict_parses_entry_texts` |
| Instructions to compile, run and test | This file, `start.py` | `test_cli.py` (the start scripts have no automated test) |
| One zip named with first and last name | `PrashantKumar.zip` | None |

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
satellite re-entry: impact at t = 2824.238 s, v = -35.718 m/s, max speed 35.718 m/s
```

A plot window opens unless you give `--no-plot`. With two presets, the window overlays both runs.

Options:

* `--integrator {simple,rk4}` replaces the integrator in every preset.
* `--no-plot` skips the plot window.
* `--csv PATH` writes each trajectory to a CSV file with the columns `t,x,v,a`, to 6 significant figures (`%.6g`). With several runs, the program adds the run name to the file name, for example `out_tennis_ball.csv`.

In the GUI window, edit the parameters, load or save a preset, and press Run.
Each run adds to the plots. Clear them with Clear plots, or untick Keep previous runs.
Save CSV writes the last run to a file with the columns `t,x,v,a`, in the same format as `--csv`.

## Preset format

A preset is a flat JSON file. The keys are the field names of `Parameters` in `ballsim/parameters.py`.
`presets/tennis_ball.json` shows every key.
All values are in SI units: metres, kilograms, seconds.
Missing keys take the default values, which are the tennis ball values. Unknown keys raise an error.
The program checks the values and names the field that is wrong.

## Test

Run this command from the same folder.

```
python -m pytest -q       # 45 tests, about 0.5 s
```

`start.py` runs the same command.

How the tests show that the physics is correct:

* Closed-form free fall: with no drag, x, v and a match `x0 + v0 t - g t^2 / 2` to 1e-6 m for both integrators.
* Terminal velocity: a long drop reaches `sqrt(m g / (CD rho pi r^2))` within 1 %, and the acceleration goes to zero.
* Integrator convergence: against the `tanh` solution for drag and constant gravity, both errors fall when dt halves. rk4 is more accurate at the tested steps (dt 0.1 and 0.05 s). On a spring, 100 rk4 steps match `cos(1)` to 1e-9.

The GUI has no automated test. I tested it by hand.

## How to extend

New gravity model:

1. Add a `Force` subclass in `forces.py`.
2. Add one branch for it in `make_forces` in `simulation.py`.
3. Add its name to `GRAVITY_MODELS` in `parameters.py`.
4. Add the parameters it needs to `Parameters` and `validate`.
5. Add a label with its symbol and unit for each new parameter to `LABELS` in `gui.py`.

New atmosphere: write a drag class that finds the density from a `density(x)` method, and use it in `make_forces` in place of `QuadraticDrag`.

New integrator: write a function with the signature of `simple_step`. Add it to `INTEGRATORS` and add its name to `INTEGRATOR_NAMES`.

New input format: write one reader that parses the file into a dict and calls `from_dict`, as `load_preset` does.
Call it where the program loads a file: `main` in `ballsim/__main__.py` and `App.load` in `ballsim/gui.py`.
Add the new suffix to `JSON_TYPES` in `gui.py`. The run loop takes only `Parameters`, so a new format does not change the simulation.

2-D motion: `State` holds vectors, each force returns a vector, `run` tests the height component, and `Trajectory`, `write_csv` and `plotting` get one column per component.
