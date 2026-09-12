"""Shared impact contract between projectiles and anything they can score on."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HitResult:
    scored: bool
    label: str
