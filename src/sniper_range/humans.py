"""Orange training mannequins that patrol, flee to cover, and score by zone."""

from __future__ import annotations

from math import copysign, hypot, sin
from typing import Iterable

from ursina import Entity, Vec3, color, invoke, time
from ursina.shaders import unlit_shader

from sniper_range import config
from sniper_range.ballistics import Vec3 as PhysVec3
from sniper_range.buildings import Settlement
from sniper_range.hits import HitResult
from sniper_range.patrol import PatrolStep, advance

ORANGE = color.rgb(0.86, 0.38, 0.12)
HEAD = color.rgb(0.93, 0.82, 0.62)
STAND = color.rgb(0.16, 0.14, 0.12)

STATE_PATROL = "patrolling"
STATE_FLEE = "fleeing"
STATE_COVER = "in_cover"
STATE_DOWN = "down"

_COVER_REACH = 0.45
_STRIDE_PER_METER = 2.6
_SWING_DEGREES = 18.0


class _HitZone(Entity):
    """Child collider that forwards the shot to the owning mannequin."""

    def __init__(self, owner: RangeMannequin, zone: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.owner = owner
        self.zone = zone

    def on_bullet_hit(self, point) -> HitResult | None:
        return self.owner.on_bullet_hit(point, zone=self.zone)


class RangeMannequin(Entity):
    def __init__(
        self,
        route: Iterable[PhysVec3],
        cover_points: Iterable[Vec3],
        **kwargs,
    ) -> None:
        self._route = tuple(route)
        if not self._route:
            raise ValueError("RangeMannequin needs at least one waypoint")
        start = self._route[0]
        super().__init__(
            position=(start.x, start.y, start.z),
            collider=None,
            **kwargs,
        )
        self.cover_points = tuple(cover_points)
        self.waypoint_index = 1 if len(self._route) > 1 else 0
        self._state = STATE_PATROL
        self._cover_target: Vec3 | None = None
        self._cover_left = 0.0
        self._stride_phase = 0.0
        self._build_body()
        first_heading = advance(start, self._route, self.waypoint_index, 1.0, 0.0).heading_degrees
        self.rotation_y = first_heading

    def _build_body(self) -> None:
        # Parts sit on the root so a fall is one rotation. Three colliders keep
        # the 500 m/s sweep cheap: head, torso, legs. Arms are visual only.
        self.stand = Entity(
            parent=self,
            model="cube",
            color=STAND,
            position=(0, 0.02, 0),
            scale=(0.36, 0.05, 0.22),
            origin_y=-0.5,
            shader=unlit_shader,
        )
        self.left_leg = _HitZone(
            self,
            "body",
            parent=self,
            model="cube",
            color=ORANGE,
            position=(-0.09, 0.88, 0),
            scale=(0.13, 0.88, 0.14),
            origin_y=0.5,
            collider="box",
            shader=unlit_shader,
        )
        self.right_leg = _HitZone(
            self,
            "body",
            parent=self,
            model="cube",
            color=ORANGE,
            position=(0.09, 0.88, 0),
            scale=(0.13, 0.88, 0.14),
            origin_y=0.5,
            collider="box",
            shader=unlit_shader,
        )
        self.torso = _HitZone(
            self,
            "body",
            parent=self,
            model="cube",
            color=ORANGE,
            position=(0, 0.88, 0),
            scale=(0.38, 0.58, 0.22),
            origin_y=-0.5,
            collider="box",
            shader=unlit_shader,
        )
        self.head = _HitZone(
            self,
            "head",
            parent=self,
            model="cube",
            color=HEAD,
            position=(0, 1.52, 0),
            scale=(0.24, 0.26, 0.22),
            origin_y=-0.5,
            collider="box",
            shader=unlit_shader,
        )
        self.left_arm = Entity(
            parent=self,
            model="cube",
            color=ORANGE,
            position=(-0.26, 1.42, 0),
            scale=(0.10, 0.52, 0.10),
            origin_y=0.5,
            shader=unlit_shader,
        )
        self.right_arm = Entity(
            parent=self,
            model="cube",
            color=ORANGE,
            position=(0.26, 1.42, 0),
            scale=(0.10, 0.52, 0.10),
            origin_y=0.5,
            shader=unlit_shader,
        )

    def update(self) -> None:
        dt = min(time.dt, config.MAX_PHYSICS_DT)
        if dt <= 0.0 or self._state == STATE_DOWN:
            return
        if self._state == STATE_PATROL:
            self._tick_patrol(dt)
        elif self._state == STATE_FLEE:
            self._tick_flee(dt)
        elif self._state == STATE_COVER:
            self._tick_cover(dt)

    def alert_to(self, point) -> None:
        if self._state != STATE_PATROL:
            return
        dx = float(point.x) - float(self.x)
        dz = float(point.z) - float(self.z)
        if hypot(dx, dz) > config.MANNEQUIN_ALERT_RADIUS:
            return
        self._begin_flee()

    def on_bullet_hit(self, point, zone: str = "body") -> HitResult | None:
        _ = point
        if self._state == STATE_DOWN:
            return None
        self._state = STATE_DOWN
        self.animate("rotation_x", 82, duration=0.32)
        invoke(self._reset, delay=config.MANNEQUIN_RESET_SECONDS)
        label = "Kopftreffer" if zone == "head" else "Körpertreffer"
        return HitResult(scored=True, label=label)

    def _tick_patrol(self, dt: float) -> None:
        here = self._phys_position()
        step = advance(
            here,
            self._route,
            self.waypoint_index,
            config.MANNEQUIN_WALK_SPEED,
            dt,
            loop=True,
        )
        self.waypoint_index = step.waypoint_index
        self._apply_step(step, dt)

    def _tick_flee(self, dt: float) -> None:
        target = self._cover_target
        if target is None:
            self._state = STATE_COVER
            self._cover_left = config.MANNEQUIN_COVER_SECONDS
            self._pose_idle(dt)
            return
        here = self._phys_position()
        goal = PhysVec3(float(target.x), 0.0, float(target.z))
        step = advance(here, (here, goal), 1, config.MANNEQUIN_SPRINT_SPEED, dt, loop=False)
        self._apply_step(step, dt)
        if hypot(float(self.x) - goal.x, float(self.z) - goal.z) <= _COVER_REACH:
            self._state = STATE_COVER
            self._cover_left = config.MANNEQUIN_COVER_SECONDS

    def _tick_cover(self, dt: float) -> None:
        self._cover_left -= dt
        self._pose_idle(dt)
        if self._cover_left <= 0.0:
            self._state = STATE_PATROL
            self._cover_target = None

    def _begin_flee(self) -> None:
        self._state = STATE_FLEE
        self._cover_target = self._nearest_cover()

    def _nearest_cover(self) -> Vec3 | None:
        if not self.cover_points:
            return None
        return min(
            self.cover_points,
            key=lambda point: hypot(float(point.x) - float(self.x), float(point.z) - float(self.z)),
        )

    def _apply_step(self, step: PatrolStep, dt: float) -> None:
        old_x, old_z = float(self.x), float(self.z)
        self.position = (step.position.x, step.position.y, step.position.z)
        self.rotation_y = _turn_towards(float(self.rotation_y), step.heading_degrees, config.MANNEQUIN_TURN_RATE * dt)
        moved = hypot(step.position.x - old_x, step.position.z - old_z)
        self._stride_phase += moved * _STRIDE_PER_METER
        self._pose_gait(self._stride_phase, moving=moved > 0.001)

    def _pose_idle(self, dt: float) -> None:
        # Decay the last stride so they do not freeze mid-swing in cover.
        self._stride_phase += (0.0 - self._stride_phase) * min(1.0, dt * 8.0)
        self._pose_gait(self._stride_phase, moving=False)

    def _pose_gait(self, phase: float, *, moving: bool) -> None:
        swing = sin(phase) * (_SWING_DEGREES if moving else _SWING_DEGREES * 0.15)
        self.left_leg.rotation_x = swing
        self.right_leg.rotation_x = -swing
        self.left_arm.rotation_x = -swing * 0.7
        self.right_arm.rotation_x = swing * 0.7

    def _reset(self) -> None:
        start = self._route[0]
        self.position = (start.x, start.y, start.z)
        self.rotation_x = 0
        self.waypoint_index = 1 if len(self._route) > 1 else 0
        self._state = STATE_PATROL
        self._cover_target = None
        self._cover_left = 0.0
        self._pose_gait(0.0, moving=False)

    def _phys_position(self) -> PhysVec3:
        return PhysVec3(float(self.x), float(self.y), float(self.z))


def spawn_mannequins(settlement: Settlement) -> list[RangeMannequin]:
    """One loop per hamlet plus a cross-lane walk at ~400 m for lead practice."""
    routes = (
        (
            PhysVec3(-58.0, 0.0, 136.0),
            PhysVec3(-44.0, 0.0, 146.0),
            PhysVec3(-52.0, 0.0, 160.0),
            PhysVec3(-70.0, 0.0, 148.0),
        ),
        (
            PhysVec3(48.0, 0.0, 338.0),
            PhysVec3(62.0, 0.0, 342.0),
            PhysVec3(60.0, 0.0, 352.0),
            PhysVec3(46.0, 0.0, 346.0),
        ),
        (
            PhysVec3(-100.0, 0.0, 548.0),
            PhysVec3(-88.0, 0.0, 540.0),
            PhysVec3(-98.0, 0.0, 532.0),
            PhysVec3(-112.0, 0.0, 542.0),
        ),
        (
            PhysVec3(-35.0, 0.0, 392.0),
            PhysVec3(20.0, 0.0, 408.0),
            PhysVec3(85.0, 0.0, 394.0),
            PhysVec3(20.0, 0.0, 385.0),
        ),
    )
    return [RangeMannequin(route, settlement.cover_points) for route in routes]


def _turn_towards(current: float, target: float, max_degrees: float) -> float:
    """Rotate the short way, then clamp so a 180° snap cannot pop the mesh."""
    delta = (target - current + 180.0) % 360.0 - 180.0
    if abs(delta) <= max_degrees:
        return current + delta
    return current + copysign(max_degrees, delta)

