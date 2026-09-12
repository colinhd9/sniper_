"""Ballistics tests stay engine-free so they can run without Ursina or a GPU."""

from math import sqrt

import pytest

from sniper_range.ballistics import Vec3, initial_velocity, integrate, step


DT = 1.0 / 240.0
G = 9.81


def test_zero_forces_move_in_a_straight_line() -> None:
    start = Vec3(0.0, 10.0, 0.0)
    velocity = Vec3(0.0, 0.0, 100.0)
    wind = Vec3(0.0, 0.0, 0.0)
    duration = 2.0

    end, end_vel = integrate(start, velocity, wind, duration, DT, gravity=0.0)

    assert end.x == pytest.approx(0.0, abs=1e-6)
    assert end.y == pytest.approx(10.0, abs=1e-6)
    assert end.z == pytest.approx(200.0, abs=1e-3)
    assert end_vel.as_tuple() == pytest.approx(velocity.as_tuple())


def test_gravity_drops_close_to_half_g_t_squared() -> None:
    start = Vec3(0.0, 0.0, 0.0)
    velocity = Vec3(0.0, 0.0, 500.0)
    wind = Vec3(0.0, 0.0, 0.0)
    duration = 1.0

    end, _ = integrate(start, velocity, wind, duration, DT, gravity=G)

    analytic_drop = 0.5 * G * duration * duration
    assert end.z == pytest.approx(500.0, abs=0.05)
    assert end.y == pytest.approx(-analytic_drop, abs=0.05)


def test_wind_drifts_laterally() -> None:
    start = Vec3(0.0, 0.0, 0.0)
    velocity = Vec3(0.0, 0.0, 500.0)
    wind = Vec3(4.0, 0.0, 0.0)
    duration = 0.8

    end, _ = integrate(start, velocity, wind, duration, DT, gravity=0.0)

    analytic_drift = 0.5 * 4.0 * duration * duration
    assert end.x == pytest.approx(analytic_drift, abs=0.03)
    assert end.z == pytest.approx(400.0, abs=0.05)
    assert end.y == pytest.approx(0.0, abs=1e-6)


def test_drop_grows_with_distance() -> None:
    start = Vec3(0.0, 0.0, 0.0)
    velocity = Vec3(0.0, 0.0, 500.0)
    wind = Vec3(0.0, 0.0, 0.0)

    near, _ = integrate(start, velocity, wind, 0.2, DT, gravity=G)
    far, _ = integrate(start, velocity, wind, 1.0, DT, gravity=G)

    assert far.z > near.z
    assert far.y < near.y


def test_initial_velocity_uses_muzzle_speed() -> None:
    direction = Vec3(0.0, 1.0, 1.0)
    velocity = initial_velocity(direction, 500.0)

    assert velocity.length() == pytest.approx(500.0)
    assert velocity.y == pytest.approx(velocity.z)


def test_step_ignores_non_positive_dt() -> None:
    pos = Vec3(1.0, 2.0, 3.0)
    vel = Vec3(4.0, 5.0, 6.0)
    wind = Vec3(1.0, 0.0, 1.0)

    assert step(pos, vel, wind, 0.0, G) == (pos, vel)
    assert step(pos, vel, wind, -0.1, G) == (pos, vel)


def test_horizontal_range_time_matches_distance_over_speed() -> None:
    speed = 500.0
    distance = 400.0
    duration = distance / speed
    start = Vec3(0.0, 1.7, 0.0)
    velocity = initial_velocity(Vec3(0.0, 0.0, 1.0), speed)

    end, _ = integrate(start, velocity, Vec3(0.0, 0.0, 0.0), duration, DT, G)

    assert end.z == pytest.approx(distance, abs=0.1)
    expected_drop = 0.5 * G * duration * duration
    assert start.y - end.y == pytest.approx(expected_drop, abs=0.05)
    assert sqrt(end.x ** 2) == pytest.approx(0.0, abs=1e-6)
