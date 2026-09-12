/** First-person controller with sprint, crouch, scoped look speed, and recoil. */

import { PerspectiveCamera, Raycaster, Vector3, type Object3D } from "three";

import {
  CROUCH_BLEND_SECONDS,
  CROUCH_HEIGHT,
  CROUCH_SPEED,
  GRAVITY,
  HIP_SENSITIVITY,
  MOUSE_PIXEL_SCALE,
  MOVE_SPEED,
  PLAYER_HEIGHT,
  PLAYER_RADIUS,
  PLAYER_SPAWN,
  RECOIL_RECOVERY,
  SCOPE_SENSITIVITY,
  SCOPED_MOVE_SPEED,
  SPRINT_SPEED,
  STEP_HEIGHT,
} from "./config";
import type { Game } from "./game";

export class Player {
  readonly camera: PerspectiveCamera;
  readonly keys = new Set<string>();
  scoped = false;
  crouched = false;
  enabled = true;
  height = PLAYER_HEIGHT;
  private heightGoal = PLAYER_HEIGHT;
  private yaw = 0;
  private pitch = 0;
  private recoil = 0;
  private verticalVelocity = 0;
  private readonly feet = new Vector3(...PLAYER_SPAWN);
  private readonly raycaster = new Raycaster();
  private readonly down = new Vector3(0, -1, 0);
  private readonly forwardFlat = new Vector3();
  private readonly rightFlat = new Vector3();
  private readonly wish = new Vector3();
  private readonly probeOrigin = new Vector3();
  private readonly probeDir = new Vector3();

  constructor(camera: PerspectiveCamera) {
    this.camera = camera;
    camera.position.copy(this.feet);
    camera.position.y += this.height;
    this.applyView();
  }

  get worldPosition(): Vector3 {
    return this.camera.position;
  }

  addRecoil(degrees: number): void {
    this.recoil += degrees;
  }

  look(movementX: number, movementY: number, game: Game): void {
    const sensitivity = this.scoped
      ? this.scopedSensitivity(game)
      : HIP_SENSITIVITY;
    this.yaw += movementX * sensitivity[0] * MOUSE_PIXEL_SCALE * (Math.PI / 180);
    this.pitch -= movementY * sensitivity[1] * MOUSE_PIXEL_SCALE * (Math.PI / 180);
    const limit = Math.PI / 2 - 0.01;
    this.pitch = Math.min(limit, Math.max(-limit, this.pitch));
  }

  update(dt: number, colliders: Object3D[]): void {
    this.heightGoal = this.crouched ? CROUCH_HEIGHT : PLAYER_HEIGHT;
    const blend = 1 - Math.exp(-dt / Math.max(CROUCH_BLEND_SECONDS, 1e-4));
    this.height += (this.heightGoal - this.height) * blend;

    this.syncLocomotion();
    this.move(dt, colliders);

    this.recoil = Math.max(0, this.recoil - RECOIL_RECOVERY * dt);
    this.applyView();
  }

  private scopedSensitivity(game: Game): [number, number] {
    const baseFov = game.weapon.zoomFovs[0];
    const scale = baseFov > 0 ? game.weapon.currentFov / baseFov : 1;
    return [SCOPE_SENSITIVITY[0] * scale, SCOPE_SENSITIVITY[1] * scale];
  }

  private syncLocomotion(): void {
    if (this.scoped) {
      this.speed = SCOPED_MOVE_SPEED;
    } else if (this.crouched) {
      this.speed = CROUCH_SPEED;
    } else if (this.keys.has("shift")) {
      this.speed = SPRINT_SPEED;
    } else {
      this.speed = MOVE_SPEED;
    }
  }

  private speed = MOVE_SPEED;

  private move(dt: number, colliders: Object3D[]): void {
    this.forwardFlat.set(Math.sin(this.yaw), 0, Math.cos(this.yaw));
    this.rightFlat.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw));

    this.wish.set(0, 0, 0);
    if (this.keys.has("w")) this.wish.add(this.forwardFlat);
    if (this.keys.has("s")) this.wish.sub(this.forwardFlat);
    if (this.keys.has("d")) this.wish.add(this.rightFlat);
    if (this.keys.has("a")) this.wish.sub(this.rightFlat);
    if (this.wish.lengthSq() > 0) {
      this.wish.normalize().multiplyScalar(this.speed * dt);
      this.slide(this.wish, colliders);
    }

    this.verticalVelocity -= GRAVITY * dt;
    this.feet.y += this.verticalVelocity * dt;
    this.ground(colliders);
  }

  private slide(delta: Vector3, colliders: Object3D[]): void {
    const steps: Array<[number, number]> = [
      [delta.x, 0],
      [0, delta.z],
    ];
    for (const [dx, dz] of steps) {
      if (dx === 0 && dz === 0) {
        continue;
      }
      this.probeOrigin.copy(this.feet);
      this.probeOrigin.y += this.height * 0.5;
      this.probeDir.set(dx, 0, dz);
      const distance = this.probeDir.length() + PLAYER_RADIUS;
      this.probeDir.normalize();
      this.raycaster.far = distance;
      this.raycaster.set(this.probeOrigin, this.probeDir);
      const hits = this.raycaster.intersectObjects(colliders, true);
      if (hits.length > 0 && hits[0].distance < PLAYER_RADIUS + 0.05) {
        continue;
      }
      this.feet.x += dx;
      this.feet.z += dz;
    }
  }

  private ground(colliders: Object3D[]): void {
    this.probeOrigin.copy(this.feet);
    this.probeOrigin.y += this.height + 0.4;
    this.raycaster.far = this.height + 2.5;
    this.raycaster.set(this.probeOrigin, this.down);
    const hits = this.raycaster.intersectObjects(colliders, true);
    if (hits.length === 0) {
      return;
    }
    const groundY = hits[0].point.y;
    const gap = this.feet.y - groundY;
    if (gap <= STEP_HEIGHT || this.verticalVelocity <= 0) {
      if (gap < STEP_HEIGHT + 0.05) {
        this.feet.y = groundY;
        this.verticalVelocity = 0;
      }
    }
  }

  private applyView(): void {
    const pitch = this.pitch + (this.recoil * Math.PI) / 180;
    this.camera.position.copy(this.feet);
    this.camera.position.y += this.height;
    // yaw 0 / pitch 0 looks north (+Z). lookAt avoids the default -Z camera.
    const lookX = Math.sin(this.yaw) * Math.cos(pitch);
    const lookY = Math.sin(pitch);
    const lookZ = Math.cos(this.yaw) * Math.cos(pitch);
    this.camera.lookAt(
      this.camera.position.x + lookX,
      this.camera.position.y + lookY,
      this.camera.position.z + lookZ,
    );
  }
}
