"""
Image Generation Service — provider-neutral image generation layer.

Architecture
------------
This module defines three layers with strict separation of concerns:

1. **Domain model** (``GeneratedImage``) — a plain dataclass holding the raw
   bytes and metadata returned by a successful generation call.  No provider-
   specific types are exposed at this level.

2. **Domain error** (``ImageGenerationError``) — raised for every provider-
   or validation-level failure.  Never raised for programming errors, which
   propagate as-is.

3. **Provider abstraction** (``ImageGenerationProvider`` ABC) — the sole
   interface that ``ImageGenerationService`` and all tests depend on.
   Concrete provider implementations (Hugging Face, IBM watsonx.ai, etc.) must
   satisfy this interface and are intentionally absent from this module until
   their API contracts are verified.

4. **Service** (``ImageGenerationService``) — accepts a ``CinematicPrompt``
   from the scene-reasoning layer, extracts the prompt text, delegates
   generation to the configured provider, and applies byte-level validation
   before returning a ``GeneratedImage``.

Data flow
---------
``CinematicPrompt`` (from ``scene_reasoning``)
  → ``ImageGenerationService.generate(cinematic_prompt)``
    → ``ImageGenerationProvider.generate_image(prompt, negative_prompt, ...)``
      → raw bytes + metadata
    → magic-byte MIME validation
    → byte-length cap check
  → ``GeneratedImage``

Supported MIME types
--------------------
``image/png``   — 8-byte PNG signature  ``\\x89PNG\\r\\n\\x1a\\n``
``image/jpeg``  — 3-byte JPEG SOI marker ``\\xff\\xd8\\xff``
``image/webp``  — 12-byte RIFF/WEBP header

MIME detection uses magic-byte inspection only (pure Python, no Pillow, no
``imghdr`` — which was removed from the Python 3.13 standard library).

Retry policy
------------
**No retry logic is implemented in this module.**  Retries are the
responsibility of the caller (e.g., the router).  A provider implementation
may implement internal retries for transient failures if appropriate for its
backend, but the ``ImageGenerationService`` makes exactly one call to the
provider per ``generate()`` invocation.

Async contract
--------------
All public methods are ``async``.  Provider implementations that call
synchronous blocking SDKs must offload those calls using
``asyncio.to_thread()`` within their ``generate_image()`` implementation so
the FastAPI event loop is never blocked.  Provider implementations that use
natively async HTTP clients (e.g. ``httpx.AsyncClient``) may call them
directly without ``asyncio.to_thread()``.

Configuration
-------------
``ImageGenerationService`` accepts a configurable ``max_image_bytes`` limit
at construction time.  The default (``10 * 1024 * 1024`` = 10 MiB) guards
against runaway responses but can be overridden for testing or adjusted for
deployment.  The value is intentionally not read from environment variables
inside this module; the caller (router or factory function) is responsible
for passing the deployment-appropriate value.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.backend.services.scene_reasoning import CinematicPrompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MIME type constants and magic-byte detection
# ---------------------------------------------------------------------------

#: Supported output MIME types.  Any provider returning a different MIME type
#: will cause ``ImageGenerationService`` to raise ``ImageGenerationError``.
SUPPORTED_MIME_TYPES: frozenset[str] = frozenset(
    {"image/png", "image/jpeg", "image/webp"}
)

# Magic byte signatures (pure Python, no imghdr, no Pillow).
_PNG_MAGIC:  bytes = b"\x89PNG\r\n\x1a\n"   # 8 bytes
_JPEG_MAGIC: bytes = b"\xff\xd8\xff"          # 3 bytes
_RIFF_MAGIC: bytes = b"RIFF"                  # 4 bytes
_WEBP_TAG:   bytes = b"WEBP"                  # 4 bytes, at offset 8


def _sniff_mime(data: bytes) -> str | None:
    """Detect the MIME type of ``data`` from its magic bytes.

    Returns the MIME type string if recognised, or ``None`` if the byte
    signature does not match any supported format.  This function never
    raises; callers are responsible for treating ``None`` as an error.

    Detection is intentionally conservative: only the three formats that
    CineForge is expected to receive are checked.
    """
    if len(data) >= 8 and data[:8] == _PNG_MAGIC:
        return "image/png"
    if len(data) >= 3 and data[:3] == _JPEG_MAGIC:
        return "image/jpeg"
    if (
        len(data) >= 12
        and data[:4] == _RIFF_MAGIC
        and data[8:12] == _WEBP_TAG
    ):
        return "image/webp"
    return None


# ---------------------------------------------------------------------------
# Default limits
# ---------------------------------------------------------------------------

#: Default maximum allowed size for a single generated image (10 MiB).
DEFAULT_MAX_IMAGE_BYTES: int = 10 * 1024 * 1024


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GeneratedImage:
    """Immutable result of a single image generation call.

    Fields
    ------
    image_bytes
        Raw image payload.  Must be non-empty PNG, JPEG, or WebP bytes
        whose MIME type matches ``mime_type``.

    mime_type
        MIME type of ``image_bytes``.  Always one of the values in
        ``SUPPORTED_MIME_TYPES`` (``"image/png"``, ``"image/jpeg"``,
        ``"image/webp"``).  Callers may rely on this field being consistent
        with the actual bytes.

    provider_id
        A short identifier for the provider that generated the image
        (e.g. ``"huggingface"``, ``"watsonx"``).  Must be non-empty.  Used
        for logging, provenance metadata, and routing decisions.  This is
        the provider's own stable label, not a model name.

    model_id
        The model identifier used for this generation call, as reported or
        configured by the provider (e.g. a HuggingFace repo ID).  May be
        an empty string if the provider does not expose its model identity.
        When available, this field is passed to the watermarking layer to
        build the provenance manifest.

    Notes
    -----
    Width and height are **not** included in this model.  Pixel dimensions
    can only be read reliably by decoding the image (which requires Pillow
    or an equivalent library).  Since Pillow is not currently installed in
    the project venv and MIME validation is performed without it, dimensions
    are omitted to avoid inventing metadata that cannot be guaranteed.
    Width/height may be added in a future task once Pillow is available and
    installed.
    """

    image_bytes: bytes
    mime_type: str
    provider_id: str
    model_id: str


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------


class ImageGenerationError(Exception):
    """Raised when the image generation provider fails to produce a valid result.

    This exception is raised for provider-level and validation-level failures:

    - Provider network or authentication errors
    - Empty response bytes
    - Unrecognised or unsupported MIME type
    - Response size exceeding the configured maximum
    - Any other provider-reported error condition

    Programming errors (``TypeError``, ``AttributeError``, etc.) propagate
    as-is and are **not** wrapped in ``ImageGenerationError``.

    The optional ``cause`` attribute preserves the original exception for
    logging and debugging without leaking provider-specific types to callers.
    """

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------


class ImageGenerationProvider(ABC):
    """Abstract interface for image generation backends.

    Concrete implementations (Hugging Face, IBM watsonx.ai, etc.) must
    subclass this ABC.  ``ImageGenerationService`` and all tests depend only
    on this interface — never on a specific provider class.

    Implementer contract
    --------------------
    - ``generate_image`` must be ``async``.
    - It must return a ``GeneratedImage`` with non-empty ``image_bytes`` whose
      magic bytes match the declared ``mime_type``.
    - It must raise ``ImageGenerationError`` for every provider-level failure
      (network timeout, authentication error, rate limit, empty response, etc.).
    - It must **not** wrap programming errors in ``ImageGenerationError``.
    - It must **not** block the event loop.  Synchronous SDK calls must be
      offloaded using ``asyncio.to_thread()``.  Natively async HTTP clients
      may be called directly.
    - ``width`` and ``height`` are advisory hints.  Providers may ignore them
      if the underlying model does not support size control, but must document
      this behaviour.
    - No retries are required at this level, though a provider may add
      internal retries for transient failures appropriate to its backend.
    """

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        width: int = 512,
        height: int = 512,
    ) -> GeneratedImage:
        """Call the backing image model and return the result.

        Args:
            prompt:          English-language image-generation prompt.
            negative_prompt: Elements to exclude from the generated image.
            width:           Requested output width in pixels (advisory).
            height:          Requested output height in pixels (advisory).

        Returns:
            A ``GeneratedImage`` with validated bytes and metadata.

        Raises:
            ImageGenerationError: for any provider-level failure.
        """


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ImageGenerationService:
    """Provider-agnostic service that converts a ``CinematicPrompt`` into
    a ``GeneratedImage``.

    Responsibilities
    ----------------
    - Extract ``visual_description`` and ``negative_prompt`` from the input
      ``CinematicPrompt`` and pass them to the configured provider.
    - Accept advisory ``width`` and ``height`` parameters and forward them.
    - Validate the provider's returned ``GeneratedImage``:
        * ``image_bytes`` must be non-empty.
        * Magic-byte MIME type must match the declared ``mime_type``.
        * ``mime_type`` must be in ``SUPPORTED_MIME_TYPES``.
        * ``image_bytes`` length must not exceed ``max_image_bytes``.
        * ``provider_id`` must be non-empty.
    - Map validation failures to ``ImageGenerationError``.
    - Propagate ``ImageGenerationError`` raised by the provider unchanged.
    - Propagate unexpected exceptions (programming errors) unchanged.

    **No retries.**  A single call to the provider is made per
    ``generate()`` invocation.  Retry logic belongs to the caller.

    Usage::

        provider = SomeConcreteProvider(...)
        service  = ImageGenerationService(provider)
        image    = await service.generate(cinematic_prompt)

    For testing without a real provider, inject a ``FakeImageProvider``
    that returns controlled ``GeneratedImage`` instances or raises
    ``ImageGenerationError`` on demand.
    """

    def __init__(
        self,
        provider: ImageGenerationProvider,
        max_image_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    ) -> None:
        """
        Args:
            provider:        Concrete ``ImageGenerationProvider`` to delegate to.
            max_image_bytes: Maximum acceptable image size in bytes.  Responses
                             larger than this raise ``ImageGenerationError``.
                             Defaults to 10 MiB.  Must be ≥ 1.
        """
        if max_image_bytes < 1:
            raise ValueError(
                f"max_image_bytes must be at least 1, got {max_image_bytes}."
            )
        self._provider = provider
        self._max_image_bytes = max_image_bytes

    async def generate(
        self,
        cinematic_prompt: CinematicPrompt,
        width: int = 512,
        height: int = 512,
    ) -> GeneratedImage:
        """Generate a storyboard image from a validated ``CinematicPrompt``.

        Args:
            cinematic_prompt: Validated prompt from ``SceneReasoningService``.
            width:            Requested image width in pixels (advisory).
            height:           Requested image height in pixels (advisory).

        Returns:
            A ``GeneratedImage`` whose bytes have passed MIME and size checks.

        Raises:
            ImageGenerationError: if the provider fails or returns invalid bytes.
        """
        logger.debug(
            "ImageGenerationService.generate: prompt_len=%d width=%d height=%d",
            len(cinematic_prompt.visual_description),
            width,
            height,
        )

        result: GeneratedImage = await self._provider.generate_image(
            prompt=cinematic_prompt.visual_description,
            negative_prompt=cinematic_prompt.negative_prompt,
            width=width,
            height=height,
        )

        self._validate(result)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate(self, result: GeneratedImage) -> None:
        """Validate a ``GeneratedImage`` returned by the provider.

        Raises:
            ImageGenerationError: on any validation failure.
        """
        # 1. Byte payload must be non-empty.
        if not result.image_bytes:
            raise ImageGenerationError(
                "Provider returned empty image bytes."
            )

        # 2. Declared MIME type must be in the supported set.
        if result.mime_type not in SUPPORTED_MIME_TYPES:
            raise ImageGenerationError(
                f"Provider returned unsupported MIME type {result.mime_type!r}. "
                f"Supported types: {sorted(SUPPORTED_MIME_TYPES)}."
            )

        # 3. Magic bytes must match the declared MIME type.
        sniffed = _sniff_mime(result.image_bytes)
        if sniffed != result.mime_type:
            raise ImageGenerationError(
                f"Image bytes do not match declared MIME type. "
                f"Declared: {result.mime_type!r}, "
                f"detected: {sniffed!r}."
            )

        # 4. Payload must not exceed the configured size limit.
        if len(result.image_bytes) > self._max_image_bytes:
            raise ImageGenerationError(
                f"Image size {len(result.image_bytes):,} bytes exceeds the "
                f"configured maximum of {self._max_image_bytes:,} bytes."
            )

        # 5. Provider identifier must be non-empty.
        if not result.provider_id or not result.provider_id.strip():
            raise ImageGenerationError(
                "Provider returned a GeneratedImage with an empty provider_id."
            )
