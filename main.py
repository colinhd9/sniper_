"""Launch Sniper Range from the project root."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sniper_range.app import run_game


if __name__ == "__main__":
    run_game()
