from pathlib import Path

import pytest

from ballsim.__main__ import main

PRESETS = Path(__file__).parent.parent / "presets"
TENNIS = str(PRESETS / "tennis_ball.json")
SATELLITE = str(PRESETS / "satellite_reentry.json")


def test_cli_prints_summary_and_csv(tmp_path, capsys):
    out = tmp_path / "out.csv"
    main([TENNIS, "--no-plot", "--csv", str(out)])
    assert "impact" in capsys.readouterr().out
    lines = out.read_text().splitlines()
    assert lines[0] == "t,x,v,a"
    assert len(lines) - 1 > 10


def test_cli_two_presets_two_csvs(tmp_path):
    out = tmp_path / "out.csv"
    main([TENNIS, SATELLITE, "--no-plot", "--csv", str(out)])
    assert (tmp_path / "out_tennis_ball.csv").exists()
    assert (tmp_path / "out_satellite_re-entry.csv").exists()


def test_cli_integrator_override_changes_result(capsys):
    main([TENNIS, "--no-plot"])
    simple = capsys.readouterr().out
    main([TENNIS, "--no-plot", "--integrator", "rk4"])
    assert capsys.readouterr().out != simple


def test_cli_needs_a_preset():
    with pytest.raises(SystemExit):
        main(["--no-plot"])


def test_cli_missing_preset_file_exits_cleanly(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "missing.json"), "--no-plot"])
