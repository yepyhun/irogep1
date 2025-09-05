
from __future__ import annotations
from pathlib import Path
from typing import Sequence, Tuple
import zipfile

DEFAULT_EXCLUDES = ["**/__pycache__/**", "**/*.pyc", ".git/**", "out/**"]

def _is_excluded(rel: Path, exclude_globs: Sequence[str]) -> bool:
    s = rel.as_posix()
    for pat in exclude_globs:
        if rel.match(pat) or Path(s).match(pat):
            return True
    return False

def make_package(base: Path,
                 include_dirs: Sequence[str],
                 exclude_globs: Sequence[str],
                 dest_dir: Path) -> Tuple[Path, int, int]:
    """
    Létrehozza dest_dir alatt a package.zip-et.
    - Csak base alatti relatív fájlok
    - Kizárások: **/__pycache__/**, **/*.pyc, .git/**, out/** (mint minimum)
    - Tömörítés: ZIP_DEFLATED
    Vissza: (zip_path, entries, size_bytes)
    """
    base = base.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "package.zip"

    excludes = list(DEFAULT_EXCLUDES) + list(exclude_globs or ())

    file_list: list[Path] = []
    for d in include_dirs:
        p = (base / d).resolve()
        if not p.exists() or not p.is_dir():
            continue
        for f in sorted(p.rglob("*")):
            if f.is_file():
                rel = f.relative_to(base)
                if _is_excluded(rel, excludes):
                    continue
                file_list.append(rel)

    entries = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in file_list:
            abs_path = base / rel
            arcname = rel.as_posix()
            zf.write(abs_path, arcname)
            entries += 1

    size = zip_path.stat().st_size
    return zip_path, entries, size
