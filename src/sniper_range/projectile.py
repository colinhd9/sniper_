"""Visible tracer that integrates ballistics and raycasts to avoid tunneling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Entity, Vec3, color, destroy, raycast, time

from sniper_range import config
from sniper_range.ballistics import Vec3 as PhysVec3
from sniper_range.ballistics import initial_velocity, step

if TYPE_CHECKING:
    from sniper_range.app import Game


def _to_phys(vector: Vec3) -> PhysVec3:
    return PhysVec3(float(vector.x), float(vector.y), float(vector.z))


def _to_ursina(vector: PhysVec3) -> Vec3:
    return Vec3(vector.x, vector.y, vector.z)


class Projectile(Entity):
    def __init__(
        self,
        game: Game,
        origin: Vec3,
        direction: Vec3,
        muzzle_velocity: float = config.MUZZLE_VELOCITY,
    ) -> None:
        super().__init__(
            model="cube",
            color=color.rgb(1.0, 0.72, 0.18),
            position=origin,
            scale=config.TRACER_SCALE,
            collider=None,
        )
        self.game = game
        self.phys_position = _to_phys(origin)
        self.phys_velocity = initial_velocity(_to_phys(direction), muzzle_velocity)
        self.age = 0.0
        self.look_at(self.position + _to_ursina(self.phys_velocity))

    def update(self) -> None:
        dt = min(time.dt, config.MAX_PHYSICS_DT)
        self.age += dt
        if self.age >= config.PROJECTILE_LIFETIME:
            destroy(self)
            return

        old_position = self.phys_position
        self.phys_position, self.phys_velocity = step(
            self.phys_position,
            self.phys_velocity,
            self.game.wind,
            dt,
            config.GRAVITY,
        )

        travel = self.phys_position - old_position
        distance = travel.length()
        if distance > 0.0:
            # Sweep a ray along the integrated segment so a 500 m/s tracer
            # cannot skip through a thin steel plate between two frames.
            hit = raycast(
                _to_ursina(old_position),
                _to_ursina(travel.normalized()),
                distance=distance,
                ignore=[*self.game.projectile_ignore, self],
                debug=False,
            )
            if hit.hit:
                self._impact(hit)
                return

        self.position = _to_ursina(self.phys_position)
        if self.phys_velocity.length() > 0.0:
            self.look_at(self.position + _to_ursina(self.phys_velocity))

    def _impact(self, hit) -> None:
        point = hit.world_point
        shot_distance = (point - self.game.player.world_position).length()
        target = hit.entity
        handler = getattr(target, "on_bullet_hit", None) if target is not None else None
        result = handler(point) if callable(handler) else None
        if result is None:
            _spawn_impact_mark(point, hit.world_normal)

        scored = bool(result is not None and result.scored)
        self.game.report_impact(
            hit=scored,
            distance=shot_distance,
            point=point,
            label=result.label if result is not None else "",
        )
        self.game.notify_impact(point)
        destroy(self)


def _spawn_impact_mark(point: Vec3, normal: Vec3) -> None:
    offset = (normal.normalized() * 0.04) if normal.length() else Vec3(0, 0.04, 0)
    mark = Entity(
        model="sphere",
        color=color.rgb(0.12, 0.1, 0.08),
        position=point + offset,
        scale=config.IMPACT_MARK_SCALE,
    )
    destroy(mark, delay=config.IMPACT_MARK_LIFETIME)


def spawn_projectile(
    game: Game,
    origin: Vec3,
    direction: Vec3,
    muzzle_velocity: float = config.MUZZLE_VELOCITY,
) -> Projectile:
    return Projectile(game, origin, direction, muzzle_velocity)
