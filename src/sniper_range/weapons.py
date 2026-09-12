"""Weapon data and first-person view models. No firing logic here."""

from __future__ import annotations

from dataclasses import dataclass

from ursina import Entity, camera, color

from sniper_range import config


@dataclass(frozen=True, slots=True)
class WeaponSpec:
    name: str
    select_key: str
    mode_label: str
    muzzle_velocity: float
    shot_cooldown: float
    automatic: bool
    zoom_fovs: tuple[float, ...]
    scope_overlay: bool
    hip_spread_degrees: float
    aim_spread_degrees: float
    recoil_degrees: float


# 80° hip / 16° / 8° / 4° → 5x, 10x, 20x. Overlay is the optic tube.
SNIPER = WeaponSpec(
    name="SR-500",
    select_key="1",
    mode_label="Repetierer",
    muzzle_velocity=config.MUZZLE_VELOCITY,
    shot_cooldown=config.SHOT_COOLDOWN,
    automatic=False,
    zoom_fovs=(16.0, 8.0, 4.0),
    scope_overlay=True,
    hip_spread_degrees=0.04,
    aim_spread_degrees=0.0,
    recoil_degrees=0.35,
)

# 7.62×39 at ~715 m/s, 600 rounds/min. Iron-sight ADS only.
AK47 = WeaponSpec(
    name="AK-47",
    select_key="2",
    mode_label="Vollauto",
    muzzle_velocity=715.0,
    shot_cooldown=0.1,
    automatic=True,
    zoom_fovs=(45.0,),
    scope_overlay=False,
    hip_spread_degrees=1.6,
    aim_spread_degrees=0.35,
    recoil_degrees=0.55,
)

LOADOUT = (SNIPER, AK47)

STEEL = color.rgb(0.16, 0.16, 0.15)
BLUED = color.rgb(0.22, 0.22, 0.2)
WOOD = color.rgb(0.42, 0.26, 0.14)
DARK_WOOD = color.rgb(0.28, 0.16, 0.1)
BAKELITE = color.rgb(0.22, 0.18, 0.12)


def build_sniper_model() -> tuple[Entity, list[Entity]]:
    parts: list[Entity] = []
    root = _part(
        parts,
        parent=camera,
        position=(0.2, -0.19, 0.22),
        rotation=(-3, -6, 0),
        origin_z=-0.5,
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=STEEL,
        position=(0, 0, 0.15),
        scale=(0.03, 0.04, 0.42),
        origin_z=-0.5,
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=BLUED,
        position=(0, 0.014, 0.46),
        scale=(0.016, 0.016, 0.28),
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=STEEL,
        position=(0, 0.03, 0.22),
        scale=(0.022, 0.022, 0.12),
    )
    return root, parts


def build_ak_model() -> tuple[Entity, list[Entity]]:
    parts: list[Entity] = []
    root = _part(
        parts,
        parent=camera,
        position=(0.21, -0.2, 0.2),
        rotation=(-4, -8, 4),
        origin_z=-0.5,
        enabled=False,
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=STEEL,
        position=(0, 0.0, 0.12),
        scale=(0.028, 0.038, 0.22),
        origin_z=-0.5,
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=WOOD,
        position=(0, -0.006, -0.02),
        scale=(0.03, 0.034, 0.16),
        origin_z=-0.5,
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=DARK_WOOD,
        position=(0.0, -0.028, 0.04),
        scale=(0.02, 0.05, 0.03),
        rotation=(18, 0, 0),
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=BLUED,
        position=(0, 0.01, 0.38),
        scale=(0.014, 0.014, 0.26),
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=WOOD,
        position=(0, 0.004, 0.34),
        scale=(0.026, 0.022, 0.1),
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=BAKELITE,
        position=(0.0, -0.04, 0.1),
        scale=(0.02, 0.07, 0.028),
        rotation=(22, 0, 12),
    )
    _part(
        parts,
        parent=root,
        model="cube",
        color=BAKELITE,
        position=(0.01, -0.07, 0.08),
        scale=(0.018, 0.05, 0.024),
        rotation=(48, 0, 10),
    )
    return root, parts


def _part(parts: list[Entity], **kwargs) -> Entity:
    entity = Entity(**kwargs)
    parts.append(entity)
    return entity
