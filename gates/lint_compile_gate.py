"""
Build Gate MVP — Lint/Compile (tool-mentes)
- Public API:
    run_lint(paths: list[str]) -> Result
    run_compile(paths: list[str]) -> Result
    run_lint_compile(paths: list[str]) -> Result
- Exit code convention: EXIT_LINTCOMPILE = 40
- Timeout: 120s per gate (enforced by simple wall-clock checks)
- Time: monotonic measurement; UTC ISO-8601 timestamps for evidence
- Read-only: does not write .pyc (PYTHONDONTWRITEBYTECODE + sys flag)
"""
from __future__ import annotations
import os, sys, time, ast, io, traceback
from dataclasses import dataclass
from typing import List, Tuple

# Ensure no pyc written
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# Reuse canonical Result container from Step-2
try:
    from runner.patch_package.result import Result  # type: ignore
except Exception:
    # Minimal fallback if import path differs in early scaffolds
    @dataclass
    class Result:
        ok: bool
        exit_code: int
        errors: list
        evidence: list

# Gate-specific constant
EXIT_LINTCOMPILE = 40

_TIMEOUT_SECS = 120.0

def _utc_now() -> str:
    import datetime as _dt
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _iter_py_files(paths: List[str]) -> List[str]:
    seen = set()
    out = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isfile(p) and p.endswith(".py"):
            if p not in seen:
                out.append(p); seen.add(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    if f.endswith(".py"):
                        fp = os.path.abspath(os.path.join(root, f))
                        if fp not in seen:
                            out.append(fp); seen.add(fp)
    out.sort()
    return out

def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()

def _lint_one(path: str) -> Tuple[bool, list]:
    """Return (ok, messages); messages are 'path:line: msg'"""
    msgs = []
    try:
        txt = _read_text(path)
    except Exception as e:
        msgs.append(f"{path}:0: cannot read file: {e}")
        return False, msgs

    # Tabs
    for i, line in enumerate(txt.splitlines(True), start=1):
        if "\t" in line:
            msgs.append(f"{path}:{i}: TAB karaktert találtunk")
        # >120 oszlop
        ln = line[:-1] if line.endswith("\n") else line
        if len(ln) > 120:
            msgs.append(f"{path}:{i}: túl hosszú sor (>120)")

    # hiányzó záró newline
    if len(txt) > 0 and not txt.endswith("\n"):
        # a "sor" a végső sor száma
        end_line = txt.count("\n") + 1
        msgs.append(f"{path}:{end_line}: hiányzó záró soremelés")

    # Syntax via AST
    try:
        ast.parse(txt, filename=path)
    except SyntaxError as se:
        ln = getattr(se, "lineno", 0) or 0
        msgs.append(f"{path}:{ln}: szintaxis hiba: {se.msg}")

    ok = (len(msgs) == 0)
    return ok, msgs

def run_lint(paths: List[str]) -> Result:
    start = time.monotonic()
    ev = [f"lint.start={_utc_now()}"]
    errors = []
    for py in _iter_py_files(paths):
        if time.monotonic() - start > _TIMEOUT_SECS:
            errors.append("timeout: lint 120s limit")
            return Result(False, EXIT_LINTCOMPILE, errors, ev + ["lint.timeout=1"])
        ok, msgs = _lint_one(py)
        if not ok:
            errors.extend(msgs)
    ev.append(f"lint.end={_utc_now()}")
    return Result(len(errors)==0, 0 if len(errors)==0 else EXIT_LINTCOMPILE, errors, ev)

def run_compile(paths: List[str]) -> Result:
    import py_compile
    start = time.monotonic()
    ev = [f"compile.start={_utc_now()}"]
    errors = []
    for py in _iter_py_files(paths):
        if time.monotonic() - start > _TIMEOUT_SECS:
            errors.append("timeout: compile 120s limit")
            return Result(False, EXIT_LINTCOMPILE, errors, ev + ["compile.timeout=1"])
        try:
            # no .pyc writing thanks to dont_write_bytecode flag
            py_compile.compile(py, doraise=True)
            ev.append(f"compiled={py}")
        except Exception as e:
            errors.append(f"{py}:0: fordítási hiba: {e}")
    ev.append(f"compile.end={_utc_now()}")
    return Result(len(errors)==0, 0 if len(errors)==0 else EXIT_LINTCOMPILE, errors, ev)

def run_lint_compile(paths: List[str]) -> Result:
    r1 = run_lint(paths)
    if not r1.ok:
        return r1
    r2 = run_compile(paths)
    if not r2.ok:
        return r2
    # merge evidence
    return Result(True, 0, [], r1.evidence + r2.evidence)
