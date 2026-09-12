/** Steel silhouettes that fall on a hit and stand back up after a delay. */

import {
  BoxGeometry,
  CircleGeometry,
  Color,
  Group,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  type Object3D,
} from "three";

import { TARGET_RESET_SECONDS, TARGET_SCALE } from "./config";

const PLATE = new Color(0.72, 0.28, 0.14);
const WHITE = new Color(0.95, 0.95, 0.9);
const DARK = new Color(0.15, 0.12, 0.12);
const STAND = new Color(0.18, 0.16, 0.14);

const FALL_IN = 0.28;
const FALL_OUT = 0.35;
const FALL_ANGLE = (82 * Math.PI) / 180;

export type HitResult = {
  scored: boolean;
  label: string;
};

type FallState = "up" | "falling" | "down" | "rising";

const PLACEMENTS: Array<[number, number, number]> = [
  [8, 0.0, 80],
  [-18, 0.0, 120],
  [42, 0.0, 155],
  [-55, 0.0, 220],
  [90, 4.0, 300],
  [-20, 0.0, 360],
  [140, 0.0, 420],
  [-110, 5.0, 480],
  [35, 0.0, 540],
  [-70, 0.0, 620],
  [20, 8.0, 700],
];

export class SteelTarget {
  readonly root: Group;
  standing = true;
  private state: FallState = "up";
  private timer = 0;
  private pitch = 0;

  constructor(x: number, y: number, z: number) {
    this.root = new Group();
    this.root.position.set(x, y, z);
    // Face the spawn so the thin plate is readable from the firing point.
    this.root.rotation.y = Math.atan2(x, z);

    const body = new Mesh(
      new BoxGeometry(TARGET_SCALE[0], TARGET_SCALE[1], TARGET_SCALE[2]),
      new MeshBasicMaterial({ color: PLATE }),
    );
    body.position.y = TARGET_SCALE[1] / 2;
    this.root.userData.target = this;
    body.userData.target = this;
    this.root.add(body);

    const bullseye = new Mesh(
      new PlaneGeometry(TARGET_SCALE[0] * 0.45, TARGET_SCALE[1] * 0.28),
      new MeshBasicMaterial({ color: WHITE }),
    );
    bullseye.position.set(0, 0, -TARGET_SCALE[2] / 2 - 0.002);
    body.add(bullseye);

    const center = new Mesh(
      new CircleGeometry(TARGET_SCALE[0] * 0.45 * 0.225, 24),
      new MeshBasicMaterial({ color: DARK }),
    );
    center.position.z = -0.002;
    bullseye.add(center);

    const base = new Mesh(new BoxGeometry(0.8, 0.05, 0.28), new MeshBasicMaterial({ color: STAND }));
    base.position.set(0, 0.025, 0.06);
    this.root.add(base);
  }

  get collider(): Object3D {
    return this.root;
  }

  update(dt: number): void {
    if (this.state === "falling") {
      this.timer += dt;
      const t = Math.min(1, this.timer / FALL_IN);
      this.pitch = FALL_ANGLE * t;
      this.root.rotation.x = this.pitch;
      if (t >= 1) {
        this.state = "down";
        this.timer = 0;
      }
      return;
    }
    if (this.state === "down") {
      this.timer += dt;
      if (this.timer >= TARGET_RESET_SECONDS) {
        this.state = "rising";
        this.timer = 0;
      }
      return;
    }
    if (this.state === "rising") {
      this.timer += dt;
      const t = Math.min(1, this.timer / FALL_OUT);
      this.pitch = FALL_ANGLE * (1 - t);
      this.root.rotation.x = this.pitch;
      if (t >= 1) {
        this.state = "up";
        this.standing = true;
        this.timer = 0;
      }
    }
  }

  onBulletHit(): HitResult | null {
    if (!this.standing) {
      return null;
    }
    this.standing = false;
    this.state = "falling";
    this.timer = 0;
    return { scored: true, label: "Treffer" };
  }
}

export function spawnTargets(parent: Object3D): SteelTarget[] {
  const targets: SteelTarget[] = [];
  for (const [x, y, z] of PLACEMENTS) {
    const target = new SteelTarget(x, y, z);
    parent.add(target.root);
    targets.push(target);
  }
  return targets;
}
