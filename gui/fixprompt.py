def make_fix_prompt(human_summary: str, raw_output: str) -> str:
    """Rövid, mérnöki prompt a hibákból; ne legyen túl bőbeszédű."""
    header = "Feladat: A build hiba javítása minimális diff-fel.\n"
    guard = ("Szabályok: csak az érintett fájlokat módosítsd; "
             "ne adj hozzá hálózatot/folyamatindítást; tartsd a kézbesítési szerződést.\n")
    body = f"Emberi összegzés:\n{human_summary.strip()}\n\nTeljes kimenet részlete:\n{raw_output[-4000:]}\n"
    ask  = ("\nKérés: Adj vissza Patch Package formátumot a konkrét javítással; "
            "rövid indoklással; új futás nélkül.")
    return header + guard + body + ask
