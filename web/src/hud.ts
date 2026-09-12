/** Scope overlay, rangefinder, wind rose, and impact text. */

import { Raycaster, Vector3 } from "three";

import { Vec3 } from "./ballistics";
import { RANGEFINDER_MAX, WEAPON_MODE, WEAPON_NAME } from "./config";
import type { Game } from "./game";
import "./hud.css";

const COMPASS_LABELS = [
  "Nord",
  "Nordost",
  "Ost",
  "Südost",
  "Süd",
  "Südwest",
  "West",
  "Nordwest",
] as const;

const _origin = new Vector3();
const _forward = new Vector3();
const _right = new Vector3();
const raycaster = new Raycaster();

export class HUD {
  private readonly root: HTMLDivElement;
  private readonly pause: HTMLDivElement;
  private readonly range: HTMLDivElement;
  private readonly wind: HTMLDivElement;
  private readonly impact: HTMLDivElement;
  private readonly weapon: HTMLDivElement;
  private readonly scope: HTMLDivElement;
  private readonly crosshair: HTMLDivElement;
  private rangefinderHeld = false;

  constructor(private readonly game: Game) {
    this.root = document.createElement("div");
    this.root.className = "hud";
    this.root.innerHTML = `
      <div class="hud-scope" hidden></div>
      <div class="hud-crosshair"></div>
      <div class="hud-wind"></div>
      <div class="hud-range" hidden></div>
      <div class="hud-impact" hidden></div>
      <div class="hud-weapon"></div>
      <p class="hud-help">WASD bewegen · Shift sprinten · C ducken · RMB Visier · Mausrad Zoom · LMB Schuss · R Entfernung · Esc Pause</p>
      <div class="hud-pause">
        <p class="hud-pause-kicker">Sniper Range</p>
        <h1>Klicken zum Spielen</h1>
        <p>Die Maus wird gesperrt. Esc gibt sie wieder frei.</p>
        <a href="/sniper/">Zur Projektseite</a>
      </div>
    `;
    document.body.append(this.root);
    this.scope = this.root.querySelector(".hud-scope") as HTMLDivElement;
    this.crosshair = this.root.querySelector(".hud-crosshair") as HTMLDivElement;
    this.wind = this.root.querySelector(".hud-wind") as HTMLDivElement;
    this.range = this.root.querySelector(".hud-range") as HTMLDivElement;
    this.impact = this.root.querySelector(".hud-impact") as HTMLDivElement;
    this.weapon = this.root.querySelector(".hud-weapon") as HTMLDivElement;
    this.pause = this.root.querySelector(".hud-pause") as HTMLDivElement;
    this.refreshWeapon();
    this.setPaused(true);
  }

  setRangefinder(held: boolean): void {
    this.rangefinderHeld = held;
  }

  setPaused(paused: boolean): void {
    this.pause.hidden = !paused;
  }

  setScoped(scoped: boolean): void {
    this.scope.hidden = !scoped;
    this.crosshair.hidden = scoped;
    this.refreshWeapon();
  }

  playShotFeedback(): void {
    this.impact.hidden = true;
  }

  showImpact(hit: boolean, distance: number, label: string): void {
    if (hit) {
      const name = label || "Treffer";
      this.impact.textContent = `${name}  ·  ${distance.toFixed(0)} m`;
      this.impact.classList.toggle("hud-impact-miss", false);
    } else {
      this.impact.textContent = `Daneben  ·  Einschlag ${distance.toFixed(0)} m`;
      this.impact.classList.toggle("hud-impact-miss", true);
    }
    this.impact.hidden = false;
  }

  refreshWeapon(): void {
    if (this.game.player.scoped) {
      this.weapon.textContent = `${WEAPON_NAME}  ·  ${this.game.weapon.magnification.toFixed(0)}x`;
      return;
    }
    this.weapon.textContent = `${WEAPON_NAME}  ·  ${WEAPON_MODE}`;
  }

  update(): void {
    this.refreshWind();
    this.refreshRangefinder();
    this.refreshWeapon();
  }

  private refreshWind(): void {
    const wind = this.game.wind;
    const strength = new Vec3(wind.x, 0, wind.z).length();
    const heading = compassLabel(wind.x, wind.z);
    _right.setFromMatrixColumn(this.game.camera.matrixWorld, 0);
    _right.y = 0;
    if (_right.lengthSq() > 0) {
      _right.normalize();
    }
    const side = windSide(wind, _right);
    this.wind.textContent = `Wind  ${strength.toFixed(1)} m/s²  ${heading}\nzieht ${side}`;
  }

  private refreshRangefinder(): void {
    this.range.hidden = !this.rangefinderHeld;
    if (!this.rangefinderHeld) {
      return;
    }
    this.game.camera.getWorldPosition(_origin);
    this.game.camera.getWorldDirection(_forward);
    raycaster.far = RANGEFINDER_MAX;
    raycaster.set(_origin, _forward);
    const hits = raycaster.intersectObjects(this.game.colliders, true);
    const hit = hits.find((entry) => !this.game.projectileIgnore.includes(entry.object));
    this.range.textContent = hit !== undefined ? `${hit.distance.toFixed(0)} m` : "kein Ziel";
  }
}

export function compassLabel(x: number, z: number): string {
  if (x === 0 && z === 0) {
    return "—";
  }
  const angle = (Math.atan2(x, z) * 180) / Math.PI;
  const index = Math.floor((((angle + 360 + 22.5) % 360) / 45) | 0);
  return COMPASS_LABELS[index];
}

function windSide(wind: Vec3, cameraRight: Vector3): string {
  const lateral = wind.x * cameraRight.x + wind.z * cameraRight.z;
  if (Math.abs(lateral) < 0.35) {
    return "kaum seitlich";
  }
  return lateral > 0 ? "nach rechts" : "nach links";
}
