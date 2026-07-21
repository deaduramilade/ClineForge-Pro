"""
Scripts router — upload and manage script files.

Parse-on-upload workflow
-------------------------
``POST /api/scripts/upload`` accepts a script file, parses it immediately
using ``ScriptParser``, and stores the resulting ``ParsedScript`` in the
process-scoped ephemeral store (``services.script_store``).

The ``script_id`` returned is a deterministic 16-character SHA-256 prefix of
the raw file bytes.  Uploading identical bytes twice therefore returns the
same ``script_id`` without re-parsing.

Decryption note (MVP limitation)
----------------------------------
SECURITY.md requires the client to AES-256-GCM-encrypt scripts before upload.
Decryption is the responsibility of the Cybersecurity Specialist and is NOT
yet implemented.  For the competition demo, plaintext files are accepted
directly.  The decryption step will slot in between ``file.read()`` and
``ScriptParser.parse()`` without changing any other code in this module.
"""

import hashlib

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

from models.schemas import ParsedScriptResponse, SceneMetadata
from services.script_parser import ScriptParser
from services.script_store import exists, get, save

router = APIRouter()

_parser = ScriptParser()

# Maximum allowed upload size: 50 MB (unchanged)
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ScriptUploadResponse(BaseModel):
    script_id: str
    filename: str
    size_bytes: int
    message: str
    title: str
    language: str
    scene_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_script_id(file_bytes: bytes) -> str:
    """Derive a deterministic 16-character script_id from file content."""
    return hashlib.sha256(file_bytes).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=ScriptUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a script file, parse it, and store the result",
)
async def upload_script(file: UploadFile) -> ScriptUploadResponse:
    """
    Accept a script file (.txt, .pdf, .docx), parse it with
    ``ScriptParser``, and persist the result in the ephemeral store.

    Returns a ``script_id`` (deterministic SHA-256 prefix of the file bytes)
    that callers can use to retrieve the parsed metadata or request a budget
    estimate without re-supplying scene/location/character counts.

    Uploading the same file twice is idempotent: the stored result is reused
    and parsing is skipped.

    **MVP limitation:** client-side AES-256 decryption is not yet wired.
    The endpoint currently accepts plaintext files for the competition demo.
    """
    allowed_mime_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/octet-stream",  # encrypted binary blobs
    }

    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = await file.read()

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum allowed size of 50 MB.",
        )

    script_id = _make_script_id(contents)
    filename = file.filename or "unknown"

    # Idempotency: skip re-parsing if already stored.
    if exists(script_id):
        stored = get(script_id)  # guaranteed non-None after exists() check
        return ScriptUploadResponse(
            script_id=script_id,
            filename=filename,
            size_bytes=len(contents),
            message="Script already parsed; returning cached result.",
            title=stored.title,
            language=stored.language,
            scene_count=stored.scene_count,
        )

    # Parse — map ValueError (unsupported extension, empty, undecodable) → 422.
    try:
        parsed = await _parser.parse(contents, filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    save(script_id, parsed)

    return ScriptUploadResponse(
        script_id=script_id,
        filename=filename,
        size_bytes=len(contents),
        message="Script parsed and stored successfully.",
        title=parsed.title,
        language=parsed.language,
        scene_count=parsed.scene_count,
    )


@router.get(
    "/{script_id}",
    response_model=ParsedScriptResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve parsed script metadata",
)
async def get_script(script_id: str) -> ParsedScriptResponse:
    """
    Return the full parsed metadata for a previously uploaded script.

    Raises HTTP 404 if the ``script_id`` is not found in the ephemeral store.
    """
    parsed = get(script_id)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script '{script_id}' not found. "
                   "Upload the script first via POST /api/scripts/upload.",
        )

    return ParsedScriptResponse(
        script_id=script_id,
        title=parsed.title,
        language=parsed.language,
        scene_count=parsed.scene_count,
        characters=parsed.characters,
        locations=parsed.locations,
        scenes=[
            SceneMetadata(
                index=s.index,
                heading=s.heading,
                description=s.description,
                characters=s.characters,
                location=s.location,
                time_of_day=s.time_of_day,
                mood=s.mood,
                dialogue=s.dialogue,
                language=s.language,
            )
            for s in parsed.scenes
        ],
    )
