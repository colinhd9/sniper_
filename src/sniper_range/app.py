"""Wire the Ursina window, sandbox systems, pause, and the editor camera."""

from __future__ import annotations

from math import cos, pi, sin
from random import uniform

from ursina import (
    EditorCamera,
    Entity,
    Ursina,
    application,
    camera,
    color,
    mouse,
    window,
)

from sniper_range import config
from sniper_range.ballistics import Vec3 as PhysVec3
from sniper_range.graphics import glsl_version, shaders_usable, use_fixed_function_pipeline
from sniper_range.buildings import build_settlement
from sniper_range.hud import HUD
from sniper_range.humans import spawn_mannequins
from sniper_range.player import SniperController
from sniper_range.targets import spawn_targets
from sniper_range.weapon import Weapon
from sniper_range.world import build_world


def random_wind() -> PhysVec3:
    """One constant wind vector per session. Angle 0 = Nord (+Z)."""
    angle = uniform(0.0, 2.0 * pi)
    strength = uniform(config.WIND_ACCEL_MIN, config.WIND_ACCEL_MAX)
    return PhysVec3(sin(angle) * strength, 0.0, cos(angle) * strength)


class Game:
    def __init__(self) -> None:
        self.shaders_enabled = shaders_usable()
        if not self.shaders_enabled:
            use_fixed_function_pipeline()
        # Ursina sizes the UI lens only when Panda3D emits 'aspectRatioChanged'.
        # Until that fires the lens keeps its 1x1 default, which blows every
        # camera.ui child up 20x and pushes the HUD off screen. Apply it now.
        window.update_aspect_ratio()
        # region agent log
        from sniper_range._debug_log import dlog
        dlog(
            "A",
            "app.py:Game.__init__",
            "render path selected",
            shaders_enabled=self.shaders_enabled,
            glsl_version=glsl_version(),
        )
        # endregion
        self.wind = random_wind()
        self.ground = build_world()
        self.settlement = build_settlement()
        self.targets = spawn_targets()
        self.mannequins = spawn_mannequins(self.settlement)
        self.player = SniperController(self)
        camera.fov = config.HIP_FOV
        camera.clip_plane_near = config.CAMERA_NEAR
        camera.clip_plane_far = config.CAMERA_FAR
        self.hud = HUD(self)
        self.weapon = Weapon(self)
        self.editor_camera = EditorCamera(enabled=False, ignore_paused=True)
        self.projectile_ignore = [self.player, *self.weapon.parts]
        # region agent log
        from sniper_range._debug_log import dlog, gsg_report
        dlog(
            "E",
            "app.py:Game.__init__",
            "game ready",
            player_pos=self.player.position,
            camera_world_pos=camera.world_position,
            camera_forward=camera.forward,
            camera_fov=camera.fov,
            paused=application.paused,
            mouse_locked=mouse.locked,
            targets=len(self.targets),
            nearest_target=self.targets[0].world_position,
            **gsg_report(),
        )
        # endregion

    def update(self) -> None:
        self.weapon.update()
        self.hud.update()

    def input(self, key: str) -> None:
        if key == config.KEY_EDITOR:
            self.toggle_editor()
            return
        self.weapon.input(key)

    def toggle_pause(self) -> None:
        if self.editor_camera.enabled:
            return
        application.paused = not application.paused
        mouse.locked = not application.paused

    def toggle_editor(self) -> None:
        entering = not self.editor_camera.enabled
        if entering:
            # Disable the controller first so it stores a valid camera
            # transform and releases the parent. Enabling the editor camera
            # afterwards lets it claim camera.parent and keep a non-zero
            # target_z so scroll zoom works.
            self.player.enabled = False
            pos = self.player.position
            self.editor_camera.position = (
                float(pos.x),
                float(pos.y) + config.EDITOR_HEIGHT,
                float(pos.z),
            )
            self.editor_camera.rotation_x = config.EDITOR_PITCH
            self.editor_camera.rotation_y = float(self.player.rotation_y)
            camera.editor_position = (0.0, 0.0, -config.EDITOR_ZOOM_DISTANCE)
            camera.fov = config.HIP_FOV
            self.editor_camera.enabled = True
            self.weapon.set_view_visible(False)
            self.hud.set_overlays_visible(False)
            mouse.locked = False
            application.paused = True
            return

        self.editor_camera.enabled = False
        self.player.enabled = True
        camera.fov = self.weapon.current_fov
        self.weapon.set_view_visible(True)
        self.hud.set_overlays_visible(True)
        mouse.locked = True
        application.paused = False

    def report_impact(self, *, hit: bool, distance: float, point, label: str = "") -> None:
        self.hud.show_impact(hit=hit, distance=distance, label=label)
        _ = point

    def notify_impact(self, point) -> None:
        for mannequin in self.mannequins:
            mannequin.alert_to(point)


class GameTicker(Entity):
    """Keeps receiving Escape while the simulation is paused."""

    def __init__(self, game: Game) -> None:
        super().__init__(ignore_paused=True)
        self.game = game

    def update(self) -> None:
        if application.paused:
            return
        self.game.update()

    def input(self, key: str) -> None:
        if key == config.KEY_PAUSE:
            self.game.toggle_pause()
            return
        if key == config.KEY_EDITOR:
            self.game.toggle_editor()
            return
        if application.paused:
            return
        self.game.input(key)


def run_game() -> None:
    app = Ursina(title="Sniper Range", borderless=False, fullscreen=False, vsync=True)
    window.color = color.rgb(0.62, 0.7, 0.76)
    game = Game()
    GameTicker(game)
    app.run()
