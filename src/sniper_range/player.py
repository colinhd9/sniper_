"""First-person controller with sprint, crouch, scoped look speed, and recoil."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Vec2, clamp, held_keys, time
from ursina.prefabs.first_person_controller import FirstPersonController

from sniper_range import config

if TYPE_CHECKING:
    from sniper_range.app import Game


class SniperController(FirstPersonController):
    """FirstPersonController that swaps speed and mouse feel while aiming."""

    def __init__(self, game: Game, **kwargs) -> None:
        self.game = game
        self.scoped = False
        self.crouched = False
        self._recoil = 0.0
        super().__init__(
            height=config.PLAYER_HEIGHT,
            speed=config.MOVE_SPEED,
            mouse_sensitivity=Vec2(*config.HIP_SENSITIVITY),
            position=config.PLAYER_SPAWN,
            **kwargs,
        )
        self.cursor.enabled = False
        self.hip_sensitivity = Vec2(*config.HIP_SENSITIVITY)
        self.scope_sensitivity = Vec2(*config.SCOPE_SENSITIVITY)
        # region agent log
        self._debug_frames = 0
        # endregion

    def on_enable(self) -> None:
        # FirstPersonController.on_enable turns its pink placeholder cursor back
        # on; the HUD owns the crosshair, so keep it hidden.
        super().on_enable()
        self.cursor.enabled = False

    def input(self, key: str) -> None:
        if key == config.KEY_CROUCH:
            self._apply_crouch(not self.crouched)
            return
        super().input(key)

    def add_recoil(self, degrees: float) -> None:
        self._recoil += degrees

    def update(self) -> None:
        # region agent log
        self._debug_frames += 1
        if self._debug_frames % 45 == 1:
            from ursina import mouse
            from sniper_range._debug_log import dlog, gsg_report

            report = gsg_report()
            dlog(
                "BC",
                "player.py:SniperController.update",
                "movement frame sample",
                frame=self._debug_frames,
                position=self.position,
                grounded=self.grounded,
                keys_wasd=[held_keys["w"], held_keys["a"], held_keys["s"], held_keys["d"]],
                mouse_velocity=mouse.velocity,
                mouse_locked=mouse.locked,
                window_foreground=report.get("window_foreground"),
                rotation_y=self.rotation_y,
                camera_pivot_x=self.camera_pivot.rotation_x,
            )
        # endregion
        self._sync_locomotion()
        # Peel last frame's kick off so mouse look edits the true aim point,
        # then put the decaying offset back on. Baking it into rotation_x
        # would climb forever at 600 rounds/min.
        self.camera_pivot.rotation_x += self._recoil
        super().update()
        self._recoil = max(0.0, self._recoil - config.RECOIL_RECOVERY * time.dt)
        self.camera_pivot.rotation_x -= self._recoil
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -90, 90)

    def _sync_locomotion(self) -> None:
        if self.scoped:
            scale = 1.0
            weapon = getattr(self.game, "weapon", None)
            if weapon is not None:
                base_fov = weapon.spec.zoom_fovs[0]
                if base_fov > 0.0:
                    scale = weapon.current_fov / base_fov
            self.mouse_sensitivity = self.scope_sensitivity * scale
            self.speed = config.SCOPED_MOVE_SPEED
        elif self.crouched:
            self.mouse_sensitivity = self.hip_sensitivity
            self.speed = config.CROUCH_SPEED
        elif held_keys[config.KEY_SPRINT]:
            self.mouse_sensitivity = self.hip_sensitivity
            self.speed = config.SPRINT_SPEED
        else:
            self.mouse_sensitivity = self.hip_sensitivity
            self.speed = config.MOVE_SPEED

    def _apply_crouch(self, crouched: bool) -> None:
        self.crouched = crouched
        # Height is read by the ground/head raycasts this frame; the pivot
        # eases so the camera does not pop.
        self.height = config.CROUCH_HEIGHT if crouched else config.PLAYER_HEIGHT
        self.camera_pivot.animate("y", self.height, duration=config.CROUCH_BLEND_SECONDS)
