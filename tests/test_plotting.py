from matplotlib.figure import Figure

from ballsim.parameters import Parameters
from ballsim.plotting import add_trajectory, make_axes
from ballsim.simulation import run


def test_plot_smoke():
    trajectory = run(Parameters())
    fig = Figure()
    axes = make_axes(fig)
    add_trajectory(axes, trajectory)
    assert len(axes) == 3
    for ax in axes:
        assert len(ax.lines) == 2  # data line plus impact line
    assert axes[0].get_legend().get_texts()[0].get_text() == trajectory.label()
