"""Patrol stepping stays engine-free so it can run without Ursina or a GPU."""

import pytest

from sniper_range.ballistics import Vec3
from sniper_range.patrol import advance, heading_between


def test_straight_line_walks_toward_the_next_waypoint() -> None:
    route = (Vec3(0.0, 0.0, 0.0), Vec3(0.0, 0.0, 10.0))
    step = advance(Vec3(0.0, 0.0, 0.0), route, 1, speed=2.0, dt=1.0)

    assert step.position.x == pytest.approx(0.0)
    assert step.position.z == pytest.approx(2.0)
    assert step.heading_degrees == pytest.approx(0.0)
    assert step.waypoint_index == 1


def test_crosses_a_waypoint_inside_one_frame() -> None:
    route = (Vec3(0.0, 0.0, 0.0), Vec3(0.0, 0.0, 3.0), Vec3(4.0, 0.0, 3.0))
    step = advance(Vec3(0.0, 0.0, 0.0), route, 1, speed=5.0, dt=1.0)

    assert step.position.x == pytest.approx(2.0)
    assert step.position.z == pytest.approx(3.0)
    assert step.heading_degrees == pytest.approx(90.0)
    assert step.waypoint_index == 2


def test_loop_wraps_to_the_first_waypoint() -> None:
    route = (Vec3(0.0, 0.0, 0.0), Vec3(0.0, 0.0, 4.0))
    step = advance(Vec3(0.0, 0.0, 0.0), route, 1, speed=6.0, dt=1.0, loop=True)

    assert step.position.x == pytest.approx(0.0)
    assert step.position.z == pytest.approx(2.0)
    assert step.heading_degrees == pytest.approx(180.0)
    assert step.waypoint_index == 0


def test_non_loop_stops_on_the_last_waypoint() -> None:
    route = (Vec3(0.0, 0.0, 0.0), Vec3(0.0, 0.0, 4.0))
    step = advance(Vec3(0.0, 0.0, 0.0), route, 1, speed=10.0, dt=1.0, loop=False)

    assert step.position.z == pytest.approx(4.0)
    assert step.waypoint_index == 1


def test_non_positive_dt_is_a_noop() -> None:
    position = Vec3(1.0, 0.0, 2.0)
    route = (Vec3(0.0, 0.0, 0.0), Vec3(10.0, 0.0, 0.0))

    assert advance(position, route, 1, speed=5.0, dt=0.0).position == position
    assert advance(position, route, 1, speed=5.0, dt=-0.2).position == position


def test_heading_east_is_ninety_degrees() -> None:
    assert heading_between(Vec3(0.0, 0.0, 0.0), Vec3(4.0, 0.0, 0.0)) == pytest.approx(90.0)
