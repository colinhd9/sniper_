"""Pick a render path the installed GPU driver can actually run.

Ursina's bundled shaders declare `#version 130`, `140`, or `150`. Apple's
OpenGL implementation only exposes a legacy 2.1 context (GLSL 1.20) unless a
core profile is requested, and GLSL 130/140 do not exist on macOS at all. Every
shader then fails to compile and the affected geometry and text vanish, leaving
just the sky. Panda3D's fixed-function pipeline still draws textures, vertex
colors, fog, and `render.setLight()` lights, so it is the safe fallback.
"""

from __future__ import annotations

# Lowest GLSL version that can run Ursina's shader set.
MIN_GLSL = (1, 50)

# Must beat the per-entity `setShader()` calls Ursina makes further down the
# scene graph; in Panda3D a higher priority on an ancestor wins.
_OVERRIDE_PRIORITY = 50


def glsl_version() -> tuple[int, int]:
    """GLSL version the live driver reports, or (0, 0) when shaders are unusable."""
    from direct.showbase.ShowBaseGlobal import base

    gsg = base.win.getGsg()
    if not gsg.getSupportsBasicShaders():
        return (0, 0)
    return (gsg.getDriverShaderVersionMajor(), gsg.getDriverShaderVersionMinor())


def shaders_usable() -> bool:
    return glsl_version() >= MIN_GLSL


def use_fixed_function_pipeline() -> None:
    """Strip every shader from the 3D scene and the UI overlay."""
    from direct.showbase.ShowBaseGlobal import base
    from ursina import camera

    base.render.setShaderOff(_OVERRIDE_PRIORITY)
    camera.ui.setShaderOff(_OVERRIDE_PRIORITY)
