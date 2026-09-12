"""Loadout manager: weapon swap, zoom steps, fire, and view-model visibility."""

from __future__ import annotations

from math import cos, pi, radians, sin, sqrt
from random import random, uniform
from typing import TYPE_CHECKING

from ursina import Vec3, camera, held_keys, time

from sniper_range import config
from sniper_range.projectile import spawn_projectile
from sniper_range.weapons import LOADOUT, WeaponSpec, build_ak_model, build_sniper_model

if TYPE_CHECKING:
    from sniper_range.app import Game

_BUILDERS = {
    "SR-500": build_sniper_model,
    "AK-47": build_ak_model,
}


class Weapon:
    def __init__(self, game: Game) -> None:
        self.game = game
        self.specs = LOADOUT
        self.models = {}
        self.parts: list = []
        self.active_index = 0
        self.zoom_index = 0
        self.cooldown_left = 0.0
        self._view_allowed = True

        for spec in self.specs:
            root, parts = _BUILDERS[spec.name]()
            self.models[spec.name] = root
            self.parts.extend(parts)
            root.enabled = spec is self.specs[0]

        # region agent log
        from sniper_range._debug_log import dlog

        active = self.models[self.spec.name]
        dlog(
            "J",
            "weapon.py:Weapon.__init__",
            "rifle scale chain",
            rifle_scale=active.scale,
            rifle_world_scale=active.world_scale,
            rifle_world_pos=active.world_position,
            camera_world_scale=camera.world_scale,
            camera_parent=type(camera.parent).__name__,
            camera_parent_world_scale=getattr(camera.parent, "world_scale", None),
            player_world_scale=game.player.world_scale,
        )
        # endregion
        self.game.hud.refresh_weapon(self)

    @property
    def spec(self) -> WeaponSpec:
        return self.specs[self.active_index]

    @property
    def current_fov(self) -> float:
        if not self.game.player.scoped:
            return config.HIP_FOV
        fovs = self.spec.zoom_fovs
        return fovs[min(self.zoom_index, len(fovs) - 1)]

    @property
    def magnification(self) -> float:
        return config.HIP_FOV / self.current_fov

    def set_view_visible(self, visible: bool) -> None:
        self._view_allowed = visible
        self._refresh_model_visibility()

    def select(self, index: int) -> None:
        index = index % len(self.specs)
        if index == self.active_index:
            return
        self.active_index = index
        self.zoom_index = 0
        self.cooldown_left = 0.0
        if self.game.player.scoped:
            self._apply_fov()
            self.game.hud.set_scoped(True, use_overlay=self.spec.scope_overlay)
        self._refresh_model_visibility()
        self.game.hud.refresh_weapon()

    def update(self) -> None:
        if self.cooldown_left > 0.0:
            self.cooldown_left = max(0.0, self.cooldown_left - time.dt)
        self._sync_scope(held_keys[config.KEY_SCOPE])
        if self.spec.automatic and held_keys[config.KEY_FIRE]:
            self.fire()

    def input(self, key: str) -> None:
        for index, spec in enumerate(self.specs):
            if key == spec.select_key:
                self.select(index)
                return
        if key == "scroll up":
            if self.game.player.scoped:
                self._nudge_zoom(1)
            else:
                self.select(self.active_index + 1)
            return
        if key == "scroll down":
            if self.game.player.scoped:
                self._nudge_zoom(-1)
            else:
                self.select(self.active_index - 1)
            return
        if key == f"{config.KEY_FIRE} down":
            self.fire()

    def _nudge_zoom(self, delta: int) -> None:
        last = len(self.spec.zoom_fovs) - 1
        self.zoom_index = max(0, min(last, self.zoom_index + delta))
        if self.game.player.scoped:
            self._apply_fov()
        self.game.hud.refresh_weapon()

    def _sync_scope(self, scoped: bool) -> None:
        if scoped == self.game.player.scoped:
            self._refresh_model_visibility()
            return

        self.game.player.scoped = scoped
        self._refresh_model_visibility()
        self._apply_fov()
        self.game.hud.set_scoped(scoped, use_overlay=self.spec.scope_overlay)

    def _apply_fov(self) -> None:
        camera.animate("fov", self.current_fov, duration=config.SCOPE_BLEND_SECONDS)

    def _refresh_model_visibility(self) -> None:
        scoped = self.game.player.scoped
        for name, model in self.models.items():
            model.enabled = self._view_allowed and name == self.spec.name and not scoped

    def fire(self) -> None:
        if self.cooldown_left > 0.0:
            return
        if not getattr(self.game.player, "enabled", True):
            return

        spec = self.spec
        self.cooldown_left = spec.shot_cooldown
        spread = spec.aim_spread_degrees if self.game.player.scoped else spec.hip_spread_degrees
        origin = camera.world_position + camera.forward * 0.45
        direction = _spread_direction(Vec3(*camera.forward), camera.right, camera.up, spread)
        self.game.player.add_recoil(spec.recoil_degrees)
        spawn_projectile(self.game, origin, direction, spec.muzzle_velocity)
        self.game.hud.play_shot_feedback()


def _spread_direction(forward: Vec3, right: Vec3, up: Vec3, spread_degrees: float) -> Vec3:
    """Offset aim inside a cone. Radius is uniform on the disk so the center is not favored."""
    if spread_degrees <= 0.0:
        return Vec3(*forward)
    radius = radians(spread_degrees) * sqrt(random())
    yaw = uniform(0.0, 2.0 * pi)
    offset = right * (cos(yaw) * radius) + up * (sin(yaw) * radius)
    return (forward + offset).normalized()
