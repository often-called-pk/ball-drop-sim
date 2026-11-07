from dataclasses import replace

import time

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ballsim.presets import load_preset
from ballsim.simulation import run
from extras.animate import FPS, Animator, format_readout, start_speed_index, values_at
from extras.quantities import compute


def tennis(**kw):
    return replace(load_preset("presets/tennis_ball.json"), integrator="rk4", **kw)


def make_animator(params):
    fig = Figure(figsize=(13, 8))
    FigureCanvasAgg(fig)
    animator = Animator(fig, params)
    fig.canvas.draw()
    return animator


@pytest.mark.parametrize("duration, index", [(7.348, 1), (144.7, 5), (2824, 8), (1.0, 0)])
def test_start_speed_index(duration, index):
    assert start_speed_index(duration) == index


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


def test_draw_frame_moves_ball_graphs_and_readout():
    animator = make_animator(tennis())
    animator.draw_frame(3.0)
    traj = animator.trajectory
    assert animator.ball.get_ydata()[0] == pytest.approx(np.interp(3.0, traj.t, traj.x))
    for line in animator.graph_lines:
        assert line.get_xdata()[-1] <= 3.0 + 1e-12
    assert "3.00" in animator.readout.get_text()


def test_satellite_builds_and_draws_last_frame():
    animator = make_animator(load_preset("presets/satellite_reentry.json"))
    animator.draw_frame(animator.trajectory.t[-1])
    animator.draw_frame(0.0)


@pytest.mark.filterwarnings("error")
def test_no_drag_builds_without_warnings():
    animator = make_animator(tennis(drag_coefficient=0.0))
    animator.draw_frame(animator.t_end)
    animator.fig.canvas.draw()


class FakeKey:
    def __init__(self, key):
        self.key = key


def test_step_advances_time_by_speed_times_elapsed():
    animator = make_animator(tennis())
    animator.on_speed(5)  # x10
    before = animator.time
    for _ in range(3):
        animator.last_tick = time.perf_counter() - 0.1
        animator.step(0)
    assert animator.time - before == pytest.approx(3 * 10 * 0.1, rel=0.05)


def test_scrubber_sets_time_and_pause_holds_it():
    animator = make_animator(tennis())
    animator.scrubber.set_val(5.0)
    assert animator.time == 5.0
    animator.playing = False
    animator.step(0)
    assert animator.time == 5.0


def test_run_to_end_stops_and_shows_banner():
    animator = make_animator(tennis())
    animator.time = animator.t_end - 1e-9
    animator.last_tick = time.perf_counter() - 0.1
    animator.step(0)
    assert animator.playing is False
    assert animator.banner.get_visible()
    assert "impact" in animator.banner.get_text()
    assert animator.pause_button.label.get_text() == "Resume"


def test_toggle_pause_flips_and_restarts_at_end():
    animator = make_animator(tennis())
    animator.toggle_pause()
    assert animator.playing is False
    assert animator.pause_button.label.get_text() == "Resume"
    animator.toggle_pause()
    assert animator.playing is True
    animator.time = animator.t_end
    animator.playing = False
    animator.toggle_pause()
    assert animator.time == 0.0 and animator.playing is True


def test_restart_resets_time_and_banner():
    animator = make_animator(tennis())
    animator.time = animator.t_end
    animator.step(0)
    animator.restart()
    assert animator.time == 0.0
    assert animator.playing is True
    assert not animator.banner.get_visible()


def test_on_speed_updates_label():
    animator = make_animator(tennis())
    animator.on_speed(5)
    assert "x10" in animator.time_label.get_text()
    assert animator.speed_slider.valtext.get_text() == "x10"


def test_keys_toggle_and_restart():
    animator = make_animator(tennis())
    animator.on_key(FakeKey(" "))
    assert animator.playing is False
    animator.time = 4.0
    animator.on_key(FakeKey("r"))
    assert animator.time == 0.0 and animator.playing is True
