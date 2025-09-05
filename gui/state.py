from dataclasses import dataclass
from typing import Literal, Optional, Dict
State = Literal["INIT","READY","RUNNING","DONE","FAIL"]

@dataclass
class Delivery:
    zip_path: str
    sha256: str
    size_bytes: int
    entries: int

@dataclass
class RunRecord:
    id: str
    started_utc: str
    finished_utc: Optional[str]
    state: State
    summary_human: str
    raw_output: str
    delivery: Optional[Delivery]
    fix_prompt: Optional[str]

@dataclass
class UIState:
    app_health: Literal["OK","WARN","FAIL"]
    app_msg: str
    next_hint: str
    drawers: Dict[str,bool]  # {"cookbook":bool, "hood":bool}
