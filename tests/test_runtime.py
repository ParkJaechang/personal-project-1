from pathlib import Path
import importlib
import tempfile
import unittest

from soop_clip_downloader.config import Settings
from soop_clip_downloader.downloader import DownloadResult
from soop_clip_downloader.runtime import build_runtime, main as runtime_main


class RecordingTelegram:
    def __init__(self):
        self.messages = []
        self.edits = []
        self.video_files = []
        self.next_message_id = 10

    def get_updates(self, *, offset=None, timeout_seconds=30):
        return {"ok": True, "result": []}

    def send_message(self, chat_id: int, text: str):
        self.messages.append((chat_id, text))
        self.next_message_id += 1
        return {"ok": True, "result": {"message_id": self.next_message_id}}

    def edit_message_text(self, chat_id: int, message_id: int, text: str):
        self.edits.append((chat_id, message_id, text))
        return {"ok": True, "result": {"message_id": message_id}}

    def send_video_file(self, chat_id: int, file_path: Path, caption: str) -> None:
        self.video_files.append((chat_id, file_path, caption))

    def send_video_path(self, chat_id: int, file_path: Path, caption: str) -> None:
        raise AssertionError("local Bot API path send should not be used")


class StaticDownloader:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def download(self, job, progress_callback=None):
        return DownloadResult(job=job, file_path=self.file_path, stdout="", stderr="")


class RuntimeTests(unittest.TestCase):
    def test_package_main_exposes_runtime_main(self):
        package_main = importlib.import_module("soop_clip_downloader.__main__")

        self.assertIs(package_main.main, runtime_main)

    def test_build_runtime_wires_app_queue_worker_and_file_delivery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            settings = Settings(
                telegram_bot_token="123:abc",
                telegram_allowed_chat_id=100,
                download_dir=Path(temp_dir),
                max_telegram_upload_mb=50,
                telegram_api_base_url=None,
                telegram_local_file_uri_base=None,
                ytdlp_path="yt-dlp",
                ffmpeg_path="ffmpeg",
            )
            telegram = RecordingTelegram()
            runtime = build_runtime(
                settings,
                telegram=telegram,
                downloader=StaticDownloader(file_path),
            )

            runtime.app.handle_text_message(
                chat_id=100,
                text="https://vod.sooplive.com/player/195880425",
            )
            runtime.worker.process_next()

            self.assertEqual(
                telegram.messages,
                [
                    (100, "Queued download: 195880425"),
                    (100, "Starting download #1: 195880425"),
                    (100, "Download progress #1: starting"),
                    (100, f"Download finished #1: {file_path} (0.0 MB). Sending to Telegram..."),
                ],
            )
            self.assertEqual(
                telegram.edits,
                [(100, 13, "Download progress #1: complete")],
            )
            self.assertEqual(telegram.video_files, [(100, file_path, "SOOP clip #1")])


if __name__ == "__main__":
    unittest.main()
