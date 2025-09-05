"""Patch Package v1 modul inicializáló.
- validate_json(payload: str) -> Result
- preflight(doc: dict) -> Result
"""
from .result import Result, EXIT_PRE
from .schema import REQUIRED_TOP_LEVEL_KEYS, OPTIONAL_TOP_LEVEL_KEYS
from .validator import validate_json
from .preflight import preflight
