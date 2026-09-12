/** Pointer-lock loop, input, wind, and system wiring. */

import {
  PerspectiveCamera,
  WebGLRenderer,
  type Object3D,
} from "three";

import { Vec3 } from "./ballistics";
import {
  CAMERA_FAR,
  CAMERA_NEAR,
  HIP_FOV,
  MAX_PHYSICS_DT,
  WIND_ACCEL_MAX,
  WIND_ACCEL_MIN,
} from "./config";
import { HUD } from "./hud";
import { Player } from "./player";
import { Projectile } from "./projectile";
import { spawnTargets, type SteelTarget } from "./targets";
import { Weapon } from "./weapon";
import { buildWorld } from "./world";

export class Game {
  readonly renderer: WebGLRenderer;
  readonly camera: PerspectiveCamera;
  readonly scene;
  readonly colliders: Object3D[];
  readonly projectileIgnore: Object3D[] = [];
  readonly projectiles: Projectile[] = [];
  readonly targets: SteelTarget[];
  readonly player: Player;
  readonly weapon: Weapon;
  readonly hud: HUD;
  readonly wind: Vec3;
  paused = true;
  private lastTime = 0;

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setClearColor(0x9eb2c2);
    this.camera = new PerspectiveCamera(
      HIP_FOV,
      window.innerWidth / window.innerHeight,
      CAMERA_NEAR,
      CAMERA_FAR,
    );
    const world = buildWorld();
    this.scene = world.scene;
    this.colliders = world.colliders;
    this.targets = spawnTargets(this.scene);
    for (const target of this.targets) {
      this.colliders.push(target.root);
    }
    this.wind = randomWind();
    this.player = new Player(this.camera);
    this.projectileIgnore.push(this.camera);
    this.weapon = new Weapon(this);
    this.hud = new HUD(this);
    this.bindInput(canvas);
    window.addEventListener("resize", () => this.resize());
  }

  start(): void {
    this.lastTime = performance.now();
    this.renderer.setAnimationLoop((time) => this.tick(time));
  }

  reportImpact(report: { hit: boolean; distance: number; label: string }): void {
    this.hud.showImpact(report.hit, report.distance, report.label);
  }

  private tick(time: number): void {
    const dt = this.frameDt(time);
    if (!this.paused) {
      this.player.update(dt, this.colliders);
      for (const target of this.targets) {
        target.update(dt);
      }
      for (const projectile of this.projectiles) {
        projectile.update(dt);
      }
      this.projectiles.splice(
        0,
        this.projectiles.length,
        ...this.projectiles.filter((item) => item.alive),
      );
    }
    this.weapon.update(dt);
    this.hud.update();
    this.renderer.render(this.scene, this.camera);
  }

  private frameDt(time: number): number {
    const raw = (time - this.lastTime) / 1000;
    this.lastTime = time;
    if (raw <= 0 || raw > 1) {
      return 1 / 60;
    }
    return Math.min(MAX_PHYSICS_DT, raw);
  }

  private bindInput(canvas: HTMLCanvasElement): void {
    const play = (): void => {
      canvas.requestPointerLock();
    };
    canvas.addEventListener("click", play);
    document.addEventListener("click", (event) => {
      const pause = document.querySelector(".hud-pause");
      if (pause !== null && pause.contains(event.target as Node)) {
        if ((event.target as HTMLElement).closest("a")) {
          return;
        }
        play();
      }
    });
    document.addEventListener("pointerlockchange", () => {
      this.paused = document.pointerLockElement !== canvas;
      this.hud.setPaused(this.paused);
      if (this.paused) {
        this.player.scoped = false;
        this.hud.setScoped(false);
      }
    });
    document.addEventListener("mousemove", (event) => {
      if (this.paused) {
        return;
      }
      this.player.look(event.movementX, event.movementY, this);
    });
    document.addEventListener("mousedown", (event) => {
      if (this.paused) {
        return;
      }
      if (event.button === 2) {
        event.preventDefault();
        this.player.scoped = true;
        this.hud.setScoped(true);
      }
      if (event.button === 0) {
        this.weapon.fire();
      }
    });
    document.addEventListener("mouseup", (event) => {
      if (event.button === 2) {
        this.player.scoped = false;
        this.hud.setScoped(false);
      }
    });
    document.addEventListener("contextmenu", (event) => event.preventDefault());
    document.addEventListener(
      "wheel",
      (event) => {
        if (this.paused || !this.player.scoped) {
          return;
        }
        event.preventDefault();
        this.weapon.nudgeZoom(event.deltaY < 0 ? 1 : -1);
      },
      { passive: false },
    );
    document.addEventListener("keydown", (event) => {
      const key = event.key.toLowerCase();
      if (key === " " || key === "tab") {
        event.preventDefault();
      }
      if (this.paused) {
        return;
      }
      if (key === "c" && !event.repeat) {
        this.player.crouched = !this.player.crouched;
      }
      if (key === "r") {
        this.hud.setRangefinder(true);
      }
      this.player.keys.add(key);
    });
    document.addEventListener("keyup", (event) => {
      const key = event.key.toLowerCase();
      this.player.keys.delete(key);
      if (key === "r") {
        this.hud.setRangefinder(false);
      }
    });
  }

  private resize(): void {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }
}

function randomWind(): Vec3 {
  const angle = Math.random() * Math.PI * 2;
  const strength = WIND_ACCEL_MIN + Math.random() * (WIND_ACCEL_MAX - WIND_ACCEL_MIN);
  return new Vec3(Math.sin(angle) * strength, 0.0, Math.cos(angle) * strength);
}
