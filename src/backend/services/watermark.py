"""
C2PA-inspired watermarking service.

Owned by: Cybersecurity Specialist
Responsibility: Embed provenance metadata into generated media.

Implementation notes
---------------------
This embeds a JSON provenance manifest as a PNG ``tEXt`` ancillary chunk
(key: ``cineforge:provenance``) using Pillow. This is the "C2PA-inspired"
claim from SECURITY.md, deliberately **not** a full C2PA (Content
Credentials) manifest — no C2PA signing, no manifest store, no claim
generator registration. Full C2PA support via ``c2pa-rs`` remains a
documented future upgrade (see CHARTER.md §6 and SECURITY.md §2).

Any input image bytes are re-encoded to PNG before the chunk is embedded,
so watermarking works regardless of the source format. PNG ``tEXt`` chunks
survive re-saving with Pillow/most tools but — like any metadata-based
approach and unlike a cryptographically-robust watermark — do **not**
survive lossy re-compression, format conversion to JPEG, or screenshotting.
That limitation should be stated plainly in any judge-facing materials
rather than implied away.
"""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from PIL import Image
from PIL.PngImagePlugin import PngInfo

_MANIFEST_KEY = "cineforge:provenance"


@dataclass(frozen=True)
class WatermarkManifest:
    """Provenance manifest embedded in a watermarked asset."""

    asset_id: str
    timestamp: str
    model_id: str
    project_id: str
    user_id_hash: str
    perceptual_hash: str


class WatermarkService:
    """
    C2PA-inspired watermarking for AI-generated images.

    Embeds a provenance manifest into every generated asset before delivery.

    Usage:
        service = WatermarkService(project_id="cineforge-demo")
        watermarked_bytes, manifest = await service.embed(image_bytes, model_id="local-placeholder")
        manifest = await service.verify(watermarked_bytes)
    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id

    async def embed(
        self,
        image_bytes: bytes,
        model_id: str,
        user_id: str = "anonymous",
    ) -> tuple[bytes, WatermarkManifest]:
        """
        Embed a C2PA-inspired watermark manifest into image bytes.

        Args:
            image_bytes: Raw image bytes (any Pillow-readable format).
            model_id: Identifier of the model/provider used for generation.
            user_id: User identifier (hashed before embedding — never
                stored or transmitted in plaintext).

        Returns:
            Tuple of (PNG-encoded watermarked image bytes, manifest).
        """
        manifest = self._build_manifest(
            model_id=model_id, user_id=user_id, image_bytes=image_bytes
        )

        img = Image.open(io.BytesIO(image_bytes))
        img.load()

        png_info = PngInfo()
        png_info.add_text(_MANIFEST_KEY, json.dumps(asdict(manifest)))

        out = io.BytesIO()
        img.save(out, format="PNG", pnginfo=png_info)
        return out.getvalue(), manifest

    async def verify(self, image_bytes: bytes) -> WatermarkManifest | None:
        """
        Verify and extract the watermark manifest from PNG image bytes.

        Returns the manifest if a CineForge provenance chunk is present,
        or None if no watermark is found (e.g. never watermarked, or the
        chunk was stripped by re-saving through a tool that discards
        ancillary PNG chunks).
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()
        except Exception:
            return None

        raw = img.text.get(_MANIFEST_KEY) if hasattr(img, "text") else None
        if not raw:
            return None

        try:
            data = json.loads(raw)
            return WatermarkManifest(**data)
        except (json.JSONDecodeError, TypeError):
            return None

    def _build_manifest(
        self,
        model_id: str,
        user_id: str,
        image_bytes: bytes,
    ) -> WatermarkManifest:
        """Build a watermark manifest for an asset.

        ``perceptual_hash`` here is a simplified stand-in — a plain
        SHA-256 of the raw bytes, not a true perceptual/robust hash — and
        is named accordingly wherever it's surfaced. A real perceptual
        hash (e.g. pHash) that survives re-compression is future work.
        """
        asset_id = hashlib.sha256(image_bytes).hexdigest()[:16]
        return WatermarkManifest(
            asset_id=asset_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_id=model_id,
            project_id=self.project_id,
            user_id_hash=hashlib.sha256(user_id.encode()).hexdigest(),
            perceptual_hash=hashlib.sha256(image_bytes).hexdigest(),
        )
