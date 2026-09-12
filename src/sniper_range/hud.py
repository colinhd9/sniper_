"""Scope overlay, rangefinder, wind rose, and impact text. No physics here."""

from __future__ import annotations

from math import atan2, degrees
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw
from ursina import Entity, Text, Texture, Vec2, Vec3, camera, color, held_keys, raycast, window

from sniper_range import config
from sniper_range.ballistics import Vec3 as PhysVec3

if TYPE_CHECKING:
    from sniper_range.app import Game


COMPASS_LABELS = (
    "Nord",
    "Nordost",
    "Ost",
    "Südost",
    "Süd",
    "Südwest",
    "West",
    "Nordwest",
)


def compass_label(x: float, z: float) -> str:
    """Map a world XZ vector to a German compass name (+Z = Nord, +X = Ost)."""
    if x == 0.0 and z == 0.0:
        return "—"
    angle = degrees(atan2(x, z))
    index = int((angle + 360.0 + 22.5) % 360.0 // 45.0)
    return COMPASS_LABELS[index]


def make_scope_texture(height: int = 1024) -> Texture:
    """Runtime scope mask: dark frame, clear circle, mil-dot reticle.

    The texture is built at the window's aspect ratio because the overlay quad
    is stretched to cover the screen; a square texture would turn the optic
    circle into an ellipse.
    """
    width = max(height, round(height * window.aspect_ratio))
    image = Image.new("RGBA", (width, height), (0, 0, 0, 240))
    draw = ImageDraw.Draw(image)
    cx, cy = width // 2, height // 2
    radius = int(height * 0.45)
    circle = (cx - radius, cy - radius, cx + radius, cy + radius)

    draw.ellipse(circle, fill=(0, 0, 0, 0))
    # Thin ring so the optic reads as a tube, not just a hole.
    draw.ellipse(circle, outline=(8, 8, 8, 255), width=16)

    reticle = (18, 18, 18, 225)
    draw.line((cx, cy - radius + 20, cx, cy + radius - 20), fill=reticle, width=2)
    draw.line((cx - radius + 20, cy, cx + radius - 20, cy), fill=reticle, width=2)

    # Evenly spaced mil dots. Players learn holdover from impact feedback,
    # not from a printed drop table, so spacing is visual rather than calibrated.
    mil_step = radius / 8
    dot_r = 4
    for i in range(-7, 8):
        if i == 0:
            continue
        offset = int(i * mil_step)
        for px, py in ((cx + offset, cy), (cx, cy + offset)):
            draw.ellipse((px - dot_r, py - dot_r, px + dot_r, py + dot_r), fill=reticle)

    return Texture(image)


class HUD:
    def __init__(self, game: Game) -> None:
        self.game = game
        self.scoped = False

        self.hip_crosshair = Entity(
            parent=camera.ui,
            model="quad",
            color=color.rgba(0.05, 0.05, 0.05, 0.85),
            scale=0.008,
            rotation_z=45,
        )
        self.scope = Entity(
            parent=camera.ui,
            model="quad",
            texture=make_scope_texture(),
            scale=(window.aspect_ratio, 1),
            z=1,
            enabled=False,
        )

        # Ursina's Text.background is sized once from the current string, and
        # clearing it raises an ImportError in 8.3, so dynamic readouts get
        # their own fixed panels instead.
        self.range_panel = _panel((0, -0.18), (0.13, 0.06))
        self.range_text = Text(
            text="",
            parent=camera.ui,
            origin=(0, 0),
            position=(0, -0.18),
            scale=1.1,
            color=color.rgb(0.97, 0.97, 0.92),
            enabled=False,
        )
        # The UI is half a unit tall but aspect_ratio/2 wide, so a fixed x
        # would slide off screen on wide displays.
        wind_corner = window.top_left + Vec2(0.02, -0.02)
        self.wind_panel = _panel(wind_corner, (0.33, 0.085), origin=(-0.5, 0.5))
        self.wind_text = Text(
            text="",
            parent=camera.ui,
            origin=(-0.5, 0.5),
            position=wind_corner + Vec2(0.012, -0.012),
            scale=0.95,
            color=color.rgb(0.97, 0.97, 0.93),
        )
        self.impact_panel = _panel((0, 0.36), (0.42, 0.07), enabled=False)
        self.impact_text = Text(
            text="",
            parent=camera.ui,
            origin=(0, 0),
            position=(0, 0.36),
            scale=1.15,
            color=color.rgb(0.97, 0.95, 0.9),
            enabled=False,
        )
        weapon_corner = window.bottom_right + Vec2(-0.02, 0.08)
        self.weapon_panel = _panel(weapon_corner, (0.28, 0.06), origin=(0.5, -0.5))
        self.weapon_text = Text(
            text="",
            parent=camera.ui,
            origin=(0.5, -0.5),
            position=weapon_corner + Vec2(-0.012, 0.012),
            scale=0.95,
            color=color.rgb(0.97, 0.97, 0.93),
        )
        self.help_text = Text(
            text=(
                "WASD bewegen   Shift sprinten   C ducken   RMB Visier   "
                "Mausrad Zoom   1/2 Waffe   LMB Schuss   R Entfernung   "
                "Esc Pause   Tab Editor"
            ),
            parent=camera.ui,
            origin=(0, -0.5),
            position=(0, -0.47),
            scale=0.62,
            color=color.rgb(0.92, 0.92, 0.88),
        )
        self.help_text.background = True
        # region agent log
        from sniper_range._debug_log import dlog
        dlog(
            "I",
            "hud.py:HUD.__init__",
            "hud geometry state",
            crosshair_scale=self.hip_crosshair.scale,
            crosshair_world_scale=self.hip_crosshair.world_scale,
            crosshair_visible=self.hip_crosshair.visible,
            ui_scale=camera.ui.scale,
            help_text_nodes=len(self.help_text.text_nodes),
            help_size=[self.help_text.width, self.help_text.height],
            help_world_scale=self.help_text.world_scale,
            help_visible=self.help_text.visible,
            help_color=str(self.help_text.color),
            help_has_background_prop=isinstance(
                type(self.help_text).__dict__.get("background"), property
            ),
        )
        # endregion
        self._refresh_wind()

    def set_scoped(self, scoped: bool, *, use_overlay: bool = True) -> None:
        self.scoped = scoped
        self.scope.enabled = bool(scoped and use_overlay)
        self.hip_crosshair.enabled = not bool(scoped and use_overlay)
        self.refresh_weapon()

    def set_overlays_visible(self, visible: bool) -> None:
        if not visible:
            self.hip_crosshair.enabled = False
            self.scope.enabled = False
            return
        overlay = True
        weapon = getattr(self.game, "weapon", None)
        if weapon is not None:
            overlay = weapon.spec.scope_overlay
        self.set_scoped(self.scoped, use_overlay=overlay)

    def refresh_weapon(self, weapon=None) -> None:
        weapon = weapon if weapon is not None else getattr(self.game, "weapon", None)
        if weapon is None or not hasattr(self, "weapon_text"):
            return
        spec = weapon.spec
        if self.scoped and spec.scope_overlay:
            label = f"{spec.name}  ·  {weapon.magnification:.0f}x"
        else:
            label = f"{spec.name}  ·  {spec.mode_label}"
        _set_text(self.weapon_text, label)

    def play_shot_feedback(self) -> None:
        self._set_impact("", color.white)

    def show_impact(self, *, hit: bool, distance: float, label: str = "") -> None:
        if hit:
            name = label or "Treffer"
            tint = (
                color.rgb(0.97, 0.82, 0.35)
                if name == "Kopftreffer"
                else color.rgb(0.55, 0.95, 0.5)
            )
            self._set_impact(f"{name}  ·  {distance:.0f} m", tint)
        else:
            self._set_impact(
                f"Daneben  ·  Einschlag {distance:.0f} m", color.rgb(0.98, 0.62, 0.55)
            )

    def _set_impact(self, message: str, text_color) -> None:
        self.impact_text.text = message
        self.impact_text.color = text_color
        self.impact_text.enabled = bool(message)
        self.impact_panel.enabled = bool(message)

    def update(self) -> None:
        self._refresh_wind()
        self._refresh_rangefinder()
        self.refresh_weapon()

    def _refresh_wind(self) -> None:
        wind = self.game.wind
        strength = PhysVec3(wind.x, 0.0, wind.z).length()
        heading = compass_label(wind.x, wind.z)
        side = _wind_side(wind, camera.right)
        _set_text(self.wind_text, f"Wind  {strength:.1f} m/s²  {heading}\nzieht {side}")

    def _refresh_rangefinder(self) -> None:
        holding = held_keys[config.KEY_RANGEFINDER]
        self.range_text.enabled = holding
        self.range_panel.enabled = holding
        if not holding:
            return

        hit = raycast(
            camera.world_position,
            camera.forward,
            distance=config.RANGEFINDER_MAX,
            ignore=self.game.projectile_ignore,
        )
        _set_text(self.range_text, f"{hit.distance:.0f} m" if hit.hit else "kein Ziel")


def _panel(
    position: tuple[float, float] | Vec2,
    scale: tuple[float, float],
    *,
    origin: tuple[float, float] = (0, 0),
    enabled: bool = True,
) -> Entity:
    """Dark backing plate so light HUD text stays readable over sky and grass."""
    return Entity(
        parent=camera.ui,
        model="quad",
        color=color.rgba(0.0, 0.0, 0.0, 0.55),
        origin=origin,
        position=Vec3(position[0], position[1], 0.01),
        scale=scale,
        enabled=enabled,
    )


def _set_text(text_entity: Text, value: str) -> None:
    """Rebuilding text nodes every frame is costly; only write real changes."""
    if text_entity.text != value:
        text_entity.text = value


def _wind_side(wind: PhysVec3, camera_right: Vec3) -> str:
    lateral = wind.x * float(camera_right.x) + wind.z * float(camera_right.z)
    if abs(lateral) < 0.35:
        return "kaum seitlich"
    return "nach rechts" if lateral > 0.0 else "nach links"
