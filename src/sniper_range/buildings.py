"""Small adobe clusters beside the firing lanes, plus cover points for dummies."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians, sin

from ursina import Entity, Vec3, color

from sniper_range.props import box

ADOBE = color.rgb(0.55, 0.42, 0.3)
RUST = color.rgb(0.35, 0.22, 0.16)
STONE = color.rgb(0.42, 0.39, 0.35)
WOOD = color.rgb(0.32, 0.24, 0.18)

WALL_THICKNESS = 0.28
DOOR_WIDTH = 1.15
POST = 0.22


@dataclass
class Settlement:
    structures: list[Entity] = field(default_factory=list)
    cover_points: list[Vec3] = field(default_factory=list)


def build_settlement() -> Settlement:
    """Place three hamlets off the steel-plate line so lanes stay readable."""
    settlement = Settlement()
    _near_village(settlement)
    _mid_village(settlement)
    _far_post(settlement)
    return settlement


def _near_village(settlement: Settlement) -> None:
    # West of the 120 m / 155 m plates. Courtyard sits between the two huts.
    _hut(settlement, (-62.0, 0.0, 130.0), (6.2, 3.2, 5.0), yaw=32.0)
    _hut(settlement, (-48.0, 0.0, 152.0), (5.6, 3.0, 4.8), yaw=212.0)
    _wall(settlement, (-74.0, 0.0, 140.0), length=16.0, height=2.4, yaw=12.0)
    _add_cover(settlement, (-76.4, 0.0, 140.5))


def _mid_village(settlement: Settlement) -> None:
    # East of the 360 m plate, north of the 300 m berm. Three huts around a yard.
    _hut(settlement, (42.0, 0.0, 332.0), (6.0, 3.2, 5.0), yaw=58.0)
    _hut(settlement, (68.0, 0.0, 338.0), (5.8, 3.1, 4.8), yaw=-81.0)
    _hut(settlement, (54.0, 0.0, 356.0), (5.4, 3.0, 4.6), yaw=176.0)
    _wall(settlement, (55.0, 0.0, 344.0), length=7.0, height=1.6, yaw=8.0)
    _add_cover(settlement, (48.0, 0.0, 348.0))


def _far_post(settlement: Settlement) -> None:
    # West of the 540 m plate, north of the 480 m berm.
    _watchtower(settlement, (-105.0, 0.0, 545.0))
    _shed(settlement, (-92.0, 0.0, 538.0), (5.2, 2.6, 4.0), yaw=200.0)
    _add_cover(settlement, (-105.0, 0.0, 551.0))
    _add_cover(settlement, (-92.0, 0.0, 544.0))


def _hut(
    settlement: Settlement,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    *,
    yaw: float,
) -> None:
    """Four walls, door gap in the local +Z face, flat roof."""
    width, height, depth = size
    cx, cy, cz = center
    side = (width - DOOR_WIDTH) * 0.5
    use_door = side >= 0.55

    _placed_wall(settlement, center, (0.0, 0.0, -depth * 0.5), (width, height, WALL_THICKNESS), yaw)
    _placed_wall(settlement, center, (-width * 0.5, 0.0, 0.0), (WALL_THICKNESS, height, depth), yaw)
    _placed_wall(settlement, center, (width * 0.5, 0.0, 0.0), (WALL_THICKNESS, height, depth), yaw)

    if use_door:
        left_x = -width * 0.5 + side * 0.5
        right_x = width * 0.5 - side * 0.5
        _placed_wall(settlement, center, (left_x, 0.0, depth * 0.5), (side, height, WALL_THICKNESS), yaw)
        _placed_wall(settlement, center, (right_x, 0.0, depth * 0.5), (side, height, WALL_THICKNESS), yaw)
    else:
        _placed_wall(settlement, center, (0.0, 0.0, depth * 0.5), (width, height, WALL_THICKNESS), yaw)

    roof_x, roof_z = _rotate_offset(0.0, 0.0, yaw)
    settlement.structures.append(
        box(
            (cx + roof_x, cy + height, cz + roof_z),
            (width + 0.7, 0.32, depth + 0.7),
            color_value=RUST,
            rotation=(0.0, yaw, 0.0),
        )
    )
    # Door stoop and the hut's lee side, so fleeing dummies have two nearby hides.
    _add_cover(settlement, _world_point(center, (0.0, 0.0, depth * 0.5 + 1.35), yaw))
    _add_cover(settlement, _world_point(center, (0.0, 0.0, -depth * 0.5 - 1.15), yaw))


def _shed(
    settlement: Settlement,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    *,
    yaw: float,
) -> None:
    """Open lean-to: four posts, a back wall, and a pitched roof."""
    width, height, depth = size
    cx, cy, cz = center
    half_w, half_d = width * 0.5, depth * 0.5
    for local in (
        (-half_w, 0.0, -half_d),
        (half_w, 0.0, -half_d),
        (-half_w, 0.0, half_d),
        (half_w, 0.0, half_d),
    ):
        wx, wz = _rotate_offset(local[0], local[2], yaw)
        settlement.structures.append(
            box(
                (cx + wx, cy, cz + wz),
                (POST, height, POST),
                color_value=WOOD,
                texture="white_cube",
                rotation=(0.0, yaw, 0.0),
            )
        )
    _placed_wall(settlement, center, (0.0, 0.0, -half_d), (width, height * 0.9, WALL_THICKNESS), yaw)
    roof_x, roof_z = _rotate_offset(0.0, 0.15, yaw)
    settlement.structures.append(
        box(
            (cx + roof_x, cy + height - 0.05, cz + roof_z),
            (width + 0.8, 0.16, depth + 1.0),
            color_value=RUST,
            rotation=(12.0, yaw, 0.0),
            texture="white_cube",
        )
    )


def _watchtower(settlement: Settlement, center: tuple[float, float, float]) -> None:
    """Tall silhouette: posts, deck, and a low parapet."""
    cx, cy, cz = center
    deck = 8.0
    span = 1.7
    for lx, lz in ((-span, -span), (span, -span), (-span, span), (span, span)):
        settlement.structures.append(
            box(
                (cx + lx, cy, cz + lz),
                (POST, deck, POST),
                color_value=WOOD,
                texture="white_cube",
            )
        )
    settlement.structures.append(
        box((cx, cy + deck, cz), (4.4, 0.22, 4.4), color_value=STONE, texture="white_cube")
    )
    rail_h = 1.15
    for pos, scale in (
        ((cx, cy + deck, cz + 2.05), (4.4, rail_h, 0.16)),
        ((cx, cy + deck, cz - 2.05), (4.4, rail_h, 0.16)),
        ((cx + 2.05, cy + deck, cz), (0.16, rail_h, 4.1)),
        ((cx - 2.05, cy + deck, cz), (0.16, rail_h, 4.1)),
    ):
        settlement.structures.append(box(pos, scale, color_value=ADOBE))
    settlement.structures.append(
        box((cx, cy + deck + rail_h, cz), (3.2, 0.28, 3.2), color_value=RUST)
    )


def _wall(
    settlement: Settlement,
    center: tuple[float, float, float],
    *,
    length: float,
    height: float,
    yaw: float,
) -> None:
    settlement.structures.append(
        box(
            center,
            (length, height, 0.55),
            color_value=STONE,
            texture="white_cube",
            rotation=(0.0, yaw, 0.0),
        )
    )


def _placed_wall(
    settlement: Settlement,
    center: tuple[float, float, float],
    local: tuple[float, float, float],
    scale: tuple[float, float, float],
    yaw: float,
) -> None:
    wx, wz = _rotate_offset(local[0], local[2], yaw)
    settlement.structures.append(
        box(
            (center[0] + wx, center[1] + local[1], center[2] + wz),
            scale,
            color_value=ADOBE,
            rotation=(0.0, yaw, 0.0),
        )
    )


def _add_cover(settlement: Settlement, point: tuple[float, float, float]) -> None:
    settlement.cover_points.append(Vec3(*point))


def _world_point(
    center: tuple[float, float, float],
    local: tuple[float, float, float],
    yaw: float,
) -> tuple[float, float, float]:
    wx, wz = _rotate_offset(local[0], local[2], yaw)
    return (center[0] + wx, center[1] + local[1], center[2] + wz)


def _rotate_offset(x: float, z: float, yaw: float) -> tuple[float, float]:
    """Rotate a local XZ offset by the same yaw Ursina applies to the box."""
    rad = radians(yaw)
    cosine, sine = cos(rad), sin(rad)
    return x * cosine - z * sine, x * sine + z * cosine
