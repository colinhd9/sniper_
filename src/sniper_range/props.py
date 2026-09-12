"""Shared world primitives. Buildings and landmarks use the same box helper."""

from __future__ import annotations

from ursina import Entity, color
from ursina.shaders import lit_with_shadows_shader


def box(
    position: tuple[float, float, float],
    scale: tuple[float, float, float],
    *,
    color_value=color.rgb(0.45, 0.4, 0.34),
    texture: str = "brick",
    rotation: tuple[float, float, float] = (0, 0, 0),
    collider: str | None = "box",
) -> Entity:
    """Axis-aligned cube sitting on the ground (`origin_y = -0.5`)."""
    return Entity(
        model="cube",
        texture=texture,
        texture_scale=(max(1, scale[0] / 4), max(1, scale[1] / 4)),
        color=color_value,
        position=position,
        scale=scale,
        rotation=rotation,
        collider=collider,
        origin_y=-0.5,
        shader=lit_with_shadows_shader,
    )
