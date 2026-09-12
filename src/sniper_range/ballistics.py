"""Engine-free projectile integration: gravity drop plus constant wind accel."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True, slots=True)
class Vec3:
    """Minimal 3-vector so tests and the game share the same physics types."""

    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vec3:
        return self * scalar

    def length(self) -> float:
        return hypot(self.x, self.y, self.z)

    def normalized(self) -> Vec3:
        magnitude = self.length()
        if magnitude == 0.0:
            return Vec3(0.0, 0.0, 0.0)
        return self * (1.0 / magnitude)

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


def initial_velocity(direction: Vec3, muzzle_speed: float) -> Vec3:
    """Scale a (possibly unnormalized) aim direction to muzzle speed."""
    return direction.normalized() * muzzle_speed


def step(
    position: Vec3,
    velocity: Vec3,
    wind: Vec3,
    dt: float,
    gravity: float = 9.81,
) -> tuple[Vec3, Vec3]:
    """Advance one semi-implicit Euler step.

    Wind is treated as constant acceleration in world space (usually XZ).
    Gravity always pulls toward -Y. Updating velocity first (semi-implicit)
    is a bit more stable than explicit Euler at 60 Hz game ticks.
    """
    if dt <= 0.0:
        return position, velocity

    acceleration = Vec3(wind.x, wind.y - gravity, wind.z)
    new_velocity = velocity + acceleration * dt
    new_position = position + new_velocity * dt
    return new_position, new_velocity


def integrate(
    position: Vec3,
    velocity: Vec3,
    wind: Vec3,
    duration: float,
    dt: float,
    gravity: float = 9.81,
) -> tuple[Vec3, Vec3]:
    """Run `step` for `duration` seconds using a fixed inner `dt`."""
    elapsed = 0.0
    while elapsed < duration:
        step_dt = dt if elapsed + dt <= duration else duration - elapsed
        position, velocity = step(position, velocity, wind, step_dt, gravity)
        elapsed += step_dt
    return position, velocity
