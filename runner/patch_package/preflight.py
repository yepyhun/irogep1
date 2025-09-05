from __future__ import annotations
import os, re, math
from typing import Any, Dict, Set
from .result import Result, EXIT_PRE
from .git_utils import working_tree_clean, commit_exists, apply_check

# Limitek
SOFT_FILES = 3
SOFT_LINES = 80
HARD_FILES = 6
HARD_LINES = 200
SOFT_BYTES = 200 * 1024  # 200 kB
HARD_FILE_BYTES = 2 * 1024 * 1024  # 2 MB per new file
HARD_TOTAL_BYTES = 5 * 1024 * 1024  # 5 MB total for new files

# Denylist
DENY_PREFIXES = (".git/", "0_SYSTEM/", "dist/", "runner/", "sandbox/", "gui/")

_seen_hashes: Set[str] = set()

def _calc_scope_from_diff(diff_text: str) -> (int, int):
    files = 0
    lines = 0
    if not isinstance(diff_text, str):
        return files, lines
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            files += 1
        elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            lines += 1
    return files, lines

def preflight(doc: Dict[str, Any]) -> Result:
    res = Result(ok=True, exit_code=0, errors=[], evidence=[])

    # Working tree tiszta?
    if not working_tree_clean():
        res.add_error("A working tree nem tiszta. Előbb mentsd vagy vondd vissza a helyi változtatásokat.")
    else:
        res.add_evidence("Working tree tiszta.")

    # base_commit létezik?
    base = doc.get("base_commit_sha")
    if not isinstance(base, str) or not commit_exists(base):
        res.add_error("A megadott base_commit_sha nem található a lokális gitben.")
    else:
        res.add_evidence(f"base_commit_sha OK: {base}")

    # Csomagméret (raw payload hossz) – ha rendelkezésre áll
    raw_len = doc.get("_raw_len")
    if isinstance(raw_len, int):
        if raw_len > SOFT_BYTES:
            res.add_evidence(f"Oversize csomag (raw_len={raw_len} byte) – lassú sáv javasolt.")
    else:
        res.add_evidence("Nem áll rendelkezésre nyers csomaghossz.")

    # scope_size kontra tényleges diff heurisztika
    files_decl = int(doc.get("scope_size", {}).get("files", 0) or 0)
    lines_decl = int(doc.get("scope_size", {}).get("lines", 0) or 0)
    files_calc = lines_calc = None

    if "diff_unified" in doc and isinstance(doc["diff_unified"], str):
        files_calc, lines_calc = _calc_scope_from_diff(doc["diff_unified"])
        res.add_evidence(f"Diff alapján becsült scope: files={files_calc}, lines={lines_calc}")

    # Soft/hard limitek
    def _check_limits(files, lines):
        if files > HARD_FILES or lines > HARD_LINES:
            res.add_error(f"Hard limit sérül: files={files} (max {HARD_FILES}) vagy lines={lines} (max {HARD_LINES}).")
        elif files > SOFT_FILES or lines > SOFT_LINES:
            res.add_evidence(f"Soft limit felett: files={files}, lines={lines} – lassú sáv javasolt.")

    _check_limits(files_decl, lines_decl)
    if files_calc is not None and lines_calc is not None:
        _check_limits(files_calc, lines_calc)

    # new_files byte limitek (ha vannak) – _nf_total_bytes a validatorban kerül kiszámításra
    nf_total = int(doc.get("_nf_total_bytes") or 0)
    if nf_total > HARD_TOTAL_BYTES:
        res.add_error(f"Új fájlok összmérete meghaladja az {HARD_TOTAL_BYTES} bájtot.")
    elif nf_total > 0:
        res.add_evidence(f"Új fájlok összmérete: {nf_total} bájt.")

    # Denylist érintésének detektálása (heurisztika diffből is)
    for key in ("diff_unified",):
        if key in doc and isinstance(doc[key], str):
            diff = doc[key]
            for prefix in DENY_PREFIXES:
                if f"/{prefix}" in diff or diff.startswith(prefix):
                    res.add_error(f"Denylist érintett a diffben: {prefix}")

    # Duplikáció védelem – doc['_payload_sha256'] jelenléte esetén
    payload_hash = doc.get("_payload_sha256")
    if isinstance(payload_hash, str):
        if payload_hash in _seen_hashes:
            res.add_error("Ugyanaz a csomag kétszer futtatva ebben a folyamatban (duplikáció-tiltás).")
        else:
            _seen_hashes.add(payload_hash)
            res.add_evidence("Payload hash regisztrálva ezen futásra.")

    # git apply --check (ha van diff)
    if isinstance(doc.get("diff_unified"), str):
        ok, msg = apply_check(doc["diff_unified"])
        if not ok:
            res.add_error(f"git apply --check hiba: {msg.strip()}")
        else:
            res.add_evidence("git apply --check OK.")

    # Végső exit code beállítása
    if not res.ok:
        res.exit_code = EXIT_PRE
    return res
