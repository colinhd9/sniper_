"""Sandbox map: large ground, readable landmarks, light and distance fog."""

from __future__ import annotations

from ursina import AmbientLight, DirectionalLight, Entity, Sky, Vec3, color, scene
from ursina.shaders import lit_with_shadows_shader

from sniper_range import config
from sniper_range.props import box


def build_world() -> Entity:
    # region agent log
    from sniper_range._debug_log import dlog, gsg_report
    dlog("A", "world.py:build_world", "graphics caps before world build", **gsg_report())
    # endregion
    scene.fog_color = color.rgb(0.62, 0.7, 0.76)
    scene.fog_density = config.FOG_RANGE

    ground = Entity(
        model="plane",
        collider="box",
        scale=config.MAP_SIZE,
        texture="grass",
        texture_scale=(64, 64),
        color=color.rgb(0.55, 0.58, 0.38),
        shader=lit_with_shadows_shader,
    )

    _build_ridges()
    _build_landmarks()
    _build_lighting()
    Sky(color=color.rgb(0.55, 0.68, 0.8))
    # region agent log
    from direct.showbase.ShowBaseGlobal import base
    from sniper_range._debug_log import dlog
    dlog(
        "H",
        "world.py:build_world",
        "world built - fog and lens state",
        ground_shader=getattr(ground.shader, "name", None),
        default_shader=getattr(Entity.default_shader, "name", None),
        entity_count=len(scene.entities),
        fog_density_attr=str(scene.fog_density),
        scene_has_fog=bool(scene.hasFog()),
        fog_mode=int(scene.fog.getMode()),
        fog_linear_onset=str(scene.fog.getLinearOnsetPoint()),
        fog_linear_opaque=str(scene.fog.getLinearOpaquePoint()),
        fog_exp_density=scene.fog.getExpDensity(),
        fog_color=str(scene.fog.getColor()),
        lens_near=base.camLens.getNear(),
        lens_far=base.camLens.getFar(),
        cam_hidden=bool(base.cam.isHidden()),
        window_clear=str(base.win.getClearColor()),
    )
    # endregion
    return ground


def _build_ridges() -> None:
    """Low mountains around the map so the player cannot walk into the void."""
    half = config.MAP_SIZE * 0.48
    height = 28
    thickness = 40
    rock = color.rgb(0.38, 0.36, 0.32)
    box((0, 0, half), (config.MAP_SIZE, height, thickness), color_value=rock, texture="white_cube")
    box((0, 0, -half), (config.MAP_SIZE, height, thickness), color_value=rock, texture="white_cube")
    box((half, 0, 0), (thickness, height, config.MAP_SIZE), color_value=rock, texture="white_cube")
    box((-half, 0, 0), (thickness, height, config.MAP_SIZE), color_value=rock, texture="white_cube")


def _build_landmarks() -> None:
    stone = color.rgb(0.42, 0.39, 0.35)
    adobe = color.rgb(0.55, 0.42, 0.3)
    rust = color.rgb(0.35, 0.22, 0.16)

    # Walkable berms and shooting platforms near mid-range targets.
    box((90, 0, 292), (18, 4, 18), color_value=stone, texture="white_cube")
    box((78, 0, 286), (10, 1.2, 16), color_value=stone, rotation=(0, 18, 0), texture="white_cube")
    box((-110, 0, 470), (16, 5, 14), color_value=stone, texture="white_cube")
    box((20, 0, 692), (20, 8, 16), color_value=stone, texture="white_cube")

    # Cover and orientation: house, wall, tower.
    box((-95, 0, 40), (10, 5.5, 8), color_value=adobe)
    box((-92, 5.5, 40), (11, 2.2, 9), color_value=rust)
    box((36, 0, 70), (14, 2.4, 0.6), color_value=stone)
    box((150, 0, 400), (6, 22, 6), color_value=adobe)
    box((150, 22, 400), (8, 3, 8), color_value=rust)

    # Rock clusters as distance cues.
    for pos, scale in (
        ((-30, 0, 60), (4, 2.2, 3.5)),
        ((22, 0, 95), (3, 1.6, 2.8)),
        ((-80, 0, 190), (6, 3.4, 5)),
        ((60, 0, 250), (5, 2.8, 4)),
        ((-140, 0, 330), (7, 4, 6)),
        ((180, 0, 510), (8, 5, 7)),
        ((-40, 0, 580), (5, 2.5, 4.5)),
        ((100, 0, 160), (3.5, 1.8, 3)),
    ):
        box(pos, scale, color_value=stone, texture="white_cube")

    # Gentle ramp so the mid platform can be climbed.
    Entity(
        model="cube",
        texture="white_cube",
        color=stone,
        position=(90, 1.2, 278),
        scale=(8, 0.6, 14),
        rotation=(18, 0, 0),
        collider="box",
        shader=lit_with_shadows_shader,
    )


def _build_lighting() -> None:
    # A 1000 m map makes cascaded shadows useless; keep the sun for shading only.
    sun = DirectionalLight(shadows=False)
    sun.look_at(Vec3(0.55, -1.0, -0.35))
    AmbientLight(color=color.rgba(0.7, 0.72, 0.76, 0.7))
