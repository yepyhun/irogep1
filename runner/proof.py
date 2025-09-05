
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def make_evidence(zip_path: Path, entries: int, size: int) -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "zip": str(zip_path.resolve()),
        "sha256": sha256_of(zip_path),
        "entries": int(entries),
        "size": int(size),
        "ts_utc": ts,
    }

def write_evidence_json(evidence: dict, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    p = dest_dir / "evidence.json"
    p.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    return p
