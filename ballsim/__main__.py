"""Command line entry point: python -m ballsim preset.json [--gui]."""
from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from ballsim.parameters import INTEGRATOR_NAMES
from ballsim.plotting import add_trajectory, make_axes
from ballsim.presets import load_preset
from ballsim.simulation import Trajectory, describe, run, write_csv


def csv_path(base: Path, trajectory: Trajectory, several: bool) -> Path:
    """One run uses the path as given. Several runs add the run name to the file name."""
    if not several:
        return base
    name = trajectory.name.replace(" ", "_")
    return base.with_name(f"{base.stem}_{name}{base.suffix}")


def main(argv: list[str] | None = None) -> None:
    """Run the presets named on the command line, or open the GUI."""
    parser = argparse.ArgumentParser(prog="ballsim", description="Ball drop simulation.")
    parser.add_argument("presets", nargs="*", help="preset JSON files to run")
    parser.add_argument("--gui", action="store_true", help="open the graphical interface")
    parser.add_argument("--integrator", choices=INTEGRATOR_NAMES,
                        help="override the preset integrator")
    parser.add_argument("--csv", metavar="PATH", help="write each trajectory to a CSV file")
    parser.add_argument("--no-plot", action="store_true", help="skip the plot window")
    args = parser.parse_args(argv)

    if args.gui:
        from ballsim import gui  # imported here so the CLI needs no Tk

        gui.main()
        return
    if not args.presets:
        parser.error("give at least one preset file, or --gui")

    trajectories = []
    for path in args.presets:
        try:
            params = load_preset(path)
        except (OSError, ValueError) as error:
            raise SystemExit(f"ballsim: {error}")
        if args.integrator:
            params = replace(params, integrator=args.integrator)
        trajectory = run(params)
        print(describe(trajectory))
        trajectories.append(trajectory)

    if args.csv:
        several = len(trajectories) > 1
        for trajectory in trajectories:
            write_csv(trajectory, csv_path(Path(args.csv), trajectory, several))

    if not args.no_plot:
        import matplotlib.pyplot as plt  # imported here so --no-plot never opens a GUI backend

        fig = plt.figure(figsize=(8, 9))
        axes = make_axes(fig)
        for trajectory in trajectories:
            add_trajectory(axes, trajectory)
        plt.show()


if __name__ == "__main__":
    main()
