from pathlib import Path
import tempfile
import unittest

from soop_clip_downloader.downloader import (
    CommandResult,
    DownloadProgress,
    DownloadError,
    YtdlpDownloader,
    build_ytdlp_command,
    parse_ytdlp_progress_line,
)
from soop_clip_downloader.jobs import DownloadJob


class DownloaderTests(unittest.TestCase):
    def test_builds_1080p_or_lower_ytdlp_command(self):
        command = build_ytdlp_command(
            url="https://vod.sooplive.com/player/195880425",
            download_dir=Path("downloads"),
            ytdlp_path="yt-dlp",
            ffmpeg_path="ffmpeg",
        )

        self.assertEqual(
            command[:6],
            [
                "yt-dlp",
                "--newline",
                "--ffmpeg-location",
                "ffmpeg",
                "-f",
                "best[height<=1080]",
            ],
        )
        self.assertNotIn("hls-original/best", command)
        self.assertIn("--merge-output-format", command)
        self.assertIn("--no-playlist", command)
        self.assertIn("https://vod.sooplive.com/player/195880425", command)

    def test_parses_ytdlp_download_progress_line(self):
        progress = parse_ytdlp_progress_line(
            "[download]  42.7% of  191.76MiB at    8.32MiB/s ETA 00:13"
        )

        self.assertEqual(
            progress,
            DownloadProgress(percent=42.7, eta="00:13", speed="8.32MiB/s"),
        )

    def test_ignores_non_progress_ytdlp_line(self):
        self.assertIsNone(parse_ytdlp_progress_line("[download] Destination: clip.mp4"))

    def test_runner_returns_newest_mp4_after_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_dir = Path(temp_dir) / "downloads"
            calls = []

            def fake_run(command, progress_callback=None):
                calls.append(command)
                download_dir.mkdir(parents=True, exist_ok=True)
                if command[0] == "yt-dlp":
                    output = download_dir / "clip.mp4"
                    output.write_bytes(b"video")
                else:
                    Path(command[-1]).write_bytes(b"clean-video")
                if command[0] == "yt-dlp" and progress_callback:
                    progress_callback(DownloadProgress(percent=55.0, eta="00:05", speed="9MiB/s"))
                return CommandResult(returncode=0, stdout="ok", stderr="")

            downloader = YtdlpDownloader(
                download_dir=download_dir,
                ytdlp_path="yt-dlp",
                ffmpeg_path="ffmpeg",
                command_runner=fake_run,
            )

            progress_events = []
            result = downloader.download(
                DownloadJob(
                    id=1,
                    url="https://vod.sooplive.com/player/195880425",
                    chat_id=100,
                ),
                progress_callback=progress_events.append,
            )

            self.assertEqual(result.file_path, download_dir / "clip.mp4")
            self.assertIn("https://vod.sooplive.com/player/195880425", calls[0])
            self.assertEqual(len(calls), 2)
            self.assertEqual(
                calls[1],
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(download_dir / "clip.mp4"),
                    "-map",
                    "0",
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(download_dir / "clip.remuxing.mp4"),
                ],
            )
            self.assertEqual((download_dir / "clip.mp4").read_bytes(), b"clean-video")
            self.assertEqual(
                progress_events,
                [DownloadProgress(percent=55.0, eta="00:05", speed="9MiB/s")],
            )

    def test_runner_raises_error_when_command_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = YtdlpDownloader(
                download_dir=Path(temp_dir) / "downloads",
                ytdlp_path="yt-dlp",
                ffmpeg_path="ffmpeg",
                command_runner=lambda command, progress_callback=None: CommandResult(
                    returncode=1,
                    stdout="",
                    stderr="unsupported url",
                ),
            )

            with self.assertRaisesRegex(DownloadError, "unsupported url"):
                downloader.download(
                    DownloadJob(
                        id=1,
                        url="https://vod.sooplive.com/player/195880425",
                        chat_id=100,
                    )
                )


if __name__ == "__main__":
    unittest.main()
