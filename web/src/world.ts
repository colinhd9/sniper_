/** Sandbox map: 1000 m ground, ridges, landmarks, fog. 1 unit = 1 meter. */

import {
  AmbientLight,
  BoxGeometry,
  CanvasTexture,
  Color,
  DirectionalLight,
  Fog,
  Mesh,
  MeshLambertMaterial,
  PlaneGeometry,
  RepeatWrapping,
  Scene,
  SRGBColorSpace,
  type Object3D,
} from "three";

import { FOG_RANGE, MAP_SIZE } from "./config";

const FOG_COLOR = new Color(0.62, 0.7, 0.76);
const SKY_COLOR = new Color(0.55, 0.68, 0.8);
const GRASS = new Color(0.55, 0.58, 0.38);
const ROCK = new Color(0.38, 0.36, 0.32);
const STONE = new Color(0.42, 0.39, 0.35);
const ADOBE = new Color(0.55, 0.42, 0.3);
const RUST = new Color(0.35, 0.22, 0.16);

export type WorldBuild = {
  scene: Scene;
  colliders: Object3D[];
};

export function buildWorld(): WorldBuild {
  const scene = new Scene();
  scene.background = SKY_COLOR;
  scene.fog = new Fog(FOG_COLOR, FOG_RANGE[0], FOG_RANGE[1]);

  const colliders: Object3D[] = [];

  const ground = new Mesh(new PlaneGeometry(MAP_SIZE, MAP_SIZE), grassMaterial());
  ground.rotation.x = -Math.PI / 2;
  ground.userData.solid = true;
  scene.add(ground);
  colliders.push(ground);

  addRidges(scene, colliders);
  addLandmarks(scene, colliders);
  addLights(scene);
  return { scene, colliders };
}

function addRidges(scene: Scene, colliders: Object3D[]): void {
  const half = MAP_SIZE * 0.48;
  const height = 28;
  const thickness = 40;
  addBox(scene, colliders, [0, 0, half], [MAP_SIZE, height, thickness], ROCK);
  addBox(scene, colliders, [0, 0, -half], [MAP_SIZE, height, thickness], ROCK);
  addBox(scene, colliders, [half, 0, 0], [thickness, height, MAP_SIZE], ROCK);
  addBox(scene, colliders, [-half, 0, 0], [thickness, height, MAP_SIZE], ROCK);
}

function addLandmarks(scene: Scene, colliders: Object3D[]): void {
  addBox(scene, colliders, [90, 0, 292], [18, 4, 18], STONE);
  addBox(scene, colliders, [78, 0, 286], [10, 1.2, 16], STONE, [0, 18, 0]);
  addBox(scene, colliders, [-110, 0, 470], [16, 5, 14], STONE);
  addBox(scene, colliders, [20, 0, 692], [20, 8, 16], STONE);

  addBox(scene, colliders, [-95, 0, 40], [10, 5.5, 8], ADOBE);
  addBox(scene, colliders, [-92, 5.5, 40], [11, 2.2, 9], RUST);
  addBox(scene, colliders, [36, 0, 70], [14, 2.4, 0.6], STONE);
  addBox(scene, colliders, [150, 0, 400], [6, 22, 6], ADOBE);
  addBox(scene, colliders, [150, 22, 400], [8, 3, 8], RUST);

  const rocks: Array<[[number, number, number], [number, number, number]]> = [
    [[-30, 0, 60], [4, 2.2, 3.5]],
    [[22, 0, 95], [3, 1.6, 2.8]],
    [[-80, 0, 190], [6, 3.4, 5]],
    [[60, 0, 250], [5, 2.8, 4]],
    [[-140, 0, 330], [7, 4, 6]],
    [[180, 0, 510], [8, 5, 7]],
    [[-40, 0, 580], [5, 2.5, 4.5]],
    [[100, 0, 160], [3.5, 1.8, 3]],
  ];
  for (const [pos, scale] of rocks) {
    addBox(scene, colliders, pos, scale, STONE);
  }

  addBox(scene, colliders, [90, 1.2, 278], [8, 0.6, 14], STONE, [18, 0, 0]);
}

function addLights(scene: Scene): void {
  const sun = new DirectionalLight(0xffffff, 1.05);
  // Ursina DirectionalLight.look_at(0.55, -1, -0.35) shines along that vector.
  sun.position.set(-0.55, 1.0, 0.35);
  scene.add(sun);
  scene.add(sun.target);
  scene.add(new AmbientLight(new Color(0.7, 0.72, 0.76), 0.7));
}

/**
 * Cube sitting on the given ground point, matching Ursina `origin_y = -0.5`.
 * Rotation is applied in degrees around that bottom-center pivot.
 */
export function addBox(
  scene: Scene,
  colliders: Object3D[],
  position: [number, number, number],
  scale: [number, number, number],
  color: Color,
  rotationDeg: [number, number, number] = [0, 0, 0],
): Mesh {
  const geometry = new BoxGeometry(scale[0], scale[1], scale[2]);
  geometry.translate(0, scale[1] / 2, 0);
  const mesh = new Mesh(geometry, new MeshLambertMaterial({ color }));
  mesh.position.set(position[0], position[1], position[2]);
  mesh.rotation.set(
    (rotationDeg[0] * Math.PI) / 180,
    (rotationDeg[1] * Math.PI) / 180,
    (rotationDeg[2] * Math.PI) / 180,
  );
  mesh.userData.solid = true;
  scene.add(mesh);
  colliders.push(mesh);
  return mesh;
}

function grassMaterial(): MeshLambertMaterial {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (ctx === null) {
    return new MeshLambertMaterial({ color: GRASS });
  }
  ctx.fillStyle = "#8d945c";
  ctx.fillRect(0, 0, 64, 64);
  for (let i = 0; i < 280; i += 1) {
    ctx.fillStyle = i % 2 === 0 ? "#7a8350" : "#a3ad6e";
    ctx.fillRect(Math.floor(Math.random() * 64), Math.floor(Math.random() * 64), 2, 2);
  }
  const texture = new CanvasTexture(canvas);
  texture.wrapS = RepeatWrapping;
  texture.wrapT = RepeatWrapping;
  texture.repeat.set(64, 64);
  texture.colorSpace = SRGBColorSpace;
  texture.anisotropy = 4;
  return new MeshLambertMaterial({ color: GRASS, map: texture });
}
