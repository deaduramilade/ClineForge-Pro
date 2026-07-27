"""
Ephemeral in-memory generated-frame store.

MVP / competition-demo limitation
----------------------------------
Mirrors ``script_store.py``: a process-scoped, in-memory dictionary mapping
``script_id`` to an ordered list of generated storyboard frames. Lost on
process restart, no auth, no bound on size — fine for a controlled demo,
not for production. Exists so ``POST /api/animatic/export`` can retrieve
frames that were produced by earlier ``POST /api/generate/storyboard``
calls for the same script.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StoredFrame:
    """A single watermarked storyboard frame, ready for animatic assembly."""

    scene_index: int
    image_bytes: bytes
    mime_type: str
    watermarked: bool


# script_id -> {scene_index -> StoredFrame}
_store: dict[str, dict[int, StoredFrame]] = {}


def save_frame(script_id: str, frame: StoredFrame) -> None:
    """Persist a single generated frame, keyed by script_id and scene_index.

    Uploading a frame for a scene_index that's already stored overwrites it
    (regeneration/idempotency for a single scene).
    """
    _store.setdefault(script_id, {})[frame.scene_index] = frame


def get_frames(script_id: str) -> list[StoredFrame]:
    """Return all stored frames for ``script_id``, ordered by scene_index."""
    frames = _store.get(script_id, {})
    return [frames[i] for i in sorted(frames)]


def has_frames(script_id: str) -> bool:
    """Return True if at least one frame has been generated for script_id."""
    return bool(_store.get(script_id))


def clear() -> None:
    """Remove all entries. Intended for use in tests only."""
    _store.clear()
