"""Engine-free waypoint walking so patrol math can be tested without Ursina."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import atan2, degrees, hypot

from sniper_range.ballistics import Vec3

_EPSILON = 1e-6


@dataclass(frozen=True, slots=True)
class PatrolStep:
    position: Vec3
    heading_degrees: float
    waypoint_index: int


def advance(
    position: Vec3,
    route: Sequence[Vec3],
    index: int,
    speed: float,
    dt: float,
    *,
    loop: bool = True,
) -> PatrolStep:
    """Walk along `route` toward `index`, spending leftover distance in-frame.

    `index` is the waypoint currently being approached. When `loop` is true the
    walker wraps to the first point after the last; otherwise it stops there.
    Motion is on the XZ plane; Y is copied from the waypoint being approached.
    """
    if not route:
        return PatrolStep(position, 0.0, 0)

    count = len(route)
    waypoint = _clamp_index(index, count, loop)
    if dt <= 0.0 or speed <= 0.0:
        return PatrolStep(position, heading_between(position, route[waypoint]), waypoint)

    remaining = speed * dt
    current = position
    # A tight loop of zero-length segments would never finish; bound the hops.
    for _ in range(count + 8):
        if remaining <= 0.0:
            break
        target = route[waypoint]
        offset_x = target.x - current.x
        offset_z = target.z - current.z
        distance = hypot(offset_x, offset_z)
        if distance <= _EPSILON:
            if _is_terminal(waypoint, count, loop):
                return PatrolStep(Vec3(target.x, target.y, target.z), heading_between(current, target), waypoint)
            waypoint = _next_index(waypoint, count, loop)
            continue
        if remaining >= distance:
            current = Vec3(target.x, target.y, target.z)
            remaining -= distance
            if _is_terminal(waypoint, count, loop):
                return PatrolStep(current, heading_between(position, target), waypoint)
            waypoint = _next_index(waypoint, count, loop)
            continue
        fraction = remaining / distance
        current = Vec3(
            current.x + offset_x * fraction,
            target.y,
            current.z + offset_z * fraction,
        )
        remaining = 0.0

    return PatrolStep(current, heading_between(current, route[waypoint]), waypoint)


def heading_between(origin: Vec3, target: Vec3) -> float:
    """Yaw in degrees from +Z (north) toward +X (east), matching Ursina `rotation_y`."""
    dx = target.x - origin.x
    dz = target.z - origin.z
    if abs(dx) <= _EPSILON and abs(dz) <= _EPSILON:
        return 0.0
    return degrees(atan2(dx, dz))


def _clamp_index(index: int, count: int, loop: bool) -> int:
    if loop:
        return index % count
    return min(max(index, 0), count - 1)


def _next_index(index: int, count: int, loop: bool) -> int:
    if loop:
        return (index + 1) % count
    return min(index + 1, count - 1)


def _is_terminal(index: int, count: int, loop: bool) -> bool:
    return (not loop and index >= count - 1) or count == 1
