"""Cookbook modal – három fül (PRPs / EXAMPLES / GUIDES), non-recursive böngészés.
Hotfix v1.6.1: valós modális párbeszéd, Frissítés / Betöltés / Hozzáadás.
- Csak .md / .txt fájlok, <= 128 KiB.
- Új minta hozzáadása: basename-only, tilos: '..', '/', '\\', abszolút út.
- UI-only: nincs hálózat, nincs külső folyamat.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Tuple
import tkinter as tk
from tkinter import ttk

BASE_DIR = Path(__file__).resolve().parents[1]
PRPS_DIR = BASE_DIR / "PRPs"
EXAMPLES_DIR = BASE_DIR / "EXAMPLES"
GUIDES_DIR = BASE_DIR / "GUIDES"

ALLOWED_EXT = {".md", ".txt"}
MAX_BYTES = 128 * 1024


def _list_dir(root: Path) -> List[Path]:
    if not root.exists():
        return []
    out: List[Path] = []
    for f in sorted(root.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            if f.suffix.lower() in ALLOWED_EXT and f.stat().st_size <= MAX_BYTES:
                out.append(f)
    return out


def list_cookbook_entries(limit: int = 200) -> List[Tuple[str, Path]]:
    items: List[Tuple[str, Path]] = []
    for root in (PRPS_DIR, EXAMPLES_DIR, GUIDES_DIR):
        for f in _list_dir(root):
            rel = str(f.relative_to(BASE_DIR))
            items.append((rel, f))
            if len(items) >= limit:
                return items
    return items


def read_snippet(path: Path, max_chars: int = 4000) -> str:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
        return txt[:max_chars]
    except Exception:
        return ""


ALLOWED_DIRS = {"PRPs": PRPS_DIR, "EXAMPLES": EXAMPLES_DIR, "GUIDES": GUIDES_DIR}


def save_snippet(target_dir: str, filename: str, content: str) -> str:
    if target_dir not in ALLOWED_DIRS:
        raise ValueError("invalid target_dir")
    # basename-only
    name = Path(filename).name
    if name != filename or name in {"", ".", ".."}:
        raise ValueError("invalid filename")
    if ".." in filename or Path(filename).is_absolute() or ("/" in filename or "\\" in filename):
        raise ValueError("invalid filename")
    if Path(name).suffix.lower() not in ALLOWED_EXT:
        raise ValueError("invalid extension")
    data = content.encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("content too large")
    out_dir = ALLOWED_DIRS[target_dir]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    out_path.write_bytes(data)
    return str(out_path.relative_to(BASE_DIR))


def open_dialog(root: tk.Tk, on_load: Callable[[str], None]) -> None:
    """Megnyit egy modális Szakácskönyv párbeszédablakot a három füllel."""
    win = tk.Toplevel(root)
    win.title("Szakácskönyv")
    win.transient(root)
    win.grab_set()

    nb = ttk.Notebook(win); nb.pack(fill="both", expand=True)

    tabs = {
        "PRPs": PRPS_DIR,
        "EXAMPLES": EXAMPLES_DIR,
        "GUIDES": GUIDES_DIR,
    }
    listboxes: dict[str, tk.Listbox] = {}

    def refresh_all(select_rel: str | None = None):
        for tab_name, dir_path in tabs.items():
            frame = frames[tab_name]
            lb: tk.Listbox = listboxes[tab_name]
            lb.delete(0, "end")
            files = _list_dir(dir_path)
            for f in files:
                lb.insert("end", str(f.relative_to(BASE_DIR)))
            # üres fül hint
            hints[tab_name].config(
                text="Csak a gyökérben lévő .md/.txt fájlokat listázzuk (≤128 KiB). Almappákat nem böngészünk."
                     if not files else ""
            )
            # kijelölés visszaállítása, ha kérve
            if select_rel is not None:
                for idx in range(lb.size()):
                    if lb.get(idx) == select_rel:
                        lb.selection_clear(0, "end")
                        lb.selection_set(idx)
                        lb.see(idx)
                        break

    frames: dict[str, ttk.Frame] = {}
    hints: dict[str, ttk.Label] = {}

    for tab_name, dir_path in tabs.items():
        frm = ttk.Frame(nb, padding=6); nb.add(frm, text=tab_name)
        frames[tab_name] = frm
        lb = tk.Listbox(frm, height=12, exportselection=False)
        lb.pack(fill="both", expand=True)
        listboxes[tab_name] = lb
        hint = ttk.Label(frm, text="", foreground="#777")
        hint.pack(fill="x", pady=(4,0))
        hints[tab_name] = hint

    # Gombok
    btns = ttk.Frame(win); btns.pack(fill="x", pady=6)
    status = ttk.Label(win, text="", foreground="#444")
    status.pack(fill="x", padx=6, pady=(0,6))

    def current_tab_name() -> str:
        return nb.tab(nb.select(), "text")

    def do_refresh():
        refresh_all()

    def do_load():
        tab = current_tab_name()
        lb = listboxes[tab]
        if lb.size() == 0 or not lb.curselection():
            status.config(text="Nincs tartalom ebben a fülben.")
            return
        rel = lb.get(lb.curselection()[0])
        path = BASE_DIR / rel
        text = read_snippet(path, max_chars=65536)
        on_load(text)
        status.config(text=f"Betöltve: {rel}")

    ttk.Button(btns, text="Frissítés", command=do_refresh, width=14, takefocus=False).pack(side="left")
    ttk.Button(btns, text="Betöltés a Tervrajzba", command=do_load, width=22, takefocus=False).pack(side="left")
    ttk.Button(btns, text="Bezár", command=win.destroy, width=10, takefocus=False).pack(side="right")

    # Hozzáadás panel
    add = ttk.LabelFrame(win, text="Új minta hozzáadása"); add.pack(fill="both", expand=False, padx=6, pady=(0,6))
    row1 = ttk.Frame(add); row1.pack(fill="x", padx=6, pady=(6,0))
    ttk.Label(row1, text="Célmappa:", width=12).pack(side="left")
    target = ttk.Combobox(row1, values=list(ALLOWED_DIRS.keys()), state="readonly", width=12)
    target.set("PRPs"); target.pack(side="left")
    ttk.Label(row1, text="Fájlnév (.md/.txt):", width=18).pack(side="left")
    name_var = tk.StringVar()
    name_ent = ttk.Entry(row1, textvariable=name_var, width=28)
    name_ent.pack(side="left", padx=(4,0))

    textw = tk.Text(add, height=6, wrap="word")
    textw.pack(fill="both", expand=True, padx=6, pady=6)

    def do_add():
        fn = name_var.get().strip()
        content = textw.get("1.0", "end-1c")
        try:
            rel = save_snippet(target.get(), fn, content)
        except Exception as e:
            status.config(text=f"Hiba: {e}")
            return
        status.config(text=f"Mentve: {rel}")
        # újratöltés és kijelölés
        try:
            select_tab = rel.split("/", 1)[0]
        except Exception:
            select_tab = "PRPs"
        # váltsunk a megfelelő fülre, ha eltér
        for i in range(nb.index("end")):
            if nb.tab(i, "text") == select_tab:
                nb.select(i)
                break
        refresh_all(select_rel=rel)

    addbtns = ttk.Frame(add); addbtns.pack(fill="x", padx=6, pady=(0,6))
    ttk.Button(addbtns, text="Hozzáadás", command=do_add, width=12, takefocus=False).pack(side="left")

    refresh_all()
    win.wait_window(win)
