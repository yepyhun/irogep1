"""Motorháztető (részletes napló) – csak szöveg, nincs futtatás/hálózat/subprocess.

Feladat:
- láthatósági flag kezelése (alapból rejtett),
- egyszerű naplóbuffer összegyűjtése,
- példaparancsok szöveges visszaadása (illusztráció, NEM végrehajtás).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List

_visible: bool = False
_log: List[str] = []

def set_visible(flag: bool) -> None:
    global _visible
    _visible = bool(flag)

def is_visible() -> bool:
    return _visible

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def log(line: str) -> None:
    _log.append(f"[{utc_now()}] {line}")

def get_text() -> str:
    return "\n".join(_log)

def clear() -> None:
    _log.clear()

def describe_commands(example_only: bool=True) -> list[str]:
    # Csak illusztráció; nincs végrehajtás.
    return [
        "python -m compileall -q .",
        "zip (projekt gyökérről, kizárásokkal)",
        "sha256sum <zip>",
        "kézbesítési szerződés ellenőrzése (ZIP létezik, méret>0, SHA, ENTRIES, markerek)",
    ]
