from pathlib import Path
import unittest

from soop_clip_downloader.downloader import build_ytdlp_command


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


if __name__ == "__main__":
    unittest.main()
