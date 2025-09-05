"""
Windows Sandbox alapértelmezett útvonal-konvenciók.
Ezeket a konstansokat használjuk a RO/WR/OUT mappákhoz a sandboxon belül.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True

# Olvasásra csatolt forrás mappa (ReadOnly) a sandboxban
SRC_RO: str = r"C:\src_ro"

# Írható munkakönyvtár a sandboxban
WORK_DIR: str = r"C:\work\w"

# Írható kimeneti könyvtár (innen gyűjtjük vissza az artefaktokat)
OUT_DIR: str = r"C:\work\out"
