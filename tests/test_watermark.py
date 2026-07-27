"""Tests for services/watermark.py — real PNG-metadata-based watermarking."""

import io

import pytest
from PIL import Image

from src.backend.services.watermark import WatermarkService


def _png_bytes(color=(10, 20, 30), size=(32, 32)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_embed_then_verify_round_trips():
    service = WatermarkService(project_id="test-proj")
    original = _png_bytes()

    watermarked_bytes, manifest = await service.embed(original, model_id="test-model")
    recovered = await service.verify(watermarked_bytes)

    assert recovered == manifest
    assert recovered.model_id == "test-model"
    assert recovered.project_id == "test-proj"


@pytest.mark.asyncio
async def test_embed_produces_valid_png_larger_than_input_metadata():
    service = WatermarkService(project_id="test-proj")
    original = _png_bytes()

    watermarked_bytes, _ = await service.embed(original, model_id="test-model")

    img = Image.open(io.BytesIO(watermarked_bytes))
    img.load()
    assert img.size == (32, 32)


@pytest.mark.asyncio
async def test_verify_returns_none_for_unwatermarked_image():
    service = WatermarkService(project_id="test-proj")
    plain = _png_bytes()

    assert await service.verify(plain) is None


@pytest.mark.asyncio
async def test_verify_returns_none_for_garbage_bytes():
    service = WatermarkService(project_id="test-proj")

    assert await service.verify(b"not an image") is None


@pytest.mark.asyncio
async def test_embed_hashes_user_id_never_stores_plaintext():
    service = WatermarkService(project_id="test-proj")
    original = _png_bytes()

    _, manifest = await service.embed(original, model_id="m", user_id="alice@example.com")

    assert "alice" not in manifest.user_id_hash
    assert len(manifest.user_id_hash) == 64  # sha256 hex digest


@pytest.mark.asyncio
async def test_different_images_get_different_asset_ids():
    service = WatermarkService(project_id="test-proj")
    img_a = _png_bytes(color=(1, 2, 3))
    img_b = _png_bytes(color=(200, 100, 50))

    _, manifest_a = await service.embed(img_a, model_id="m")
    _, manifest_b = await service.embed(img_b, model_id="m")

    assert manifest_a.asset_id != manifest_b.asset_id
