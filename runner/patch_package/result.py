from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

# Exit kódok (részleges; Step 2-ben a PRE kapu lényeges)
EXIT_PRE = 39

@dataclass
class Result:
    ok: bool
    exit_code: int = 0
    errors: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.ok = False

    def add_evidence(self, msg: str) -> None:
        self.evidence.append(msg)
