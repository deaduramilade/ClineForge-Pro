"""
Motion animatic service.

Owned by: ML Engineer
Responsibility: Sequence storyboard frames into motion animatics (MP4/GIF).

Implementation notes
---------------------
- GIF export uses Pillow only (already a project dependency) — works
  anywhere, no system dependency.
- MP4 export shells out to ``ffmpeg`` via subprocess. This is a **system**
  dependency, not a Python package — it must be installed on whatever
  host runs the backend (``apt install ffmpeg`` / bundled in the deploy
  image). ``AnimaticService`` checks for it with ``shutil.which`` and
  raises a clear ``AnimaticError`` (not a generic crash) if it's missing,
  so the router can turn that into an honest error message instead of a
  silent failure or a fake success.
- Transitions ("fade", "dissolve") declared on ``AnimaticFrame`` are
  accepted but not yet implemented — every export is currently a hard
  cut between frames regardless of the requested transition. This is a
  known, intentional gap, not a bug: cut-only export was prioritized to
  get *something real* shipped before the deadline.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


class AnimaticError(Exception):
    """Raised when animatic assembly fails (bad input, or missing ffmpeg for MP4)."""


@dataclass(frozen=True)
class AnimaticFrame:
    """A single frame in an animatic."""

    scene_index: int
    image_bytes: bytes
    duration_ms: int = 2000
    transition: str = "fade"  # accepted, not yet implemented — see module docstring


@dataclass(frozen=True)
class AnimaticExport:
    """Result of an animatic export."""

    script_id: str
    format: str  # "mp4" or "gif"
    duration_seconds: float
    frame_count: int
    file_bytes: bytes


class AnimaticService:
    """
    Assemble storyboard frames into a motion animatic.

    Usage:
        service = AnimaticService()
        result = await service.export(script_id, frames, output_format="gif")
    """

    async def export(
        self,
        script_id: str,
        frames: list[AnimaticFrame],
        output_format: str = "mp4",
    ) -> AnimaticExport:
        """
        Export a list of storyboard frames as a motion animatic.

        Args:
            script_id: ID of the source script.
            frames: Ordered list of frames with timing data. Must be
                non-empty.
            output_format: "mp4" or "gif".

        Returns:
            AnimaticExport with real, playable file bytes.

        Raises:
            AnimaticError: on empty input, an unsupported format, or (for
                mp4) a missing ffmpeg binary on the host.
        """
        if not frames:
            raise AnimaticError(
                "Cannot export an animatic with zero frames. "
                "Generate at least one storyboard frame first."
            )
        if output_format not in ("mp4", "gif"):
            raise AnimaticError(
                f"Unsupported format {output_format!r}. Use 'mp4' or 'gif'."
            )

        ordered = sorted(frames, key=lambda f: f.scene_index)
        total_seconds = sum(f.duration_ms for f in ordered) / 1000.0

        if output_format == "gif":
            file_bytes = self._export_gif(ordered)
        else:
            file_bytes = self._export_mp4(ordered)

        return AnimaticExport(
            script_id=script_id,
            format=output_format,
            duration_seconds=total_seconds,
            frame_count=len(ordered),
            file_bytes=file_bytes,
        )

    # ------------------------------------------------------------------
    # GIF (Pillow only)
    # ------------------------------------------------------------------

    def _export_gif(self, frames: list[AnimaticFrame]) -> bytes:
        images = [
            Image.open(io.BytesIO(f.image_bytes)).convert("RGB") for f in frames
        ]
        # Pillow needs identical canvas sizes across frames for a clean GIF.
        target_size = images[0].size
        images = [img.resize(target_size) for img in images]

        durations = [f.duration_ms for f in frames]

        out = io.BytesIO()
        images[0].save(
            out,
            format="GIF",
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=0,
        )
        return out.getvalue()

    # ------------------------------------------------------------------
    # MP4 (ffmpeg subprocess)
    # ------------------------------------------------------------------

    def _export_mp4(self, frames: list[AnimaticFrame]) -> bytes:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise AnimaticError(
                "ffmpeg is not installed on this host, so MP4 export isn't "
                "available. Install ffmpeg, or request format='gif' instead "
                "(GIF export has no system dependency)."
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            concat_lines: list[str] = []
            last_name = ""

            for i, frame in enumerate(frames):
                img = Image.open(io.BytesIO(frame.image_bytes)).convert("RGB")
                frame_path = tmp_path / f"frame_{i:04d}.png"
                img.save(frame_path, format="PNG")
                concat_lines.append(f"file '{frame_path.name}'")
                concat_lines.append(f"duration {frame.duration_ms / 1000.0}")
                last_name = frame_path.name

            # ffmpeg's concat demuxer requires the last file repeated
            # without a duration line to make its duration take effect.
            concat_lines.append(f"file '{last_name}'")

            concat_file = tmp_path / "concat.txt"
            concat_file.write_text("\n".join(concat_lines))

            output_path = tmp_path / "output.mp4"
            cmd = [
                ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",  # even dimensions required by libx264
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
            result = subprocess.run(cmd, cwd=tmp_path, capture_output=True, text=True)

            if result.returncode != 0:
                raise AnimaticError(
                    f"ffmpeg failed (exit {result.returncode}): {result.stderr[-500:]}"
                )

            return output_path.read_bytes()
