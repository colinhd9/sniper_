"""Headed probe: boot the game, force input, screenshot, log pixel + shader facts."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

NOTIFY_PATH = ROOT / "scripts" / "_panda_notify.txt"
SHOT_DIR = ROOT / "scripts"

from panda3d.core import Filename, loadPrcFileData

# Capture Panda3D's own shader-compile diagnostics so they can be parsed, not eyeballed.
loadPrcFileData("", f"notify-output {NOTIFY_PATH.as_posix()}")

from ursina import Ursina, application, camera, held_keys, invoke, window  # noqa: E402

import os  # noqa: E402

from sniper_range import _debug_log, graphics  # noqa: E402
from sniper_range._debug_log import dlog  # noqa: E402

if os.environ.get("PROBE_FORCE_SHADERS") == "1":
    graphics.shaders_usable = lambda: True  # keep Ursina's GLSL shaders on

from sniper_range.app import Game, GameTicker  # noqa: E402

_debug_log.RUN_ID = "shaders-on" if os.environ.get("PROBE_FORCE_SHADERS") == "1" else "post-fix"


def shoot_screenshot(name: str) -> Path:
    from direct.showbase.ShowBaseGlobal import base

    # saveScreenshot grabs the last completed frame, so force a couple of
    # renders first; otherwise early captures come back empty.
    for _ in range(3):
        base.graphicsEngine.render_frame()
    path = SHOT_DIR / name
    base.win.saveScreenshot(Filename.fromOsSpecific(str(path)))
    return path


def describe_image(path: Path) -> dict:
    from PIL import Image

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        small = rgb.resize((160, 100))
        pixels = list(small.getdata())
    counts = Counter(pixels)
    top = counts.most_common(4)
    return {
        "file": path.name,
        "unique_colors": len(counts),
        "dominant": [f"{c}x{n}" for c, n in top],
        "dominant_share": round(top[0][1] / len(pixels), 3),
        "mean_rgb": [round(sum(p[i] for p in pixels) / len(pixels), 1) for i in range(3)],
    }


def describe_ui(path: Path) -> dict:
    """Measure UI elements against a plain red background: dark crosshair vs light text."""
    from PIL import Image

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size
        pixels = rgb.load()

    dark_box = [w, h, -1, -1]
    light_box = [w, h, -1, -1]
    dark_n = light_n = 0
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            if r > 180 and g < 70 and b < 70:
                continue  # red background
            brightness = (r + g + b) / 3
            box, is_dark = (dark_box, True) if brightness < 110 else (light_box, False)
            if is_dark:
                dark_n += 1
            else:
                light_n += 1
            box[0] = min(box[0], x)
            box[1] = min(box[1], y)
            box[2] = max(box[2], x)
            box[3] = max(box[3], y)

    def fmt(box: list[int], count: int) -> str:
        if count == 0:
            return "none"
        return f"x{box[0]}-{box[2]} y{box[1]}-{box[3]} ({box[2]-box[0]+1}x{box[3]-box[1]+1}px)"

    return {
        "screen": f"{w}x{h}",
        "dark_pixels": dark_n,
        "dark_bbox": fmt(dark_box, dark_n),
        "dark_height_share": round((dark_box[3] - dark_box[1] + 1) / h, 4) if dark_n else 0,
        "light_pixels": light_n,
        "light_bbox": fmt(light_box, light_n),
    }


def parse_notify() -> dict:
    if not NOTIFY_PATH.exists():
        return {"notify": "missing"}
    lines = NOTIFY_PATH.read_text(errors="replace").splitlines()
    unsupported = [l for l in lines if "not supported" in l]
    versions = sorted({l.split("version")[-1].strip().strip("'\" ") for l in unsupported})
    return {
        "notify_lines": len(lines),
        "shader_errors": len([l for l in lines if "compiling GLSL" in l]),
        "rejected_glsl_versions": versions[:8],
        "sample": unsupported[:3],
    }


def main() -> None:
    app = Ursina(title="Sniper Range probe", borderless=False, fullscreen=False, vsync=False)
    # Deliberately garish clear color: it must NOT match the fog color, otherwise
    # "empty background" and "fully fogged world" are indistinguishable in pixels.
    window.color = (1.0, 0.0, 0.0, 1)
    game = Game()
    GameTicker(game)

    state = {"phase": 0, "start_pos": None}

    def step() -> None:
        from direct.showbase.ShowBaseGlobal import base

        phase = state["phase"]
        state["phase"] += 1

        if phase == 0:
            # Face the target line so captures are comparable between runs.
            game.player.rotation_y = 0
            game.player.camera_pivot.rotation_x = 0
            shot = shoot_screenshot("probe_idle.png")
            dlog("H", "probe:idle", "first frame with fixed fog range", **describe_image(shot))
            dlog("A", "probe:notify", "panda3d shader diagnostics", **parse_notify())
            base.render.hide()  # UI only, over the red clear color
        elif phase == 1:
            shot = shoot_screenshot("probe_ui_only.png")
            dlog("I", "probe:ui_only", "UI measured over red background", **describe_ui(shot))
            base.render.show()
            game.hud.show_impact(hit=True, distance=642)
            state["start_pos"] = tuple(game.player.position)
            held_keys["w"] = 1
        elif phase == 2:
            dlog(
                "C",
                "probe:forced_input",
                "position after forced W key",
                start=state["start_pos"],
                now=tuple(game.player.position),
                grounded=game.player.grounded,
            )
            held_keys["w"] = 0
            held_keys["right mouse"] = 1
        elif phase == 3:
            shot = shoot_screenshot("probe_scoped.png")
            dlog(
                "D",
                "probe:scoped",
                "scoped frame",
                camera_fov=camera.fov,
                scoped=game.player.scoped,
                scope_enabled=game.hud.scope.enabled,
                **describe_image(shot),
            )
            held_keys["right mouse"] = 0
            game.weapon.cooldown_left = 0.0
            game.weapon.fire()
        elif phase == 4:
            dlog(
                "C",
                "probe:after_shot",
                "projectile spawned",
                projectiles=len([e for e in base.render.findAllMatches("**/+GeomNode")][:0]) or
                sum(1 for e in __import__("ursina").scene.entities if type(e).__name__ == "Projectile"),
                impact_text=game.hud.impact_text.text,
            )
        elif phase >= 6:
            shot = shoot_screenshot("probe_final.png")
            dlog("A", "probe:final", "final frame", impact=game.hud.impact_text.text, **describe_image(shot))
            application.quit()
            return

        invoke(step, delay=0.45)

    invoke(step, delay=1.2)
    app.run()


if __name__ == "__main__":
    main()
