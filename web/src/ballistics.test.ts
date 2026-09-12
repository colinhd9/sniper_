import { describe, expect, it } from "vitest";

import { Vec3, initialVelocity, integrate, step } from "./ballistics";

const DT = 1.0 / 240.0;
const G = 9.81;

describe("ballistics", () => {
  it("moves in a straight line when forces are zero", () => {
    const start = new Vec3(0.0, 10.0, 0.0);
    const velocity = new Vec3(0.0, 0.0, 100.0);
    const wind = new Vec3(0.0, 0.0, 0.0);

    const [end, endVel] = integrate(start, velocity, wind, 2.0, DT, 0.0);

    expect(end.x).toBeCloseTo(0.0, 5);
    expect(end.y).toBeCloseTo(10.0, 5);
    expect(end.z).toBeCloseTo(200.0, 2);
    expect(endVel.asTuple()).toEqual(velocity.asTuple());
  });

  it("drops close to half g t squared", () => {
    const start = new Vec3(0.0, 0.0, 0.0);
    const velocity = new Vec3(0.0, 0.0, 500.0);
    const wind = new Vec3(0.0, 0.0, 0.0);

    const [end] = integrate(start, velocity, wind, 1.0, DT, G);

    const analyticDrop = 0.5 * G * 1.0 * 1.0;
    expect(end.z).toBeCloseTo(500.0, 1);
    expect(end.y).toBeCloseTo(-analyticDrop, 1);
  });

  it("drifts laterally with wind", () => {
    const start = new Vec3(0.0, 0.0, 0.0);
    const velocity = new Vec3(0.0, 0.0, 500.0);
    const wind = new Vec3(4.0, 0.0, 0.0);
    const duration = 0.8;

    const [end] = integrate(start, velocity, wind, duration, DT, 0.0);

    const analyticDrift = 0.5 * 4.0 * duration * duration;
    expect(end.x).toBeCloseTo(analyticDrift, 1);
    expect(end.z).toBeCloseTo(400.0, 1);
    expect(end.y).toBeCloseTo(0.0, 5);
  });

  it("drops more at longer flight times", () => {
    const start = new Vec3(0.0, 0.0, 0.0);
    const velocity = new Vec3(0.0, 0.0, 500.0);
    const wind = new Vec3(0.0, 0.0, 0.0);

    const [near] = integrate(start, velocity, wind, 0.2, DT, G);
    const [far] = integrate(start, velocity, wind, 1.0, DT, G);

    expect(far.z).toBeGreaterThan(near.z);
    expect(far.y).toBeLessThan(near.y);
  });

  it("scales initial velocity to muzzle speed", () => {
    const velocity = initialVelocity(new Vec3(0.0, 1.0, 1.0), 500.0);
    expect(velocity.length()).toBeCloseTo(500.0, 5);
    expect(velocity.y).toBeCloseTo(velocity.z, 5);
  });

  it("ignores non-positive dt", () => {
    const pos = new Vec3(1.0, 2.0, 3.0);
    const vel = new Vec3(4.0, 5.0, 6.0);
    const wind = new Vec3(1.0, 0.0, 1.0);

    expect(step(pos, vel, wind, 0.0, G)).toEqual([pos, vel]);
    expect(step(pos, vel, wind, -0.1, G)).toEqual([pos, vel]);
  });

  it("covers horizontal distance in distance/speed seconds", () => {
    const speed = 500.0;
    const distance = 400.0;
    const duration = distance / speed;
    const start = new Vec3(0.0, 1.7, 0.0);
    const velocity = initialVelocity(new Vec3(0.0, 0.0, 1.0), speed);

    const [end] = integrate(start, velocity, new Vec3(0.0, 0.0, 0.0), duration, DT, G);

    expect(end.z).toBeCloseTo(distance, 0);
    const expectedDrop = 0.5 * G * duration * duration;
    expect(start.y - end.y).toBeCloseTo(expectedDrop, 1);
    expect(Math.sqrt(end.x ** 2)).toBeCloseTo(0.0, 5);
  });
});
