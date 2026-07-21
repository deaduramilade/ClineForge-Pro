"""
Unit tests for the provider-neutral image generation domain layer.

``src.backend.services.image_generation``

All tests are deterministic and make no network calls.  A ``FakeImageProvider``
is injected wherever a real provider would be used, giving the test suite full
control over provider return values and exception behaviour.

Test categories
---------------
1.  ``_sniff_mime`` — magic-byte MIME detection (pure function, exercised directly)
2.  ``GeneratedImage`` — frozen dataclass construction / immutability
3.  ``ImageGenerationError`` — exception API
4.  ``ImageGenerationService`` construction — ``max_image_bytes`` validation
5.  ``ImageGenerationService.generate`` — success paths (PNG / JPEG / WebP)
6.  ``ImageGenerationService.generate`` — CinematicPrompt field forwarding
7.  ``ImageGenerationService.generate`` — width / height forwarding
8.  ``ImageGenerationService.generate`` — validation rejections
9.  ``ImageGenerationService.generate`` — provider exception propagation
10. ``ImageGenerationService.generate`` — size-boundary edge cases
11. ``ImageGenerationService.generate`` — no-retry guarantee
12. ``ImageGenerationService.generate`` — invalid provider return type
"""

from __future__ import annotations

import asyncio
import pytest

from src.backend.services.image_generation import (
    DEFAULT_MAX_IMAGE_BYTES,
    SUPPORTED_MIME_TYPES,
    GeneratedImage,
    ImageGenerationError,
    ImageGenerationProvider,
    ImageGenerationService,
    _sniff_mime,
)
from src.backend.services.scene_reasoning import (
    CameraAngle,
    CinematicPrompt,
    ShotType,
)


# ---------------------------------------------------------------------------
# Magic-byte fixtures (minimal valid image headers)
# ---------------------------------------------------------------------------

# 8-byte PNG signature followed by padding to make a plausible payload.
_PNG_HEADER: bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8   # 16 bytes

# 3-byte JPEG SOI followed by padding.
_JPEG_HEADER: bytes = b"\xff\xd8\xff" + b"\x00" * 13       # 16 bytes

# 12-byte RIFF/WEBP header followed by padding.
_WEBP_HEADER: bytes = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 4  # 16 bytes

# Bytes that look like none of the above.
_UNKNOWN_HEADER: bytes = b"\x00\x01\x02\x03" * 4           # 16 bytes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):
    """Run an async coroutine in a fresh event loop.  Avoids pytest-asyncio
    dependency and keeps tests synchronous-looking."""
    return asyncio.run(coro)


def _make_prompt(
    *,
    visual_description: str = "A sunlit rooftop in Cairo at dusk",
    negative_prompt: str = "text, watermarks, blurry, low quality",
    shot_type: ShotType = ShotType.WIDE,
    camera_angle: CameraAngle = CameraAngle.EYE_LEVEL,
    lighting: str = "golden hour backlit",
    mood: str = "neutral",
    environment: str = "exterior rooftop, urban Cairo",
    characters: list[str] | None = None,
) -> CinematicPrompt:
    """Construct a fully valid ``CinematicPrompt`` with sensible defaults."""
    return CinematicPrompt(
        visual_description=visual_description,
        shot_type=shot_type,
        camera_angle=camera_angle,
        lighting=lighting,
        mood=mood,
        environment=environment,
        characters=characters or [],
        negative_prompt=negative_prompt,
    )


# ---------------------------------------------------------------------------
# FakeImageProvider
# ---------------------------------------------------------------------------


class FakeImageProvider(ImageGenerationProvider):
    """Deterministic test double for ``ImageGenerationProvider``.

    Behaviour is controlled by constructor arguments:

    ``return_image``
        When set, ``generate_image`` returns this ``GeneratedImage`` directly.

    ``raise_error``
        When set, ``generate_image`` raises this exception.

    ``call_count``
        Incremented on every invocation — used to verify retry behaviour.

    ``last_call_kwargs``
        Records the keyword arguments passed to the most recent call.

    If both ``return_image`` and ``raise_error`` are set, ``raise_error``
    takes precedence.
    """

    def __init__(
        self,
        return_image: GeneratedImage | None = None,
        raise_error: BaseException | None = None,
    ) -> None:
        self.return_image = return_image
        self.raise_error = raise_error
        self.call_count: int = 0
        self.last_call_kwargs: dict = {}

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        width: int = 512,
        height: int = 512,
    ) -> GeneratedImage:
        self.call_count += 1
        self.last_call_kwargs = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
        }
        if self.raise_error is not None:
            raise self.raise_error
        if self.return_image is not None:
            return self.return_image
        raise RuntimeError("FakeImageProvider: no return_image or raise_error set")


def _make_fake_png(
    provider_id: str = "fake",
    model_id: str = "fake-model-v1",
    extra_bytes: int = 0,
) -> GeneratedImage:
    """Return a ``GeneratedImage`` with valid PNG magic bytes."""
    return GeneratedImage(
        image_bytes=_PNG_HEADER + b"\x00" * extra_bytes,
        mime_type="image/png",
        provider_id=provider_id,
        model_id=model_id,
    )


def _make_fake_jpeg(
    provider_id: str = "fake",
    model_id: str = "fake-model-v1",
) -> GeneratedImage:
    return GeneratedImage(
        image_bytes=_JPEG_HEADER,
        mime_type="image/jpeg",
        provider_id=provider_id,
        model_id=model_id,
    )


def _make_fake_webp(
    provider_id: str = "fake",
    model_id: str = "fake-model-v1",
) -> GeneratedImage:
    return GeneratedImage(
        image_bytes=_WEBP_HEADER,
        mime_type="image/webp",
        provider_id=provider_id,
        model_id=model_id,
    )


# ===========================================================================
# 1.  _sniff_mime — magic-byte detection
# ===========================================================================


class TestSniffMime:
    def test_png_recognised(self):
        assert _sniff_mime(_PNG_HEADER) == "image/png"

    def test_jpeg_recognised(self):
        assert _sniff_mime(_JPEG_HEADER) == "image/jpeg"

    def test_webp_recognised(self):
        assert _sniff_mime(_WEBP_HEADER) == "image/webp"

    def test_unknown_returns_none(self):
        assert _sniff_mime(_UNKNOWN_HEADER) is None

    def test_empty_bytes_returns_none(self):
        assert _sniff_mime(b"") is None

    def test_truncated_png_too_short_returns_none(self):
        # Only 7 bytes — PNG signature needs 8.
        assert _sniff_mime(b"\x89PNG\r\n\x1a") is None

    def test_truncated_jpeg_too_short_returns_none(self):
        # Only 2 bytes — JPEG SOI needs 3.
        assert _sniff_mime(b"\xff\xd8") is None

    def test_truncated_webp_too_short_returns_none(self):
        # Only 11 bytes — WEBP needs 12.
        assert _sniff_mime(b"RIFF\x00\x00\x00\x00WEB") is None

    def test_riff_without_webp_tag_returns_none(self):
        """RIFF header with a non-WEBP four-cc must not match."""
        data = b"RIFF\x00\x00\x00\x00AVI " + b"\x00" * 4
        assert _sniff_mime(data) is None

    def test_png_with_trailing_data_still_recognised(self):
        """Trailing data after the signature must not affect detection."""
        assert _sniff_mime(_PNG_HEADER + b"\xff" * 1000) == "image/png"

    def test_all_supported_types_covered(self):
        """Every value in SUPPORTED_MIME_TYPES is detectable by _sniff_mime."""
        samples = {
            "image/png": _PNG_HEADER,
            "image/jpeg": _JPEG_HEADER,
            "image/webp": _WEBP_HEADER,
        }
        assert set(samples.keys()) == SUPPORTED_MIME_TYPES
        for mime, data in samples.items():
            assert _sniff_mime(data) == mime


# ===========================================================================
# 2.  GeneratedImage — dataclass API
# ===========================================================================


class TestGeneratedImage:
    def test_fields_accessible(self):
        img = _make_fake_png()
        assert img.image_bytes == _PNG_HEADER
        assert img.mime_type == "image/png"
        assert img.provider_id == "fake"
        assert img.model_id == "fake-model-v1"

    def test_frozen_rejects_mutation(self):
        img = _make_fake_png()
        with pytest.raises((AttributeError, TypeError)):
            img.provider_id = "other"  # type: ignore[misc]

    def test_empty_model_id_allowed(self):
        """model_id may be empty — provider may not expose its model identity."""
        img = GeneratedImage(
            image_bytes=_PNG_HEADER,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        assert img.model_id == ""


# ===========================================================================
# 3.  ImageGenerationError — exception API
# ===========================================================================


class TestImageGenerationError:
    def test_is_exception(self):
        err = ImageGenerationError("something went wrong")
        assert isinstance(err, Exception)

    def test_message_preserved(self):
        err = ImageGenerationError("test message")
        assert str(err) == "test message"

    def test_cause_defaults_to_none(self):
        err = ImageGenerationError("msg")
        assert err.cause is None

    def test_cause_preserved(self):
        original = ValueError("root cause")
        err = ImageGenerationError("wrapped", cause=original)
        assert err.cause is original

    def test_cause_is_keyword_only(self):
        with pytest.raises(TypeError):
            ImageGenerationError("msg", ValueError("cause"))  # type: ignore[call-arg]


# ===========================================================================
# 4.  ImageGenerationService construction
# ===========================================================================


class TestServiceConstruction:
    def test_valid_construction(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        assert svc is not None

    def test_custom_max_image_bytes_accepted(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider, max_image_bytes=512)
        assert svc._max_image_bytes == 512

    def test_zero_max_image_bytes_rejected(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        with pytest.raises(ValueError, match="max_image_bytes must be at least 1"):
            ImageGenerationService(provider, max_image_bytes=0)

    def test_negative_max_image_bytes_rejected(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        with pytest.raises(ValueError):
            ImageGenerationService(provider, max_image_bytes=-1)


# ===========================================================================
# 5.  generate() — success paths
# ===========================================================================


class TestGenerateSuccess:
    def test_png_generation_succeeds(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        result = _run(svc.generate(_make_prompt()))
        assert isinstance(result, GeneratedImage)
        assert result.mime_type == "image/png"
        assert result.image_bytes == _PNG_HEADER

    def test_jpeg_generation_succeeds(self):
        provider = FakeImageProvider(return_image=_make_fake_jpeg())
        svc = ImageGenerationService(provider)
        result = _run(svc.generate(_make_prompt()))
        assert result.mime_type == "image/jpeg"

    def test_webp_generation_succeeds(self):
        provider = FakeImageProvider(return_image=_make_fake_webp())
        svc = ImageGenerationService(provider)
        result = _run(svc.generate(_make_prompt()))
        assert result.mime_type == "image/webp"

    def test_returned_image_is_same_object(self):
        """Service returns the provider's GeneratedImage unchanged."""
        img = _make_fake_png()
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider)
        result = _run(svc.generate(_make_prompt()))
        assert result is img

    def test_provider_id_preserved(self):
        img = _make_fake_png(provider_id="huggingface")
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider)
        result = _run(svc.generate(_make_prompt()))
        assert result.provider_id == "huggingface"

    def test_model_id_preserved(self):
        img = _make_fake_png(model_id="stabilityai/stable-diffusion-xl")
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider)
        result = _run(svc.generate(_make_prompt()))
        assert result.model_id == "stabilityai/stable-diffusion-xl"


# ===========================================================================
# 6.  generate() — CinematicPrompt field forwarding
# ===========================================================================


class TestPromptForwarding:
    def test_visual_description_forwarded_as_prompt(self):
        """visual_description must arrive as the ``prompt`` kwarg."""
        img = _make_fake_png()
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider)
        cp = _make_prompt(visual_description="Dramatic desert dunes at midnight")
        _run(svc.generate(cp))
        assert provider.last_call_kwargs["prompt"] == "Dramatic desert dunes at midnight"

    def test_negative_prompt_forwarded(self):
        """negative_prompt must arrive as the ``negative_prompt`` kwarg."""
        img = _make_fake_png()
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider)
        cp = _make_prompt(negative_prompt="cartoons, oversaturated, jpeg artifacts")
        _run(svc.generate(cp))
        assert provider.last_call_kwargs["negative_prompt"] == "cartoons, oversaturated, jpeg artifacts"

    def test_other_cinematic_fields_not_forwarded_to_provider(self):
        """Provider receives only prompt, negative_prompt, width, height."""
        img = _make_fake_png()
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider)
        _run(svc.generate(_make_prompt()))
        assert set(provider.last_call_kwargs.keys()) == {
            "prompt", "negative_prompt", "width", "height"
        }


# ===========================================================================
# 7.  generate() — width / height forwarding
# ===========================================================================


class TestDimensionForwarding:
    def test_default_dimensions(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        _run(svc.generate(_make_prompt()))
        assert provider.last_call_kwargs["width"] == 512
        assert provider.last_call_kwargs["height"] == 512

    def test_custom_width_forwarded(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        _run(svc.generate(_make_prompt(), width=1024))
        assert provider.last_call_kwargs["width"] == 1024

    def test_custom_height_forwarded(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        _run(svc.generate(_make_prompt(), height=768))
        assert provider.last_call_kwargs["height"] == 768

    def test_custom_width_and_height_forwarded(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        _run(svc.generate(_make_prompt(), width=1920, height=1080))
        assert provider.last_call_kwargs["width"] == 1920
        assert provider.last_call_kwargs["height"] == 1080


# ===========================================================================
# 8.  generate() — validation rejections
# ===========================================================================


class TestValidationRejections:
    def test_empty_image_bytes_rejected(self):
        bad = GeneratedImage(
            image_bytes=b"",
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="empty image bytes"):
            _run(svc.generate(_make_prompt()))

    def test_unsupported_mime_type_rejected(self):
        # GIF magic bytes with a declared GIF MIME type.
        bad = GeneratedImage(
            image_bytes=b"GIF89a" + b"\x00" * 10,
            mime_type="image/gif",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="unsupported MIME type"):
            _run(svc.generate(_make_prompt()))

    def test_mime_inconsistent_with_magic_bytes_rejected(self):
        """PNG bytes declared as JPEG must be rejected."""
        bad = GeneratedImage(
            image_bytes=_PNG_HEADER,      # PNG magic
            mime_type="image/jpeg",       # wrong declared type
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="do not match declared MIME type"):
            _run(svc.generate(_make_prompt()))

    def test_jpeg_magic_declared_as_png_rejected(self):
        bad = GeneratedImage(
            image_bytes=_JPEG_HEADER,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="do not match declared MIME type"):
            _run(svc.generate(_make_prompt()))

    def test_webp_magic_declared_as_jpeg_rejected(self):
        bad = GeneratedImage(
            image_bytes=_WEBP_HEADER,
            mime_type="image/jpeg",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="do not match declared MIME type"):
            _run(svc.generate(_make_prompt()))

    def test_oversized_image_rejected(self):
        # Service with max = 100 bytes; image has 200 bytes.
        big_img = GeneratedImage(
            image_bytes=_PNG_HEADER + b"\x00" * 200,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=big_img)
        svc = ImageGenerationService(provider, max_image_bytes=100)
        with pytest.raises(ImageGenerationError, match="exceeds the configured maximum"):
            _run(svc.generate(_make_prompt()))

    def test_empty_provider_id_rejected(self):
        bad = GeneratedImage(
            image_bytes=_PNG_HEADER,
            mime_type="image/png",
            provider_id="",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="empty provider_id"):
            _run(svc.generate(_make_prompt()))

    def test_whitespace_only_provider_id_rejected(self):
        bad = GeneratedImage(
            image_bytes=_PNG_HEADER,
            mime_type="image/png",
            provider_id="   ",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="empty provider_id"):
            _run(svc.generate(_make_prompt()))

    def test_unknown_magic_bytes_with_valid_declared_type_rejected(self):
        """Random bytes declared as PNG must be rejected (magic mismatch)."""
        bad = GeneratedImage(
            image_bytes=_UNKNOWN_HEADER + b"\x00" * 100,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError, match="do not match declared MIME type"):
            _run(svc.generate(_make_prompt()))


# ===========================================================================
# 9.  generate() — provider exception propagation
# ===========================================================================


class TestProviderExceptionPropagation:
    def test_provider_image_generation_error_propagates(self):
        """ImageGenerationError from the provider propagates unchanged."""
        original = ImageGenerationError("network timeout", cause=TimeoutError("timed out"))
        provider = FakeImageProvider(raise_error=original)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError) as exc_info:
            _run(svc.generate(_make_prompt()))
        assert exc_info.value is original

    def test_provider_runtime_error_propagates_unwrapped(self):
        """A non-ImageGenerationError from the provider propagates as-is (not wrapped)."""
        provider = FakeImageProvider(raise_error=RuntimeError("unexpected sdk crash"))
        svc = ImageGenerationService(provider)
        with pytest.raises(RuntimeError, match="unexpected sdk crash"):
            _run(svc.generate(_make_prompt()))

    def test_provider_value_error_propagates_unwrapped(self):
        provider = FakeImageProvider(raise_error=ValueError("bad config"))
        svc = ImageGenerationService(provider)
        with pytest.raises(ValueError, match="bad config"):
            _run(svc.generate(_make_prompt()))

    def test_provider_connection_error_propagates_unwrapped(self):
        provider = FakeImageProvider(raise_error=ConnectionError("refused"))
        svc = ImageGenerationService(provider)
        with pytest.raises(ConnectionError):
            _run(svc.generate(_make_prompt()))


# ===========================================================================
# 10.  generate() — size-boundary edge cases
# ===========================================================================


class TestSizeBoundary:
    def test_image_at_exact_max_bytes_accepted(self):
        """An image whose size equals max_image_bytes must pass (not > max)."""
        max_bytes = 50
        payload = _PNG_HEADER + b"\x00" * (max_bytes - len(_PNG_HEADER))
        assert len(payload) == max_bytes
        img = GeneratedImage(
            image_bytes=payload,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider, max_image_bytes=max_bytes)
        result = _run(svc.generate(_make_prompt()))
        assert result is img

    def test_image_one_byte_over_max_rejected(self):
        """An image one byte beyond max_image_bytes must be rejected."""
        max_bytes = 50
        payload = _PNG_HEADER + b"\x00" * (max_bytes - len(_PNG_HEADER) + 1)
        assert len(payload) == max_bytes + 1
        img = GeneratedImage(
            image_bytes=payload,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider, max_image_bytes=max_bytes)
        with pytest.raises(ImageGenerationError, match="exceeds the configured maximum"):
            _run(svc.generate(_make_prompt()))

    def test_custom_max_image_bytes_honoured(self):
        """A service with a higher max_image_bytes accepts larger images."""
        large_max = 1024 * 1024  # 1 MiB
        payload = _PNG_HEADER + b"\x00" * 500_000
        img = GeneratedImage(
            image_bytes=payload,
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=img)
        svc = ImageGenerationService(provider, max_image_bytes=large_max)
        result = _run(svc.generate(_make_prompt()))
        assert result is img

    def test_default_max_image_bytes_constant(self):
        assert DEFAULT_MAX_IMAGE_BYTES == 10 * 1024 * 1024


# ===========================================================================
# 11.  generate() — no-retry guarantee
# ===========================================================================


class TestNoRetry:
    def test_provider_called_exactly_once_on_success(self):
        provider = FakeImageProvider(return_image=_make_fake_png())
        svc = ImageGenerationService(provider)
        _run(svc.generate(_make_prompt()))
        assert provider.call_count == 1

    def test_provider_called_exactly_once_on_error(self):
        """Service must not retry after a provider failure."""
        provider = FakeImageProvider(
            raise_error=ImageGenerationError("quota exceeded")
        )
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError):
            _run(svc.generate(_make_prompt()))
        assert provider.call_count == 1

    def test_provider_called_exactly_once_on_validation_failure(self):
        """Service must not retry after its own validation fails."""
        bad = GeneratedImage(
            image_bytes=b"",
            mime_type="image/png",
            provider_id="fake",
            model_id="",
        )
        provider = FakeImageProvider(return_image=bad)
        svc = ImageGenerationService(provider)
        with pytest.raises(ImageGenerationError):
            _run(svc.generate(_make_prompt()))
        assert provider.call_count == 1


# ===========================================================================
# 12.  generate() — invalid provider return type
# ===========================================================================


class ProviderReturnsWrongType(ImageGenerationProvider):
    """A deliberately broken provider that returns a plain dict instead of GeneratedImage."""

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str,
        width: int = 512,
        height: int = 512,
    ) -> GeneratedImage:
        return {"image_bytes": _PNG_HEADER, "mime_type": "image/png"}  # type: ignore[return-value]


class TestInvalidProviderReturnType:
    def test_dict_return_triggers_attribute_error(self):
        """A provider returning a dict instead of GeneratedImage causes
        AttributeError (a programming error) to propagate unchanged — the
        service does NOT wrap it in ImageGenerationError."""
        svc = ImageGenerationService(ProviderReturnsWrongType())
        with pytest.raises((AttributeError, TypeError)):
            _run(svc.generate(_make_prompt()))
