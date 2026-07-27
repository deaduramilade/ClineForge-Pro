"""Tests for services/animatic.py — real GIF (Pillow) and MP4 (ffmpeg) export."""

import io
import shutil

import pytest
from PIL import Image

from src.backend.services.animatic import AnimaticError, AnimaticFrame, AnimaticService

_HAS_FFMPEG = shutil.which("ffmpeg") is not None


def _frame(scene_index: int, color, duration_ms: int = 1000) -> AnimaticFrame:
    img = Image.new("RGB", (16, 16), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return AnimaticFrame(scene_index=scene_index, image_bytes=buf.getvalue(), duration_ms=duration_ms)


@pytest.mark.asyncio
async def test_gif_export_produces_valid_multiframe_gif():
    service = AnimaticService()
    frames = [_frame(0, (255, 0, 0)), _frame(1, (0, 255, 0)), _frame(2, (0, 0, 255))]

    result = await service.export("script-1", frames, output_format="gif")

    assert result.format == "gif"
    assert result.frame_count == 3
    assert result.duration_seconds == pytest.approx(3.0)

    gif = Image.open(io.BytesIO(result.file_bytes))
    assert gif.is_animated
    assert gif.n_frames == 3


@pytest.mark.asyncio
async def test_gif_export_orders_frames_by_scene_index_not_input_order():
    service = AnimaticService()
    frames = [_frame(2, (0, 0, 255)), _frame(0, (255, 0, 0)), _frame(1, (0, 255, 0))]

    result = await service.export("script-1", frames, output_format="gif")
    gif = Image.open(io.BytesIO(result.file_bytes))

    gif.seek(0)
    first_pixel = gif.convert("RGB").getpixel((0, 0))
    assert first_pixel[0] > first_pixel[2]


@pytest.mark.asyncio
async def test_export_rejects_empty_frame_list():
    service = AnimaticService()
    with pytest.raises(AnimaticError, match="zero frames"):
        await service.export("script-1", [], output_format="gif")


@pytest.mark.asyncio
async def test_export_rejects_unsupported_format():
    service = AnimaticService()
    with pytest.raises(AnimaticError, match="Unsupported format"):
        await service.export("script-1", [_frame(0, (1, 2, 3))], output_format="avi")


@pytest.mark.asyncio
@pytest.mark.skipif(not _HAS_FFMPEG, reason="ffmpeg not installed on this host")
async def test_mp4_export_produces_playable_file():
    service = AnimaticService()
    frames = [_frame(0, (255, 0, 0)), _frame(1, (0, 255, 0))]

    result = await service.export("script-1", frames, output_format="mp4")

    assert result.format == "mp4"
    assert len(result.file_bytes) > 1000
    assert b"ftyp" in result.file_bytes[:64]
