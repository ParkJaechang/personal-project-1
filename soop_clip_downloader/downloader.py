"""Download command construction for SOOP clips."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
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
        "--newline",
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


def build_ffmpeg_remux_command(
    *,
    file_path: Path,
    temp_path: Path,
    ffmpeg_path: str,
) -> list[str]:
    """Build a lossless MP4 remux command to rewrite container metadata."""

    return [
        ffmpeg_path,
        "-y",
        "-i",
        str(file_path),
        "-map",
        "0",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(temp_path),
    ]


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class DownloadProgress:
    percent: float
    eta: str | None
    speed: str | None


@dataclass(frozen=True)
class DownloadResult:
    job: DownloadJob
    file_path: Path
    stdout: str
    stderr: str


class DownloadError(RuntimeError):
    """Raised when yt-dlp fails or no output file can be located."""


ProgressCallback = Callable[[DownloadProgress], None]
CommandRunner = Callable[[list[str], ProgressCallback | None], CommandResult]


_PERCENT_RE = re.compile(r"^\[download\]\s+(?P<percent>\d+(?:\.\d+)?)%", re.IGNORECASE)
_SPEED_RE = re.compile(r"\bat\s+(?P<speed>\S+/s)", re.IGNORECASE)
_ETA_RE = re.compile(r"\bETA\s+(?P<eta>\S+)", re.IGNORECASE)


def parse_ytdlp_progress_line(line: str) -> DownloadProgress | None:
    line = line.strip()
    match = _PERCENT_RE.search(line)
    if not match:
        return None

    speed = _SPEED_RE.search(line)
    eta = _ETA_RE.search(line)
    return DownloadProgress(
        percent=float(match.group("percent")),
        eta=eta.group("eta") if eta else None,
        speed=speed.group("speed") if speed else None,
    )


class SubprocessCommandRunner:
    def __call__(
        self,
        command: list[str],
        progress_callback: ProgressCallback | None = None,
    ) -> CommandResult:
        completed = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output_lines: list[str] = []
        assert completed.stdout is not None
        for line in completed.stdout:
            output_lines.append(line)
            if progress_callback:
                progress = parse_ytdlp_progress_line(line)
                if progress:
                    progress_callback(progress)

        returncode = completed.wait()
        stdout = "".join(output_lines)
        return CommandResult(
            returncode=returncode,
            stdout=stdout,
            stderr="",
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

    def download(
        self,
        job: DownloadJob,
        progress_callback: ProgressCallback | None = None,
    ) -> DownloadResult:
        self._download_dir.mkdir(parents=True, exist_ok=True)
        before = set(self._download_dir.glob("*.mp4"))
        command = build_ytdlp_command(
            url=job.url,
            download_dir=self._download_dir,
            ytdlp_path=self._ytdlp_path,
            ffmpeg_path=self._ffmpeg_path,
        )
        result = self._command_runner(command, progress_callback)
        if result.returncode != 0:
            raise DownloadError(_best_error_message(result))

        file_path = _newest_mp4(self._download_dir, before)
        if file_path is None:
            raise DownloadError("yt-dlp completed but no MP4 file was found")

        self._remux_mp4(file_path)

        return DownloadResult(
            job=job,
            file_path=file_path,
            stdout=result.stdout,
            stderr=result.stderr,
        )

    def _remux_mp4(self, file_path: Path) -> None:
        temp_path = file_path.with_name(f"{file_path.stem}.remuxing{file_path.suffix}")
        temp_path.unlink(missing_ok=True)
        result = self._command_runner(
            build_ffmpeg_remux_command(
                file_path=file_path,
                temp_path=temp_path,
                ffmpeg_path=self._ffmpeg_path,
            ),
            None,
        )
        if result.returncode != 0:
            temp_path.unlink(missing_ok=True)
            raise DownloadError(_best_error_message(result))
        if not temp_path.exists():
            raise DownloadError("ffmpeg remux completed but no MP4 file was found")
        temp_path.replace(file_path)


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
