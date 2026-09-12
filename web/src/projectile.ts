/** Visible tracer that integrates ballistics and raycasts to avoid tunneling. */

import {
  BoxGeometry,
  Color,
  Mesh,
  MeshBasicMaterial,
  Raycaster,
  Vector3,
} from "three";

import { Vec3, initialVelocity, step } from "./ballistics";
import {
  GRAVITY,
  IMPACT_MARK_LIFETIME,
  IMPACT_MARK_SCALE,
  PROJECTILE_LIFETIME,
  TRACER_SCALE,
} from "./config";
import type { Game } from "./game";
import type { HitResult, SteelTarget } from "./targets";

const TRACER = new Color(1.0, 0.72, 0.18);
const MARK = new Color(0.12, 0.1, 0.08);

const _from = new Vector3();
const _dir = new Vector3();
const _look = new Vector3();
const raycaster = new Raycaster();

export class Projectile {
  readonly mesh: Mesh;
  private physPosition: Vec3;
  private physVelocity: Vec3;
  private age = 0;
  alive = true;

  constructor(
    private readonly game: Game,
    origin: Vec3,
    direction: Vec3,
    muzzleVelocity: number,
  ) {
    this.mesh = new Mesh(
      new BoxGeometry(TRACER_SCALE[0], TRACER_SCALE[1], TRACER_SCALE[2]),
      new MeshBasicMaterial({ color: TRACER }),
    );
    this.mesh.position.set(origin.x, origin.y, origin.z);
    this.physPosition = origin;
    this.physVelocity = initialVelocity(direction, muzzleVelocity);
    this.orient();
    game.scene.add(this.mesh);
    game.projectileIgnore.push(this.mesh);
  }

  update(dt: number): void {
    if (!this.alive) {
      return;
    }
    this.age += dt;
    if (this.age >= PROJECTILE_LIFETIME) {
      this.destroy();
      return;
    }

    const oldPosition = this.physPosition;
    [this.physPosition, this.physVelocity] = step(
      this.physPosition,
      this.physVelocity,
      this.game.wind,
      dt,
      GRAVITY,
    );
    const travel = this.physPosition.sub(oldPosition);
    const distance = travel.length();
    if (distance > 0) {
      _from.set(oldPosition.x, oldPosition.y, oldPosition.z);
      const n = travel.normalized();
      _dir.set(n.x, n.y, n.z);
      raycaster.far = distance;
      raycaster.set(_from, _dir);
      const hits = raycaster.intersectObjects(this.game.colliders, true);
      const hit = hits.find((entry) => !this.game.projectileIgnore.includes(entry.object));
      if (hit !== undefined) {
        this.impact(hit.point, hit.normal ?? new Vector3(0, 1, 0), hit.object);
        return;
      }
    }

    this.mesh.position.set(this.physPosition.x, this.physPosition.y, this.physPosition.z);
    this.orient();
  }

  private orient(): void {
    if (this.physVelocity.length() <= 0) {
      return;
    }
    _look.set(
      this.mesh.position.x + this.physVelocity.x,
      this.mesh.position.y + this.physVelocity.y,
      this.mesh.position.z + this.physVelocity.z,
    );
    this.mesh.lookAt(_look);
  }

  private impact(point: Vector3, normal: Vector3, object: { userData: { target?: SteelTarget } }): void {
    const playerPos = this.game.player.worldPosition;
    const shotDistance = point.distanceTo(playerPos);
    const target = findTarget(object);
    let result: HitResult | null = null;
    if (target !== undefined) {
      result = target.onBulletHit();
    }
    if (result === null) {
      spawnImpactMark(this.game, point, normal);
    }
    this.game.reportImpact({
      hit: result !== null && result.scored,
      distance: shotDistance,
      label: result?.label ?? "",
    });
    this.destroy();
  }

  private destroy(): void {
    if (!this.alive) {
      return;
    }
    this.alive = false;
    this.game.scene.remove(this.mesh);
    this.mesh.geometry.dispose();
    const ignore = this.game.projectileIgnore;
    const index = ignore.indexOf(this.mesh);
    if (index >= 0) {
      ignore.splice(index, 1);
    }
  }
}

function findTarget(object: { userData: { target?: SteelTarget }; parent?: unknown }): SteelTarget | undefined {
  let current: { userData: { target?: SteelTarget }; parent?: unknown } | null = object;
  while (current !== null) {
    if (current.userData.target !== undefined) {
      return current.userData.target;
    }
    current = (current.parent as typeof current) ?? null;
  }
  return undefined;
}

function spawnImpactMark(game: Game, point: Vector3, normal: Vector3): void {
  const mark = new Mesh(
    new BoxGeometry(IMPACT_MARK_SCALE, IMPACT_MARK_SCALE, IMPACT_MARK_SCALE),
    new MeshBasicMaterial({ color: MARK }),
  );
  const offset = normal.clone().normalize().multiplyScalar(0.04);
  mark.position.copy(point).add(offset);
  game.scene.add(mark);
  window.setTimeout(() => {
    game.scene.remove(mark);
    mark.geometry.dispose();
  }, IMPACT_MARK_LIFETIME * 1000);
}

export function spawnProjectile(
  game: Game,
  origin: Vec3,
  direction: Vec3,
  muzzleVelocity: number,
): Projectile {
  const projectile = new Projectile(game, origin, direction, muzzleVelocity);
  game.projectiles.push(projectile);
  return projectile;
}
