import unicodedata, re

MAX_INPUT_CHARS = 500_000
CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
SMART_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'",
    "\u201C": '"', "\u201D": '"',
    "\u2013": "-", "\u2014": "-",
    "\u00A0": " ",
})

def sanitize(text: str) -> tuple[str, list[str]]:
    """Sanitizer (NFC, CRLF→LF, vezérlők eltávolítása, BOM kiszedése, „okos idézők”)."""
    notes = []
    changed = False

    if len(text) > MAX_INPUT_CHARS:
        notes.append(f"Input túl nagy ({len(text)}), trunc {MAX_INPUT_CHARS}-ig.")
        text = text[:MAX_INPUT_CHARS]
        changed = True

    before = text
    text = text.lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_RE.sub("", text)
    text = text.translate(SMART_MAP)
    text = unicodedata.normalize("NFC", text)
    text = text.strip()

    if text != before or changed:
        notes.append("Normalizálás és tisztítás alkalmazva.")

    return text, notes
