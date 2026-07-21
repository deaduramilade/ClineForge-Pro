"""
Ephemeral in-memory script store.

MVP / competition-demo limitation
----------------------------------
This module provides a process-scoped dictionary that maps ``script_id``
strings to ``ParsedScript`` objects.  Storage is intentionally in-process:

- No database, no file I/O, no external dependencies.
- All stored scripts are lost when the server process restarts.
- No authentication or access control — any caller with a valid ``script_id``
  can retrieve the corresponding ``ParsedScript``.
- Unbounded size; suitable for a controlled demo environment only.

When a production persistence layer (e.g. a database or a distributed cache)
is introduced, it should replace the functions in this module while leaving
their call sites unchanged.
"""

from src.backend.services.script_parser import ParsedScript

# Module-level store — process-scoped, ephemeral.
_store: dict[str, ParsedScript] = {}


def save(script_id: str, parsed: ParsedScript) -> None:
    """Persist a ``ParsedScript`` under ``script_id``."""
    _store[script_id] = parsed


def get(script_id: str) -> ParsedScript | None:
    """Return the ``ParsedScript`` for ``script_id``, or ``None`` if absent."""
    return _store.get(script_id)


def exists(script_id: str) -> bool:
    """Return ``True`` if ``script_id`` is already stored."""
    return script_id in _store


def clear() -> None:
    """Remove all entries.  Intended for use in tests only."""
    _store.clear()
