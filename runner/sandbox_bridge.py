"""
Runner–Sandbox híd (MVP): profil szöveg előállítása futtatás nélkül.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from sandbox.wsb_profile import make_wsb_xml
from sandbox.paths import SRC_RO, WORK_DIR, OUT_DIR

def prepare_profile_text(src_ro: str = SRC_RO, work_dir: str = WORK_DIR, out_dir: str = OUT_DIR) -> str:
    """
    Állítsa elő a .wsb profil XML-t a megadott (vagy alapértelmezett) útvonalakkal.
    Nem ír fájlt és nem indít sandboxot.
    """
    return make_wsb_xml(src_ro, work_dir, out_dir)
