
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List
from .preflight import check_environment
from .packager import make_package
from .proof import sha256_of, make_evidence, write_evidence_json
from datetime import datetime, timezone
import json

@dataclass
class RunResult:
    ok: bool
    error: str|None
    zip_path: str|None
    sha256: str|None
    entries: int|None
    size: int|None
    logs: List[str]
    summary: str

def _utc_stamp_minute() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%MZ")

def run_once(plan_text: str, abort_flag: Callable[[], bool], base: Path) -> RunResult:
    logs: List[str] = []
    try:
        if abort_flag():
            return RunResult(False, "Megszakítva", None, None, None, None, logs, "Megszakítva.")

        logs.append("Előkészítés…")
        ok, msgs = check_environment(base)
        logs.extend(msgs)
        if not ok:
            return RunResult(False, "Előkészítés sikertelen", None, None, None, None, logs, "Hiba: előkészítés sikertelen.")

        if abort_flag():
            return RunResult(False, "Megszakítva", None, None, None, None, logs, "Megszakítva.")

        logs.append("Csomagolás…")
        out_dir = base / "out"
        run_dir = out_dir / f"run-{_utc_stamp_minute()}"
        run_dir.mkdir(parents=True, exist_ok=True)

        include_dirs = ["gui", "PRPs", "EXAMPLES", "GUIDES"]
        exclude_globs = ["**/__pycache__/**", "**/*.pyc", ".git/**", "out/**"]
        zip_path, entries, size = make_package(base, include_dirs, exclude_globs, run_dir)

        if abort_flag():
            return RunResult(False, "Megszakítva", None, None, None, None, logs, "Megszakítva.")

        logs.append("Ellenőrzés…")
        sha = sha256_of(zip_path)
        ev = make_evidence(zip_path, entries, size)
        write_evidence_json(ev, run_dir)

        hist_line = dict(ev)
        hist_line.update({"summary": f"Csomag elkészült — ENTRIES={entries}, SIZE={size}, SHA={sha[:7]}…", "ok": True})
        with (out_dir / "history.jsonl").open("a", encoding="utf-8") as hf:
            hf.write(json.dumps(hist_line, ensure_ascii=False) + "\n")

        logs.append("Kész.")

        summary = f"Csomag elkészült — ENTRIES={entries}, SIZE={size}, SHA={sha[:7]}…"
        return RunResult(True, None, str(zip_path.resolve()), sha, entries, size, logs, summary)

    except Exception as e:
        logs.append(f"Hiba: {e!r}")
        return RunResult(False, str(e), None, None, None, None, logs, f"Hiba: {e}")
