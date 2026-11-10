import time
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ballsim.presets import load_preset
from ballsim.simulation import run
from extras.animate import TARGET_PLAYBACK, Animator, format_readout, main, values_at
from extras.quantities import compute

PRESETS = Path(__file__).resolve().parents[2] / "presets"


def tennis(**kw):
    return replace(load_preset(PRESETS / "tennis_ball.json"), integrator="rk4", **kw)


def make_animator(params):
    fig = Figure(figsize=(13, 8))
    FigureCanvasAgg(fig)
    animator = Animator(fig, params)
    fig.canvas.draw()
    return animator


def test_values_at_zero_is_first_sample():
    params = tennis()
    traj = run(params)
    q = compute(params, traj)
    values = values_at(traj, q, 0.0)
    assert values["x"] == traj.x[0]
    assert values["v"] == traj.v[0]
    assert values["drag"] == q.drag[0]
    assert values["lost"] == q.lost[0]


def test_readout_says_no_drag():
    params = tennis(drag_coefficient=0.0)
    traj = run(params)
    text = format_readout(values_at(traj, compute(params, traj), 1.0))
    assert "no drag" in text


def test_tennis_draws_scrubs_and_shows_banner_at_end():
    animator = make_animator(tennis())
    traj, q = animator.trajectory, animator.quantities
    assert not animator.banner.get_visible()
    animator.draw_frame(3.0)
    assert animator.ball.get_ydata()[0] == pytest.approx(np.interp(3.0, traj.t, traj.x))
    for line in animator.graph_lines:
        assert line.get_xdata()[-1] <= 3.0 + 1e-12
    assert "3.00" in animator.readout.get_text()
    assert len(animator.graph_lines[1].axes.lines) == 3  # line, dot and terminal speed
    animator.scrubber.set_val(5.0)
    assert animator.time == 5.0
    assert "5.00" in animator.readout.get_text()
    assert not animator.banner.get_visible()
    animator.scrubber.set_val(animator.t_end)
    assert animator.banner.get_visible()
    ground = animator.ball_ax.get_ylim()[0]
    assert ground < 0
    assert traj.x[-1] + q.weight[-1] / animator.n_per_m >= ground  # weight arrow stays in view


def test_satellite_builds_and_draws_first_and_last_frame():
    animator = make_animator(load_preset(PRESETS / "satellite_reentry.json"))
    animator.draw_frame(animator.trajectory.t[-1])
    animator.draw_frame(0.0)
    assert len(animator.graph_lines[1].axes.lines) == 2  # line and dot only


@pytest.mark.filterwarnings("error")
def test_no_drag_builds_without_warnings():
    animator = make_animator(tennis(drag_coefficient=0.0))
    animator.draw_frame(animator.t_end)
    animator.fig.canvas.draw()


@pytest.mark.filterwarnings("error::RuntimeWarning")
def test_zero_gravity_builds_and_draws():
    animator = make_animator(tennis(g=0.0, initial_velocity=-5.0))
    animator.draw_frame(animator.t_end)
    animator.fig.canvas.draw()


def test_step_advances_time_at_fixed_playback_rate():
    animator = make_animator(tennis())
    animator.step(0)  # first tick only starts the clock
    assert animator.time == 0.0
    for _ in range(3):
        animator.last_tick = time.perf_counter() - 0.1
        animator.step(0)
    rate = animator.t_end / TARGET_PLAYBACK
    assert animator.time == pytest.approx(3 * rate * 0.1, rel=0.05)


def test_pause_resume_and_run_to_end():
    animator = make_animator(tennis())
    calls = []
    animator.animation.pause = lambda: calls.append("pause")
    animator.animation.resume = lambda: calls.append("resume")
    animator.toggle_pause()
    assert animator.playing is False
    assert animator.pause_button.label.get_text() == "Resume"
    animator.scrubber.set_val(5.0)  # scrubbing while paused still redraws and holds the time
    assert "5.00" in animator.readout.get_text()
    animator.step(0)
    assert animator.time == 5.0
    animator.toggle_pause()
    assert animator.playing is True
    assert animator.last_tick is None  # a resume must not count the paused time
    animator.time = animator.t_end - 1e-9
    animator.last_tick = time.perf_counter() - 0.1
    animator.step(0)
    assert animator.playing is False
    assert animator.banner.get_visible()
    assert "impact" in animator.banner.get_text()
    assert animator.pause_button.label.get_text() == "Resume"
    animator.toggle_pause()  # resume at the end restarts
    assert animator.time == 0.0 and animator.playing is True
    assert not animator.banner.get_visible()
    assert calls == ["pause", "resume", "pause", "resume"]


def test_main_missing_file_exits_with_message():
    with pytest.raises(SystemExit) as info:
        main([str(PRESETS / "does_not_exist.json")])
    assert "animate" in str(info.value)
