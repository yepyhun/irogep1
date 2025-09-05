"""GUI – Szuper Írógép — GUI MVP (Step6 Komfort integráció)
- Nem használ hálózatot / külső folyamatot.
- Futáskor a runner.run.run_once(...) lokálisan csomagol és bizonyítékot készít az out/ alá.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, List
import threading, json
from pathlib import Path
from datetime import datetime, timezone

try:
    import ttkbootstrap as tb  # type: ignore
except Exception:
    tb = None  # type: ignore

try:
    from gui import ids
except Exception:
    class _IDS:
        APP_NAME = "Szuper Írógép"
        APP_VERSION = "1.x"
    ids = _IDS()  # type: ignore

try:
    from gui import hood
except Exception:
    class _H:
        @staticmethod
        def log(*_a, **_k): pass
        @staticmethod
        def is_visible(): return False
        @staticmethod
        def set_visible(*_a, **_k): pass
        @staticmethod
        def get_text(): return ""
    hood = _H()  # type: ignore

# Preferált integráció a runner-rel
from runner.run import run_once, RunResult  # type: ignore

APP_TITLE = f"{ids.APP_NAME} v{getattr(ids,'APP_VERSION','?')} — GUI MVP"

class App(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=8)
        self.master = master
        self.root = master  # baseline-compat: open_dialog(self.root, ...)

        if isinstance(master, (tk.Tk, tk.Toplevel)):
            master.title(APP_TITLE)

        self._running: bool = False
        self._scheduled: list[int] = []
        self._last_next_hint: str = ""
        self._history_lines: List[str] = []

        header = ttk.Frame(self); header.pack(fill="x", pady=(0,6))
        ttk.Label(header, text=APP_TITLE, font=("TkDefaultFont", 12, "bold")).pack(side="left")
        ttk.Button(header, text="Szakácskönyv", command=self.open_cookbook, width=16, takefocus=False).pack(side="right", padx=(6,0))
        self.hood_btn = ttk.Button(header, text="Motorháztető", command=self.toggle_hood, width=20, takefocus=False); self.hood_btn.pack(side="right")

        hint = ttk.Frame(self); hint.pack(fill="x", pady=(0,6))
        ttk.Label(hint, text="Következő lépés:", width=14).pack(side="left")
        self.next_hint = ttk.Label(hint, text="", foreground="#888"); self.next_hint.pack(side="left")
        self._set_next_hint("Illessz be tervrajzot!")

        # 1) TERVRAJZ
        card1 = ttk.LabelFrame(self, text="1) TERVRAJZ — BEILLESZTÉS & TISZTÍTÁS"); card1.pack(fill="both", expand=False, pady=(0,6))
        self.paste_input = tk.Text(card1, height=10, wrap="word", name=getattr(ids, "PASTE_INPUT", "#paste-input"))
        self.paste_input.pack(fill="both", expand=True, padx=6, pady=6)
        self.paste_input.bind("<<Modified>>", self._on_text_modified)
        tools = ttk.Frame(card1); tools.pack(fill="x", padx=6, pady=(0,6))
        self.btn_sanitize = ttk.Button(tools, text="Tisztítás", command=self.on_sanitize, width=16, takefocus=False); self.btn_sanitize.pack(side="left")
        ttk.Button(tools, text="Másolás (Terv)", command=lambda: self._copy(self.paste_input.get("1.0","end-1c")), takefocus=False).pack(side="right")

        # 2) FUTTATÁS
        card2 = ttk.LabelFrame(self, text="2) FUTTATÁS — NEM BLOKKOL"); card2.pack(fill="both", expand=False, pady=(0,6))
        runbar = ttk.Frame(card2); runbar.pack(fill="x", padx=6, pady=(6,0))
        self.btn_run = ttk.Button(runbar, text="Futtatás", command=self.on_run, width=16, takefocus=False); self.btn_run.pack(side="left")
        self.btn_stop = ttk.Button(runbar, text="Stop", command=self.on_stop, width=10, takefocus=False); self.btn_stop.pack(side="left", padx=(6,0))
        self.prog = ttk.Progressbar(runbar, mode="determinate", maximum=100); self.prog.pack(fill="x", expand=True, side="left", padx=(12,0))
        self.run_log = tk.Text(card2, height=10, wrap="word", name=getattr(ids, "RAW_OUTPUT", "#raw-output")); self.run_log.pack(fill="both", expand=True, padx=6, pady=6)
        ttk.Button(card2, text="Másolás (Futási napló)", command=lambda: self._copy(self.run_log.get("1.0","end-1c")), takefocus=False).pack(anchor="e", padx=6, pady=(0,6))

        # 3) EREDMÉNY & BIZONYÍTÉK
        card3 = ttk.LabelFrame(self, text="3) EREDMÉNY & BIZONYÍTÉK"); card3.pack(fill="both", expand=False)
        self.summary = tk.Text(card3, height=4, wrap="word", name=getattr(ids, "SUMMARY_HUMAN", "#summary-human")); self.summary.pack(fill="x", padx=6, pady=(6,0))
        ttk.Button(card3, text="Másolás (Összefoglaló)", command=lambda: self._copy(self.summary.get("1.0","end-1c")), takefocus=False).pack(anchor="e", padx=6, pady=(0,6))

        # Evidence mezők (ZIP, SHA256, ENTRIES, SIZE) + másolás gombok
        self.e_frame = ttk.Frame(card3); self.e_frame.pack(fill="x", padx=6, pady=(0,6))
        self.e_zip = tk.StringVar(); self.e_sha = tk.StringVar(); self.e_entries = tk.StringVar(); self.e_size = tk.StringVar()
        def _row(label: str, var: tk.StringVar):
            row = ttk.Frame(self.e_frame); row.pack(fill="x", pady=1)
            ttk.Label(row, text=label, width=10).pack(side="left")
            ent = ttk.Entry(row, textvariable=var); ent.pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="Másolás", takefocus=False, command=lambda v=var: self._copy(v.get())).pack(side="right")
        _row("ZIP", self.e_zip)
        _row("SHA256", self.e_sha)
        _row("ENTRIES", self.e_entries)
        _row("SIZE", self.e_size)

        # Előzmények
        self.history_frame = ttk.Frame(card3); self.history_frame.pack(fill="x", padx=6, pady=(0,6))
        ttk.Label(self.history_frame, text="Előzmények (utolsó 10):", foreground="#666").pack(anchor="w")
        self.history_list = ttk.Frame(self.history_frame); self.history_list.pack(fill="x")

        # Motorháztető
        self.hood_frame = ttk.LabelFrame(self, text="Motorháztető (részletes napló)")
        self.hood_text = tk.Text(self.hood_frame, height=10, wrap="none"); self.hood_text.pack(fill="both", expand=True, padx=6, pady=6)
        ttk.Button(self.hood_frame, text="Másolás (Motorháztető)", command=lambda: self._copy(self.hood_text.get("1.0","end-1c")), takefocus=False).pack(anchor="e", padx=6, pady=(0,6))
        self._render_hood_visibility(initial=True)

        self._update_run_enabled()
        self._refresh_history_ui()

    # ---------- Helpers ----------
    def _copy(self, text: str) -> None:
        try:
            self.clipboard_clear(); self.clipboard_append(text)
            self._flash_status("Másolva ✓", 1200)
        except Exception:
            pass

    def _flash_status(self, msg: str, ms: int = 1500) -> None:
        prev = self._last_next_hint
        self.next_hint.config(text=msg)
        self.after(ms, lambda: self.next_hint.config(text=prev))

    def _set_next_hint(self, msg: str) -> None:
        self._last_next_hint = msg
        self.next_hint.config(text=msg)

    def _update_run_enabled(self) -> None:
        has_text = self._has_paste_text()
        self.btn_run.config(state=("normal" if has_text and not self._running else "disabled"))
        self.btn_stop.config(state=("normal" if self._running else "disabled"))
        if not self._running:
            if not has_text: self._set_next_hint("Illessz be tervrajzot!")
            else: self._set_next_hint("Nyomd meg a Futtatás gombot!")

    def _has_paste_text(self) -> bool:
        return bool(self.paste_input.get("1.0","end-1c").strip())

    def _on_text_modified(self, _evt=None):
        try: self.paste_input.edit_modified(0)
        except Exception: pass
        self._update_run_enabled()

    def toggle_hood(self) -> None:
        try: hood.set_visible(not hood.is_visible())
        except Exception: pass
        self._render_hood_visibility()

    def _render_hood_visibility(self, initial: bool=False) -> None:
        vis = False
        try: vis = hood.is_visible()
        except Exception: vis = False
        if vis:
            if not initial:
                try:
                    self.hood_text.delete("1.0","end")
                    self.hood_text.insert("1.0", getattr(hood, "get_text", lambda: "")() or "Itt jelennek meg a parancsok és a részletes logok.")
                except Exception: pass
            self.hood_frame.pack(fill="both", expand=True, pady=(6,0))
            self.hood_btn.config(text="Motorháztető elrejtése")
        else:
            if self.hood_frame.winfo_ismapped(): self.hood_frame.pack_forget()
            self.hood_btn.config(text="Motorháztető")

    def _refresh_history_ui(self) -> None:
        for w in list(self.history_list.children.values()): w.destroy()
        try:
            base = Path(__file__).resolve().parents[1]
            hist = base / "out" / "history.jsonl"
            lines = []
            if hist.exists():
                with hist.open("r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f if ln.strip()]
            tail = lines[-10:]
            self._history_lines = tail
            for ln in reversed(tail):
                try:
                    obj = json.loads(ln)
                    ts = obj.get("ts_utc",""); sha = obj.get("sha256","")[:7]
                    ent = obj.get("entries",""); sz = obj.get("size","")
                    row = ttk.Frame(self.history_list); row.pack(fill="x")
                    ttk.Label(row, text=f"{ts}  {sha}  {ent}  {sz}").pack(side="left")
                    ttk.Button(row, text="Másolás (előzmény sor)", takefocus=False, command=lambda s=ln: self._copy(s)).pack(side="right")
                except Exception: pass
        except Exception: pass

    def _append_history(self, sha: str, entries: int, size: int) -> None:
        """Sikeres futás esetén sor hozzáfűzése az out/history.jsonl fájlhoz (duplázás elkerülése)."""
        try:
            base = Path(__file__).resolve().parents[1]
            out_dir = base / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            hist = out_dir / "history.jsonl"
            # Kerüld a duplikációt: ha már szerepel ugyanaz a sha, ne írj új sort
            if hist.exists():
                try:
                    with hist.open("r", encoding="utf-8") as f:
                        for ln in f:
                            if f'"sha256":"{sha}"' in ln:
                                return
                except Exception:
                    pass
            obj = {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": sha,
                "entries": int(entries),
                "size": int(size),
            }
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ---------- Actions ----------
    def on_sanitize(self) -> None:
        try:
            from gui.sanitize import sanitize
        except Exception:
            sanitize = lambda t: (t, [])
        original = self.paste_input.get("1.0","end-1c")
        cleaned, notes = sanitize(original)
        if cleaned != original:
            self.paste_input.delete("1.0","end"); self.paste_input.insert("1.0", cleaned)
            self._flash_status("Tisztítás kész — Nyomd meg a Futtatás gombot!", 2000)
        else:
            self._flash_status("Minden tiszta! — Nyomd meg a Futtatás gombot!", 2000)
        self._update_run_enabled()

    def on_run(self) -> None:
        if not self._has_paste_text() or self._running:
            if not self._running: self._set_next_hint("Illessz be tervrajzot!")
            return
        # Tisztítás a panelekben
        self.run_log.delete("1.0","end"); self.summary.delete("1.0","end")
        try: self.hood_text.delete("1.0","end")
        except Exception: pass
        # Evidence mezők törlése
        self.e_zip.set(""); self.e_sha.set(""); self.e_entries.set(""); self.e_size.set("")
        self.prog['value'] = 0
        self._set_next_hint("Fut… (Stop elérhető)")
        self._running = True; self._update_run_enabled()

        # MVP "vizuális" lépések
        steps = ["Előkészítés…","Sanitizer OK","Lint/Compile (szimuláció)…","Csomagolás (szimuláció)…","Ellenőrzés (MVP)…"]
        self._scheduled.clear(); total = len(steps)
        def stepper(i=0):
            if not self._running: return
            if i < total:
                line = steps[i]
                self.run_log.insert("end", f"{line}\n"); self.run_log.see("end")
                try: hood.log(f"STEP {i+1}/{total}: {line}")
                except Exception: pass
                self.prog['value'] = int((i+1)*100/total)
                self._scheduled.append(self.after(150, lambda: stepper(i+1)))
            else:
                plan_text = self.paste_input.get("1.0","end-1c")
                def worker():
                    base = Path(__file__).resolve().parents[1]
                    # Valódi futtatás a runner-rel; abort_flag megszakításra
                    res = run_once(plan_text, abort_flag=lambda: not self._running, base=base)
                    def finalize():
                        for l in res.logs:
                            self.run_log.insert("end", l + "\n")
                        self.run_log.see("end")
                        # Evidence megjelenítése (Motorháztető + panel)
                        try: self.hood_text.insert("end", "\n== Evidence ==\n")
                        except Exception: pass
                        if res.zip_path:
                            try: self.hood_text.insert("end", f"ZIP: {res.zip_path}\n")
                            except Exception: pass
                            self.e_zip.set(res.zip_path)
                        if res.sha256:
                            try: self.hood_text.insert("end", f"SHA256: {res.sha256}\n")
                            except Exception: pass
                            self.e_sha.set(res.sha256)
                        if res.entries is not None:
                            try: self.hood_text.insert("end", f"ENTRIES: {res.entries}\n")
                            except Exception: pass
                            self.e_entries.set(str(res.entries))
                        if res.size is not None:
                            try: self.hood_text.insert("end", f"SIZE: {res.size}\n")
                            except Exception: pass
                            self.e_size.set(str(res.size))

                        self.summary.insert("1.0", (res.summary or "") + "\n")
                        # Stop állapot lezárása
                        self._running = False; self._update_run_enabled()
                        if res.ok:
                            self._set_next_hint("Kész.")
                            # History append csak siker esetén (duplázás elkerülésével)
                            if res.sha256 and (res.entries is not None) and (res.size is not None):
                                self._append_history(res.sha256, int(res.entries), int(res.size))
                        else:
                            if (res.error or "").lower().startswith("megszakítva"):
                                self._set_next_hint("Megszakítva.")
                            else:
                                self._set_next_hint(f"Hiba: {res.error}")
                        self._refresh_history_ui()
                    self.after(0, finalize)
                threading.Thread(target=worker, daemon=True).start()
        stepper(0)

    def on_stop(self) -> None:
        if not self._running: return
        for h in self._scheduled:
            try: self.after_cancel(h)
            except Exception: pass
        self._scheduled.clear()
        self._running = False; self.prog['value'] = 0
        try: hood.log("STOP: felhasználói megszakítás")
        except Exception: pass
        self._set_next_hint("Megszakítva.")
        self._update_run_enabled()

    def open_cookbook(self) -> None:
        # Cookbook modal (valódi), csendes hibaág
        try:
            from gui import cookbook
            cookbook.open_dialog(self.root, on_load=self._load_recipe_from_file)
        except Exception:
            pass

    def _load_recipe_from_file(self, text: str) -> None:
        """A Szakácskönyvből betöltött szöveget átveszi a Tervrajz mező."""
        try:
            self.paste_input.delete("1.0", "end")
            self.paste_input.insert("1.0", text)
            self._flash_status("Nyomd meg a Futtatás gombot!", 1500)
            self._update_run_enabled()
        except Exception:
            pass

def main() -> None:
    # Témakezelés: ttkbootstrap (darkly) → ttk (clam) fallback, baseline szerint
    if tb is not None:
        try:
            root = tb.Window(themename="darkly")
            _ = tb.Style()
        except Exception:
            root = tk.Tk(); style = ttk.Style(root)
    else:
        root = tk.Tk(); style = ttk.Style(root)
        try: style.theme_use("clam")
        except Exception: pass
    app = App(root); app.pack(fill="both", expand=True)
    root.minsize(900, 640); root.mainloop()

if __name__ == "__main__":
    main()
