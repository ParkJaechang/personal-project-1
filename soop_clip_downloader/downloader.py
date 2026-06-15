"""Download command construction for SOOP clips."""

from __future__ import annotations

from pathlib import Path


def build_ytdlp_command(
    *,
    url: str,
    download_dir: Path,
    ytdlp_path: str,
    ffmpeg_path: str,
) -> list[str]:
    """Build a yt-dlp argv list for original-quality SOOP User Clip download."""

    output_template = str(download_dir / "%(title)s [%(id)s].%(ext)s")
    return [
        ytdlp_path,
        "--ffmpeg-location",
        ffmpeg_path,
        "-f",
        "hls-original/best",
        "--merge-output-format",
        "mp4",
        "--no-playlist",
        "-o",
        output_template,
        url,
    ]
