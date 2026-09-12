"""Temporary NDJSON debug instrumentation. Remove after the render bug is fixed."""

from __future__ import annotations

import json
import time
from pathlib import Path

LOG_PATH = Path(
    "/Users/colinhd/Library/Mobile Documents/com~apple~CloudDocs/python/.cursor/debug-72ae24.log"
)
RUN_ID = "run1"


def dlog(hypothesis: str, location: str, message: str, **data) -> None:
    entry = {
        "sessionId": "72ae24",
        "runId": RUN_ID,
        "hypothesisId": hypothesis,
        "location": location,
        "message": message,
        "data": {k: (repr(v) if not isinstance(v, (int, float, str, bool, type(None))) else v) for k, v in data.items()},
        "timestamp": int(time.time() * 1000),
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def gsg_report() -> dict:
    """Query the live Panda3D graphics state guardian for shader capabilities."""
    try:
        from direct.showbase.ShowBaseGlobal import base  # type: ignore

        gsg = base.win.getGsg()
        props = base.win.getProperties()
        return {
            "driver_vendor": gsg.getDriverVendor(),
            "driver_renderer": gsg.getDriverRenderer(),
            "driver_version": gsg.getDriverVersion(),
            "gl_major": gsg.getDriverVersionMajor(),
            "gl_minor": gsg.getDriverVersionMinor(),
            "glsl_major": gsg.getDriverShaderVersionMajor(),
            "glsl_minor": gsg.getDriverShaderVersionMinor(),
            "supports_glsl": bool(gsg.getSupportsGlsl()),
            "supports_basic_shaders": bool(gsg.getSupportsBasicShaders()),
            "window_foreground": bool(props.getForeground()),
            "window_open": bool(props.getOpen()),
        }
    except Exception as exc:  # pragma: no cover - instrumentation only
        return {"error": repr(exc)}
