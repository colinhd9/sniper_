/** SR-500 loadout: zoom steps, fire, hip spread, and a small view model. */

import {
  BoxGeometry,
  Color,
  Group,
  Mesh,
  MeshLambertMaterial,
  Vector3,
} from "three";

import { Vec3 } from "./ballistics";
import {
  AIM_SPREAD_DEGREES,
  HIP_FOV,
  HIP_SPREAD_DEGREES,
  MUZZLE_VELOCITY,
  RECOIL_DEGREES,
  SCOPE_BLEND_SECONDS,
  SHOT_COOLDOWN,
  WEAPON_MODE,
  WEAPON_NAME,
  ZOOM_FOVS,
} from "./config";
import type { Game } from "./game";
import { spawnProjectile } from "./projectile";

const STEEL = new Color(0.16, 0.16, 0.15);
const BLUED = new Color(0.22, 0.22, 0.2);

export class Weapon {
  readonly name = WEAPON_NAME;
  readonly modeLabel = WEAPON_MODE;
  readonly zoomFovs = ZOOM_FOVS;
  zoomIndex = 0;
  private cooldownLeft = 0;
  private readonly view: Group;
  private fov = HIP_FOV;
  private readonly muzzle = new Vector3();
  private readonly forward = new Vector3();
  private readonly right = new Vector3();
  private readonly up = new Vector3();

  constructor(private readonly game: Game) {
    this.view = buildRifle();
    this.view.visible = false;
    game.camera.add(this.view);
  }

  get currentFov(): number {
    if (!this.game.player.scoped) {
      return HIP_FOV;
    }
    return this.zoomFovs[Math.min(this.zoomIndex, this.zoomFovs.length - 1)];
  }

  get magnification(): number {
    return HIP_FOV / this.currentFov;
  }

  nudgeZoom(delta: number): void {
    const last = this.zoomFovs.length - 1;
    this.zoomIndex = Math.max(0, Math.min(last, this.zoomIndex + delta));
    this.game.hud.refreshWeapon();
  }

  update(dt: number): void {
    this.cooldownLeft = Math.max(0, this.cooldownLeft - dt);
    const target = this.currentFov;
    const k = 1 - Math.exp(-dt / Math.max(SCOPE_BLEND_SECONDS, 1e-4));
    this.fov += (target - this.fov) * k;
    this.game.camera.fov = this.fov;
    this.game.camera.updateProjectionMatrix();
    this.view.visible = !this.game.player.scoped && this.game.player.enabled && !this.game.paused;
  }

  fire(): void {
    if (this.cooldownLeft > 0 || this.game.paused || !this.game.player.enabled) {
      return;
    }
    this.cooldownLeft = SHOT_COOLDOWN;
    const spread = this.game.player.scoped ? AIM_SPREAD_DEGREES : HIP_SPREAD_DEGREES;
    this.game.camera.getWorldDirection(this.forward);
    this.right.crossVectors(this.forward, this.game.camera.up).normalize();
    this.up.crossVectors(this.right, this.forward).normalize();
    this.game.camera.getWorldPosition(this.muzzle);
    this.muzzle.addScaledVector(this.forward, 0.45);
    const direction = spreadDirection(this.forward, this.right, this.up, spread);
    this.game.player.addRecoil(RECOIL_DEGREES);
    spawnProjectile(
      this.game,
      new Vec3(this.muzzle.x, this.muzzle.y, this.muzzle.z),
      direction,
      MUZZLE_VELOCITY,
    );
    this.game.hud.playShotFeedback();
  }
}

function spreadDirection(
  forward: Vector3,
  right: Vector3,
  up: Vector3,
  spreadDegrees: number,
): Vec3 {
  if (spreadDegrees <= 0) {
    return new Vec3(forward.x, forward.y, forward.z);
  }
  const radius = (spreadDegrees * Math.PI) / 180 * Math.sqrt(Math.random());
  const yaw = Math.random() * Math.PI * 2;
  const ox = Math.cos(yaw) * radius;
  const oy = Math.sin(yaw) * radius;
  const x = forward.x + right.x * ox + up.x * oy;
  const y = forward.y + right.y * ox + up.y * oy;
  const z = forward.z + right.z * ox + up.z * oy;
  return new Vec3(x, y, z).normalized();
}

function buildRifle(): Group {
  const root = new Group();
  root.position.set(0.28, -0.22, -0.55);
  root.rotation.set(-0.04, -0.1, 0.04);
  root.scale.setScalar(0.55);
  part(root, [0.03, 0.04, 0.42], [0, 0, -0.05], STEEL);
  part(root, [0.016, 0.016, 0.28], [0, 0.014, -0.32], BLUED);
  part(root, [0.022, 0.022, 0.12], [0, 0.03, -0.08], STEEL);
  return root;
}

function part(
  root: Group,
  scale: [number, number, number],
  position: [number, number, number],
  color: Color,
): void {
  const mesh = new Mesh(new BoxGeometry(...scale), new MeshLambertMaterial({ color }));
  mesh.position.set(...position);
  root.add(mesh);
}
