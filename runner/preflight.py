
from __future__ import annotations
from pathlib import Path
from typing import Tuple, List
import sys

def check_environment(base: Path) -> Tuple[bool, List[str]]:
    """
    Ellenőrzések:
    - Python >= 3.8 (sys.version_info)
    - base tartalmaz legalább egyet: gui/ VAGY runner/ és a tudásmappák közül legalább egyet: PRPs/, EXAMPLES/, GUIDES/
    - out/ létrehozható és írható (ha nincs, hozd létre)
    Vissza: (ok, üzenetek listája emberi nyelven)
    """
    msgs: List[str] = []
    ok = True

    # Python verzió
    if sys.version_info < (3,8):
        ok = False
        msgs.append(f"Python verzió túl régi: {sys.version.split()[0]} (>=3.8 szükséges)")
    else:
        msgs.append(f"Python version OK: {sys.version.split()[0]}")

    # Könyvtárak ellenőrzése
    base = base.resolve()
    has_gui = (base / "gui").exists()
    has_runner = (base / "runner").exists()
    has_any_core = has_gui or has_runner
    if not has_any_core:
        ok = False
        msgs.append("Hiányzik a GUI vagy a runner mappa (legalább az egyik szükséges).")
    else:
        core_list = []
        if has_gui: core_list.append("gui/")
        if has_runner: core_list.append("runner/")
        msgs.append("Magmappák elérhetők: " + ", ".join(core_list))

    has_know = any((base / d).exists() for d in ("PRPs","EXAMPLES","GUIDES"))
    if not has_know:
        msgs.append("Figyelmeztetés: nem található PRPs/, EXAMPLES/ vagy GUIDES/ (opcionális).")
    else:
        avail = [d for d in ("PRPs","EXAMPLES","GUIDES") if (base / d).exists()]
        msgs.append("Tudásmappák elérhetők: " + ", ".join(f"{d}/" for d in avail))

    # out/ írhatóság
    out_dir = base / "out"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        test_file = out_dir / ".write_test.tmp"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        msgs.append(f"Írási jog OK: {out_dir}")
    except Exception as e:
        ok = False
        msgs.append(f"Nem írható az out/ mappa: {e!r}")

    return ok, msgs
