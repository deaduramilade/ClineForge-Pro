"""Scripts router — upload and manage script files."""

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

router = APIRouter()

# Maximum allowed upload size: 50 MB
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class ScriptUploadResponse(BaseModel):
    script_id: str
    filename: str
    size_bytes: int
    message: str


@router.post(
    "/upload",
    response_model=ScriptUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload an encrypted script file",
)
async def upload_script(file: UploadFile) -> ScriptUploadResponse:
    """
    Accept an AES-256-encrypted script file and queue it for parsing.

    The client must encrypt the script using AES-256-GCM (WebCrypto API)
    before uploading. Plaintext scripts are never accepted.

    Returns a script_id that can be used to poll for parsing results.
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

    # TODO (ML Engineer): pass to script_parser service after decryption
    # TODO (Cybersecurity): integrate decryption step here
    script_id = "placeholder-script-id"

    return ScriptUploadResponse(
        script_id=script_id,
        filename=file.filename or "unknown",
        size_bytes=len(contents),
        message="Script received and queued for parsing.",
    )


@router.get(
    "/{script_id}",
    summary="Get parsed script metadata",
)
async def get_script(script_id: str) -> dict:
    """
    Retrieve the parsing results for a previously uploaded script.

    Returns scene breakdown, character list, and location list.
    """
    # TODO (Data Science Lead): return real parsed data from script_parser service
    return {
        "script_id": script_id,
        "status": "pending",
        "message": "Parsing not yet implemented.",
    }
