from __future__ import annotations
import subprocess, shlex, os
from typing import Tuple

def run_cmd(cmd: str) -> Tuple[int, str, str]:
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out, err

def working_tree_clean() -> bool:
    code, out, err = run_cmd("git status --porcelain")
    if code != 0:
        # Ha nincs repo, ez is "nem tiszta" jelzés
        return False
    return out.strip() == ""

def commit_exists(sha: str) -> bool:
    code, out, err = run_cmd(f"git cat-file -t {shlex.quote(sha)}")
    return code == 0 and out.strip() in {"commit", "tag"}  # tag is elfogadható mint mutató

def apply_check(diff_text: str) -> Tuple[bool, str]:
    # Írjuk ideiglenes fájlba a diffet és futtassuk a git apply --check parancsot.
    # Step 2-ben nem kötelező futtatni; a megvalósítás a későbbi használathoz kell.
    import tempfile
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
        tf.write(diff_text)
        temp_name = tf.name
    try:
        code, out, err = run_cmd(f"git apply --check {temp_name}")
        ok = (code == 0)
        msg = out if ok else err
        return ok, msg
    finally:
        try:
            os.remove(temp_name)
        except Exception:
            pass
