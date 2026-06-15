from pathlib import Path
import tempfile
import unittest

from soop_clip_downloader.downloader import (
    CommandResult,
    DownloadError,
    YtdlpDownloader,
    build_ytdlp_command,
)
from soop_clip_downloader.jobs import DownloadJob


class DownloaderTests(unittest.TestCase):
    def test_builds_original_quality_ytdlp_command(self):
        command = build_ytdlp_command(
            url="https://vod.sooplive.com/player/195880425",
            download_dir=Path("downloads"),
            ytdlp_path="yt-dlp",
            ffmpeg_path="ffmpeg",
        )

        self.assertEqual(
            command[:5],
            [
                "yt-dlp",
                "--ffmpeg-location",
                "ffmpeg",
                "-f",
                "hls-original/best",
            ],
        )
        self.assertIn("--merge-output-format", command)
        self.assertIn("--no-playlist", command)
        self.assertIn("https://vod.sooplive.com/player/195880425", command)

    def test_runner_returns_newest_mp4_after_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            download_dir = Path(temp_dir) / "downloads"
            calls = []

            def fake_run(command):
                calls.append(command)
                download_dir.mkdir(parents=True, exist_ok=True)
                output = download_dir / "clip.mp4"
                output.write_bytes(b"video")
                return CommandResult(returncode=0, stdout="ok", stderr="")

            downloader = YtdlpDownloader(
                download_dir=download_dir,
                ytdlp_path="yt-dlp",
                ffmpeg_path="ffmpeg",
                command_runner=fake_run,
            )

            result = downloader.download(
                DownloadJob(
                    id=1,
                    url="https://vod.sooplive.com/player/195880425",
                    chat_id=100,
                )
            )

            self.assertEqual(result.file_path, download_dir / "clip.mp4")
            self.assertIn("https://vod.sooplive.com/player/195880425", calls[0])

    def test_runner_raises_error_when_command_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = YtdlpDownloader(
                download_dir=Path(temp_dir) / "downloads",
                ytdlp_path="yt-dlp",
                ffmpeg_path="ffmpeg",
                command_runner=lambda command: CommandResult(
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
