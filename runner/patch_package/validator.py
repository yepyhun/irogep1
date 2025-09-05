from __future__ import annotations
import json, re, unicodedata
from typing import Any, Dict, List
from .result import Result, EXIT_PRE
from .schema import REQUIRED_TOP_LEVEL_KEYS, OPTIONAL_TOP_LEVEL_KEYS, XOR_FIELDS, ALLOWED_EXTRA_KEYS

HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
WINDOWS_FORBIDDEN = set('<>:"/\\|?*')

def _is_text(s: str) -> bool:
    # Heurisztika: ne legyen benne NUL
    return "\x00" not in s

def _normalize_nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)

def _valid_path(p: str) -> bool:
    if p.startswith(("/", "\\")):  # abszolút gyökér/UNC
        return False
    # relatív normalizálás
    import os
    norm = os.path.normpath(p).replace('\\', '/')
    if norm.startswith("../") or "/../" in norm or norm == "..":
        return False
    # tiltott karakterek
    if any(ch in WINDOWS_FORBIDDEN for ch in p):
        return False
    return True

def _validate_top_keys(doc: Dict[str, Any], res: Result) -> None:
    keys = set(doc.keys())
    missing = REQUIRED_TOP_LEVEL_KEYS - keys
    if missing:
        res.add_error(f"Hiányzó kötelező mezők: {sorted(missing)}")
    extra = keys - (REQUIRED_TOP_LEVEL_KEYS | OPTIONAL_TOP_LEVEL_KEYS | set(XOR_FIELDS) | {"_raw_len"})
    unexpected = [k for k in extra if k not in ALLOWED_EXTRA_KEYS]
    if unexpected:
        res.add_error(f"Váratlan extra mezők: {sorted(unexpected)}")

def _validate_xor(doc: Dict[str, Any], res: Result) -> None:
    have_diff = "diff_unified" in doc and isinstance(doc.get("diff_unified"), str)
    have_new = "new_files" in doc and isinstance(doc.get("new_files"), list)
    if have_diff == have_new:
        res.add_error("Pontosan az egyik szükséges: diff_unified XOR new_files[]")

def _validate_scope_size(doc: Dict[str, Any], res: Result) -> None:
    ss = doc.get("scope_size")
    if not isinstance(ss, dict):
        res.add_error("scope_size kötelező dict {files:int, lines:int}")
        return
    files = ss.get("files")
    lines = ss.get("lines")
    if not isinstance(files, int) or not isinstance(lines, int):
        res.add_error("scope_size.files és .lines egész számok legyenek")
        return
    # Soft/Hard limitek jelzése (preflight fog dönteni)
    if files < 0 or lines < 0:
        res.add_error("scope_size nem lehet negatív")

def _validate_provenance(doc: Dict[str, Any], res: Result) -> None:
    p = doc.get("provenance")
    if not isinstance(p, dict):
        res.add_error("provenance kötelező objektum")
        return
    for k in ("llm_vendor", "llm_model", "timestamp_utc"):
        if not isinstance(p.get(k), str) or not p.get(k):
            res.add_error(f"provenance.{k} kötelező szöveg")
    # prompt_header opcionális, de ha van, string legyen
    if "prompt_header" in p and not isinstance(p.get("prompt_header"), str):
        res.add_error("provenance.prompt_header ha megadott, string legyen")

def _validate_new_files(doc: Dict[str, Any], res: Result) -> None:
    nf = doc.get("new_files", [])
    if nf is None:
        return
    if not isinstance(nf, list):
        res.add_error("new_files lista kell legyen")
        return
    total_bytes = 0
    for i, it in enumerate(nf):
        if not isinstance(it, dict):
            res.add_error(f"new_files[{i}] objektum kell legyen")
            continue
        path = it.get("path")
        mode = it.get("mode")
        content = it.get("content")
        if not isinstance(path, str) or not isinstance(mode, str) or not isinstance(content, str):
            res.add_error(f"new_files[{i}] path/mode/content kötelező sztring")
            continue
        # NFC és path-szabályok
        path_nfc = _normalize_nfc(path)
        if not _valid_path(path_nfc):
            res.add_error(f"new_files[{i}] érvénytelen elérési út: {path}")
        # windows tiltott karakterek
        if any(ch in WINDOWS_FORBIDDEN for ch in path_nfc):
            res.add_error(f"new_files[{i}] tiltott karakter a fájlnévben: {path}")
        total_bytes += len(content.encode("utf-8"))
    # méretet a preflight fogja eldönteni; itt csak kalkulálunk, ha kell
    doc["_nf_total_bytes"] = total_bytes

def _validate_diff_unified(doc: Dict[str, Any], res: Result) -> None:
    diff = doc.get("diff_unified")
    if diff is None:
        return
    if not isinstance(diff, str):
        res.add_error("diff_unified szöveg kell legyen")
        return
    if not _is_text(diff):
        res.add_error("diff_unified bináris tartalmat tartalmaz (tilos)")
    # Nagyon alap unidiff jelzés (nem kötelező hibának venni)
    # if "@@ " not in diff and "diff --git" not in diff:

def validate_json(payload: str) -> Result:
    res = Result(ok=True)
    try:
        doc = json.loads(payload)
    except Exception as e:
        res.add_error(f"JSON parse hiba: {e}")
        return res
    # kulcsok, típusok
    _validate_top_keys(doc, res)
    if doc.get("schema_version") != "1":
        res.add_error("schema_version != '1'")
    if not isinstance(doc.get("base_branch"), str) or not doc.get("base_branch"):
        res.add_error("base_branch kötelező szöveg")
    if not isinstance(doc.get("base_commit_sha"), str) or not HEX40.match(doc.get("base_commit_sha", "")):
        res.add_error("base_commit_sha 40 hex karakter")
    if not isinstance(doc.get("commit_message"), str) or not doc.get("commit_message").strip():
        res.add_error("commit_message kötelező szöveg")
    _validate_scope_size(doc, res)
    _validate_provenance(doc, res)
    _validate_new_files(doc, res)
    _validate_diff_unified(doc, res)
    _validate_xor(doc, res)
    # nyers hossz eltárolása a preflightnak
    try:
        doc["_raw_len"] = len(payload.encode("utf-8"))
    except Exception:
        doc["_raw_len"] = None
    # evidence
    if res.ok:
        res.add_evidence("Schema OK")
    return res
