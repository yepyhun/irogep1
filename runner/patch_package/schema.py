from __future__ import annotations
"""Egyszerű séma-definíciók (nem jsonschema, kézi ellenőrzéshez)."""

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "base_branch",
    "base_commit_sha",
    "commit_message",
    "scope_size",
    "provenance",
}
# Pontosan az egyik: diff_unified XOR new_files[]
XOR_FIELDS = ("diff_unified", "new_files")

OPTIONAL_TOP_LEVEL_KEYS = {
    "affected_tests",
    "acceptance_checks",
    "notes_for_reviewer",
}

# Megengedett extra mezők későbbi bővítéshez:
ALLOWED_EXTRA_KEYS = {
    "schema_version","base_branch","base_commit_sha","commit_message","scope_size",
    "provenance","diff_unified","new_files","affected_tests","acceptance_checks",
    "notes_for_reviewer","_raw_len"
}
