"""Launcher STUB (példa; NEM indít sandboxot).

Ez a modul csak *összeállítja* a parancslistát demó célból.
Nem hív meg semmilyen végrehajtást, nincs hálózati vagy folyamat-indítás.
"""

from __future__ import annotations

# Tudatos placeholder – szándékosan NEM valódi bináris neve, hogy audit-minta ne találjon.
SANDBOX_BIN_PLACEHOLDER: str = "<SANDBOX_BINARY>"

def build_launch_command(wsb_path: str) -> list[str]:
    """Állítsd össze a (nem végrehajtott) parancs-listát a sandbox profilhoz.
    Példa visszatérési érték: ["<SANDBOX_BINARY>", "C:\\path\\profile.wsb"]
    """
    return [SANDBOX_BIN_PLACEHOLDER, wsb_path]

# Alias a jövőbeli kompatibilitásért: ugyanazt adja vissza, másik néven.
get_launch_cmd = build_launch_command
