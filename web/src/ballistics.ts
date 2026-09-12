/** Engine-free projectile integration: gravity drop plus constant wind accel. */

export class Vec3 {
  constructor(
    public x: number,
    public y: number,
    public z: number,
  ) {}

  add(other: Vec3): Vec3 {
    return new Vec3(this.x + other.x, this.y + other.y, this.z + other.z);
  }

  sub(other: Vec3): Vec3 {
    return new Vec3(this.x - other.x, this.y - other.y, this.z - other.z);
  }

  mul(scalar: number): Vec3 {
    return new Vec3(this.x * scalar, this.y * scalar, this.z * scalar);
  }

  length(): number {
    return Math.hypot(this.x, this.y, this.z);
  }

  normalized(): Vec3 {
    const magnitude = this.length();
    if (magnitude === 0.0) {
      return new Vec3(0.0, 0.0, 0.0);
    }
    return this.mul(1.0 / magnitude);
  }

  asTuple(): [number, number, number] {
    return [this.x, this.y, this.z];
  }
}

export function initialVelocity(direction: Vec3, muzzleSpeed: number): Vec3 {
  return direction.normalized().mul(muzzleSpeed);
}

export function step(
  position: Vec3,
  velocity: Vec3,
  wind: Vec3,
  dt: number,
  gravity = 9.81,
): [Vec3, Vec3] {
  if (dt <= 0.0) {
    return [position, velocity];
  }

  const acceleration = new Vec3(wind.x, wind.y - gravity, wind.z);
  const newVelocity = velocity.add(acceleration.mul(dt));
  const newPosition = position.add(newVelocity.mul(dt));
  return [newPosition, newVelocity];
}

export function integrate(
  position: Vec3,
  velocity: Vec3,
  wind: Vec3,
  duration: number,
  dt: number,
  gravity = 9.81,
): [Vec3, Vec3] {
  let elapsed = 0.0;
  let pos = position;
  let vel = velocity;
  while (elapsed < duration) {
    const stepDt = elapsed + dt <= duration ? dt : duration - elapsed;
    [pos, vel] = step(pos, vel, wind, stepDt, gravity);
    elapsed += stepDt;
  }
  return [pos, vel];
}
