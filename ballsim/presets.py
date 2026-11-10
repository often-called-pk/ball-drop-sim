"""Save and load parameters as flat JSON files."""
from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path

from ballsim.parameters import TEXT_FIELDS, Parameters, validate


def from_dict(data: dict) -> Parameters:
    """Build validated Parameters from a dict of numbers or number texts."""
    unknown = sorted(set(data) - {f.name for f in fields(Parameters)})
    if unknown:
        raise ValueError(f"unknown preset key(s): {', '.join(unknown)}")
    values = {}
    for key, value in data.items():
        if key not in TEXT_FIELDS:
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key} must be a number, got {value!r}")
        values[key] = value
    params = Parameters(**values)
    validate(params)
    return params


def load_preset(path: str | Path) -> Parameters:
    """Read a preset file, fill gaps with defaults and validate it."""
    with open(path) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("preset must be a JSON object")
    return from_dict(data)


def save_preset(params: Parameters, path: str | Path) -> None:
    """Write every parameter so the file shows the full run setup."""
    with open(path, "w") as f:
        json.dump(asdict(params), f, indent=2)
