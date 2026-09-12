"""Keep the browser config.ts numbers aligned with the desktop config.py spec."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sniper_range import config
from sniper_range.weapons import SNIPER

TS_PATH = Path(__file__).resolve().parents[1] / "web" / "src" / "config.ts"


def _parse_ts_numbers(source: str) -> dict[str, float | tuple[float, ...]]:
    values: dict[str, float | tuple[float, ...]] = {}
    scalar = re.compile(
        r"^export const ([A-Z][A-Z0-9_]+) = (-?\d+\.?\d*)(?:\s*/\s*(-?\d+\.?\d*))?;",
        re.MULTILINE,
    )
    for match in scalar.finditer(source):
        name, left, right = match.group(1), match.group(2), match.group(3)
        values[name] = float(left) / float(right) if right else float(left)
    vector = re.compile(
        r"^export const ([A-Z][A-Z0-9_]+): \[[^\]]+\] = \[([^\]]+)\];",
        re.MULTILINE,
    )
    for match in vector.finditer(source):
        parts = tuple(float(item.strip()) for item in match.group(2).split(","))
        values[match.group(1)] = parts
    return values


def test_web_config_matches_desktop_constants() -> None:
    parsed = _parse_ts_numbers(TS_PATH.read_text(encoding="utf-8"))
    expected: dict[str, float | tuple[float, ...]] = {
        "HIP_FOV": config.HIP_FOV,
        "SCOPE_FOV": config.SCOPE_FOV,
        "SCOPE_BLEND_SECONDS": config.SCOPE_BLEND_SECONDS,
        "CAMERA_NEAR": config.CAMERA_NEAR,
        "CAMERA_FAR": config.CAMERA_FAR,
        "MOVE_SPEED": config.MOVE_SPEED,
        "SPRINT_SPEED": config.SPRINT_SPEED,
        "CROUCH_SPEED": config.CROUCH_SPEED,
        "SCOPED_MOVE_SPEED": config.SCOPED_MOVE_SPEED,
        "HIP_SENSITIVITY": config.HIP_SENSITIVITY,
        "SCOPE_SENSITIVITY": config.SCOPE_SENSITIVITY,
        "PLAYER_HEIGHT": config.PLAYER_HEIGHT,
        "CROUCH_HEIGHT": config.CROUCH_HEIGHT,
        "CROUCH_BLEND_SECONDS": config.CROUCH_BLEND_SECONDS,
        "PLAYER_SPAWN": config.PLAYER_SPAWN,
        "RECOIL_RECOVERY": config.RECOIL_RECOVERY,
        "GRAVITY": config.GRAVITY,
        "MUZZLE_VELOCITY": config.MUZZLE_VELOCITY,
        "PROJECTILE_LIFETIME": config.PROJECTILE_LIFETIME,
        "MAX_PHYSICS_DT": config.MAX_PHYSICS_DT,
        "WIND_ACCEL_MIN": config.WIND_ACCEL_MIN,
        "WIND_ACCEL_MAX": config.WIND_ACCEL_MAX,
        "COMPASS_NORTH": config.COMPASS_NORTH,
        "SHOT_COOLDOWN": config.SHOT_COOLDOWN,
        "TRACER_SCALE": config.TRACER_SCALE,
        "RANGEFINDER_MAX": config.RANGEFINDER_MAX,
        "IMPACT_MARK_LIFETIME": config.IMPACT_MARK_LIFETIME,
        "IMPACT_MARK_SCALE": config.IMPACT_MARK_SCALE,
        "TARGET_RESET_SECONDS": config.TARGET_RESET_SECONDS,
        "TARGET_SCALE": config.TARGET_SCALE,
        "MAP_SIZE": config.MAP_SIZE,
        "FOG_RANGE": config.FOG_RANGE,
        "ZOOM_FOVS": SNIPER.zoom_fovs,
        "HIP_SPREAD_DEGREES": SNIPER.hip_spread_degrees,
        "AIM_SPREAD_DEGREES": SNIPER.aim_spread_degrees,
        "RECOIL_DEGREES": SNIPER.recoil_degrees,
    }
    for name, value in expected.items():
        assert name in parsed, f"{name} missing from config.ts"
        if isinstance(value, tuple):
            got = parsed[name]
            assert isinstance(got, tuple)
            assert got == pytest.approx(tuple(float(item) for item in value))
        else:
            assert parsed[name] == pytest.approx(float(value))
