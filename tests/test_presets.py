import json
from dataclasses import replace
from pathlib import Path

import pytest

from ballsim.parameters import Parameters, validate
from ballsim.presets import from_dict, load_preset, save_preset


def test_round_trip(tmp_path):
    p = Parameters(name="x", mass=2.0)
    path = tmp_path / "x.json"
    save_preset(p, path)
    assert load_preset(path) == p
    shipped = Path(__file__).parent.parent / "presets" / "tennis_ball.json"
    assert load_preset(shipped) == Parameters()


@pytest.mark.parametrize(
    "field, bad",
    [
        ("mass", 0),
        ("radius", -1),
        ("time_step", 0),
        ("finish_time", 0),
        ("drag_coefficient", -0.1),
        ("fluid_density", -1),
        ("initial_height", 0),
        ("gravity_model", "moon"),
        ("integrator", "euler"),
        ("g", -1),
        ("finish_time", float("inf")),
        ("time_step", 1e-9),
    ],
)
def test_invalid_field_named(field, bad):
    with pytest.raises(ValueError, match=f"^{field} "):
        validate(replace(Parameters(), **{field: bad}))


def test_newtonian_needs_positive_planet():
    with pytest.raises(ValueError, match="R"):
        validate(replace(Parameters(), gravity_model="newtonian", R=0.0))


def test_unknown_key_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"mas": 1}))
    with pytest.raises(ValueError, match="mas"):
        load_preset(path)


def test_partial_preset_fills_defaults_and_casts(tmp_path):
    path = tmp_path / "partial.json"
    path.write_text(json.dumps({"mass": 2}))
    loaded = load_preset(path)
    assert loaded == replace(Parameters(), mass=2.0)
    assert isinstance(loaded.mass, float)


@pytest.mark.parametrize("bad", ['"abc"', "null"])
def test_non_numeric_preset_value_named(tmp_path, bad):
    path = tmp_path / "bad.json"
    path.write_text('{"mass": ' + bad + "}")
    with pytest.raises(ValueError, match="mass"):
        load_preset(path)


def test_preset_must_be_object(tmp_path):
    path = tmp_path / "list.json"
    path.write_text("[1, 2]")
    with pytest.raises(ValueError, match="JSON object"):
        load_preset(path)


def test_from_dict_parses_entry_texts():
    loaded = from_dict({"name": "x", "mass": "2", "integrator": "rk4"})
    assert loaded == replace(Parameters(), name="x", mass=2.0, integrator="rk4")


def test_from_dict_bad_number_names_field():
    with pytest.raises(ValueError, match="mass must be a number"):
        from_dict({"mass": "abc"})


def test_from_dict_rejects_unknown_key_and_invalid_value():
    with pytest.raises(ValueError, match="mas"):
        from_dict({"mas": "1"})
    with pytest.raises(ValueError, match="^mass "):
        from_dict({"mass": "0"})
