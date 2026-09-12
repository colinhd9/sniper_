/** Tunable gameplay and physics constants. 1 world unit = 1 meter. */

export const HIP_FOV = 80.0;
export const SCOPE_FOV = 16.0;
export const SCOPE_BLEND_SECONDS = 0.14;
export const CAMERA_NEAR = 0.08;
export const CAMERA_FAR = 2500.0;

export const MOVE_SPEED = 5.5;
export const SPRINT_SPEED = 8.5;
export const CROUCH_SPEED = 2.0;
export const SCOPED_MOVE_SPEED = 1.8;
export const HIP_SENSITIVITY: [number, number] = [42.0, 42.0];
export const SCOPE_SENSITIVITY: [number, number] = [11.0, 11.0];
export const PLAYER_HEIGHT = 1.7;
export const CROUCH_HEIGHT = 1.05;
export const CROUCH_BLEND_SECONDS = 0.16;
export const PLAYER_SPAWN: [number, number, number] = [0.0, 3.0, 0.0];
export const RECOIL_RECOVERY = 6.0;
/** Converts Ursina-style sensitivity (deg per ~window fraction) to pointer-lock pixels. */
export const MOUSE_PIXEL_SCALE = 1 / 800;

export const GRAVITY = 9.81;
export const MUZZLE_VELOCITY = 500.0;
export const PROJECTILE_LIFETIME = 4.0;
export const MAX_PHYSICS_DT = 1.0 / 30.0;
export const WIND_ACCEL_MIN = 2.0;
export const WIND_ACCEL_MAX = 5.5;
export const COMPASS_NORTH: [number, number, number] = [0.0, 0.0, 1.0];

export const SHOT_COOLDOWN = 1.15;
export const TRACER_SCALE: [number, number, number] = [0.04, 0.04, 0.55];
export const ZOOM_FOVS: [number, number, number] = [16.0, 8.0, 4.0];
export const HIP_SPREAD_DEGREES = 0.04;
export const AIM_SPREAD_DEGREES = 0.0;
export const RECOIL_DEGREES = 0.35;
export const PLAYER_RADIUS = 0.35;
export const STEP_HEIGHT = 0.6;

export const RANGEFINDER_MAX = 1200.0;

export const IMPACT_MARK_LIFETIME = 22.0;
export const IMPACT_MARK_SCALE = 0.22;

export const TARGET_RESET_SECONDS = 8.0;
export const TARGET_SCALE: [number, number, number] = [0.7, 1.8, 0.12];

export const MAP_SIZE = 1000.0;
export const FOG_RANGE: [number, number] = [180.0, 2400.0];

export const WEAPON_NAME = "SR-500";
export const WEAPON_MODE = "Repetierer";
