"""Tunable gameplay and physics constants. 1 Ursina unit = 1 meter."""

# Camera
HIP_FOV = 80.0
SCOPE_FOV = 16.0
SCOPE_BLEND_SECONDS = 0.14
CAMERA_NEAR = 0.08
CAMERA_FAR = 2500.0
EDITOR_ZOOM_DISTANCE = 60.0
EDITOR_HEIGHT = 35.0
EDITOR_PITCH = 55.0

# Movement (m/s)
MOVE_SPEED = 5.5
SPRINT_SPEED = 8.5
CROUCH_SPEED = 2.0
SCOPED_MOVE_SPEED = 1.8
HIP_SENSITIVITY = (42.0, 42.0)
SCOPE_SENSITIVITY = (11.0, 11.0)
PLAYER_HEIGHT = 1.7
CROUCH_HEIGHT = 1.05
CROUCH_BLEND_SECONDS = 0.16
PLAYER_SPAWN = (0.0, 3.0, 0.0)
RECOIL_RECOVERY = 6.0

# Ballistics
GRAVITY = 9.81
MUZZLE_VELOCITY = 500.0
PROJECTILE_LIFETIME = 4.0
# Semi-implicit Euler stays stable at typical frame times; clamp huge hitches.
MAX_PHYSICS_DT = 1.0 / 30.0
# Wind is a constant horizontal acceleration (m/s²). At 400 m / 500 m/s
# (t ≈ 0.8 s) a 4 m/s² wind drifts the bullet by ~1.3 m.
WIND_ACCEL_MIN = 2.0
WIND_ACCEL_MAX = 5.5
# World compass used by the HUD: +Z = Nord, +X = Ost.
COMPASS_NORTH = (0.0, 0.0, 1.0)

# Weapon
SHOT_COOLDOWN = 1.15
TRACER_SCALE = (0.04, 0.04, 0.55)

# Rangefinder
RANGEFINDER_MAX = 1200.0

# Impact marks
IMPACT_MARK_LIFETIME = 22.0
IMPACT_MARK_SCALE = 0.22

# Targets
TARGET_RESET_SECONDS = 8.0
TARGET_SCALE = (0.7, 1.8, 0.12)

# Walking range mannequins (m, m/s, deg/s)
MANNEQUIN_WALK_SPEED = 1.4
MANNEQUIN_SPRINT_SPEED = 4.2
MANNEQUIN_TURN_RATE = 220.0
MANNEQUIN_ALERT_RADIUS = 25.0
MANNEQUIN_COVER_SECONDS = 6.0
MANNEQUIN_RESET_SECONDS = 10.0
MANNEQUIN_HEIGHT = 1.8

# World
MAP_SIZE = 1000.0
# Linear fog as (start, fully opaque) in meters. Ursina 8.3 ignores a plain
# float here, which would leave Panda3D's default 0-100 m fog and hide the
# whole map behind a flat wall of fog color.
FOG_RANGE = (180.0, 2400.0)

# Keys (Ursina names)
KEY_SCOPE = "right mouse"
KEY_FIRE = "left mouse"
KEY_RANGEFINDER = "r"
KEY_SPRINT = "shift"
KEY_CROUCH = "c"
KEY_PAUSE = "escape"
KEY_EDITOR = "tab"
