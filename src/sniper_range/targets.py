"""Steel silhouettes that fall on a hit and stand back up after a delay."""

from __future__ import annotations

from ursina import Entity, Vec3, color, invoke
from ursina.shaders import unlit_shader

from sniper_range import config
from sniper_range.hits import HitResult


class SteelTarget(Entity):
    def __init__(self, position: tuple[float, float, float], **kwargs) -> None:
        super().__init__(
            model="cube",
            texture="white_cube",
            color=color.rgb(0.72, 0.28, 0.14),
            scale=config.TARGET_SCALE,
            position=position,
            origin_y=-0.5,
            collider="box",
            shader=unlit_shader,
            **kwargs,
        )
        self.standing = True
        self.bullseye = Entity(
            parent=self,
            model="quad",
            z=-0.52,
            scale=(0.45, 0.28),
            color=color.rgb(0.95, 0.95, 0.9),
        )
        self.center = Entity(
            parent=self.bullseye,
            model="circle",
            z=-0.01,
            scale=0.45,
            color=color.rgb(0.15, 0.12, 0.12),
        )
        self.base = Entity(
            parent=self,
            model="cube",
            color=color.rgb(0.18, 0.16, 0.14),
            position=(0, 0.02, 0.35),
            scale=(1.15, 0.06, 0.7),
            origin_y=-0.5,
        )

    def on_bullet_hit(self, point) -> HitResult | None:
        _ = point
        if not self.standing:
            return None
        self.register_hit()
        return HitResult(scored=True, label="Treffer")

    def register_hit(self) -> None:
        if not self.standing:
            return
        self.standing = False
        self.animate("rotation_x", 82, duration=0.28)
        invoke(self.reset_target, delay=config.TARGET_RESET_SECONDS)

    def reset_target(self) -> None:
        self.animate("rotation_x", 0, duration=0.35)
        invoke(setattr, self, "standing", True, delay=0.35)


def spawn_targets() -> list[SteelTarget]:
    """Place 11 plates from 80 m out to the far ridgeline (~700 m)."""
    placements = (
        (8, 0.0, 80),
        (-18, 0.0, 120),
        (42, 0.0, 155),
        (-55, 0.0, 220),
        (90, 4.0, 300),
        (-20, 0.0, 360),
        (140, 0.0, 420),
        (-110, 5.0, 480),
        (35, 0.0, 540),
        (-70, 0.0, 620),
        (20, 8.0, 700),
    )
    targets: list[SteelTarget] = []
    for x, y, z in placements:
        target = SteelTarget(position=(x, y, z))
        target.look_at(Vec3(0, y + 0.9, 0))
        target.rotation = (0, target.rotation_y, 0)
        targets.append(target)
    return targets
