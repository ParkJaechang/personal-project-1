"""Download command construction for SOOP clips."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable

from soop_clip_downloader.jobs import DownloadJob


def build_ytdlp_command(
    *,
    url: str,
    download_dir: Path,
    ytdlp_path: str,
    ffmpeg_path: str,
) -> list[str]:
    """Build a yt-dlp argv list for 1080p-or-lower SOOP User Clip download."""

    output_template = str(download_dir / "%(title)s [%(id)s].%(ext)s")
    return [
        ytdlp_path,
        "--ffmpeg-location",
        ffmpeg_path,
        "-f",
        "best[height<=1080]",
        "--merge-output-format",
        "mp4",
        "--no-playlist",
        "-o",
        output_template,
        url,
    ]


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class DownloadResult:
    job: DownloadJob
    file_path: Path
    stdout: str
    stderr: str


class DownloadError(RuntimeError):
    """Raised when yt-dlp fails or no output file can be located."""


CommandRunner = Callable[[list[str]], CommandResult]


class SubprocessCommandRunner:
    def __call__(self, command: list[str]) -> CommandResult:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


class YtdlpDownloader:
    def __init__(
        self,
        *,
        download_dir: Path,
        ytdlp_path: str,
        ffmpeg_path: str,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._download_dir = download_dir
        self._ytdlp_path = ytdlp_path
        self._ffmpeg_path = ffmpeg_path
        self._command_runner = command_runner or SubprocessCommandRunner()

    def download(self, job: DownloadJob) -> DownloadResult:
        self._download_dir.mkdir(parents=True, exist_ok=True)
        before = set(self._download_dir.glob("*.mp4"))
        command = build_ytdlp_command(
            url=job.url,
            download_dir=self._download_dir,
            ytdlp_path=self._ytdlp_path,
            ffmpeg_path=self._ffmpeg_path,
        )
        result = self._command_runner(command)
        if result.returncode != 0:
            raise DownloadError(_best_error_message(result))

        file_path = _newest_mp4(self._download_dir, before)
        if file_path is None:
            raise DownloadError("yt-dlp completed but no MP4 file was found")

        return DownloadResult(
            job=job,
            file_path=file_path,
            stdout=result.stdout,
            stderr=result.stderr,
        )


def _newest_mp4(download_dir: Path, before: set[Path]) -> Path | None:
    candidates = [path for path in download_dir.glob("*.mp4") if path not in before]
    if not candidates:
        candidates = list(download_dir.glob("*.mp4"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _best_error_message(result: CommandResult) -> str:
    message = (result.stderr or result.stdout).strip()
    return message or f"yt-dlp failed with exit code {result.returncode}"
