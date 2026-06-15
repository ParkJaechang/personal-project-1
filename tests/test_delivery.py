from pathlib import Path
import tempfile
import unittest

from soop_clip_downloader.delivery import CompletedFileDeliverer


class RecordingTelegram:
    def __init__(self):
        self.messages = []
        self.video_files = []
        self.video_paths = []

    def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))

    def send_video_file(self, chat_id: int, file_path: Path, caption: str) -> None:
        self.video_files.append((chat_id, file_path, caption))

    def send_video_path(self, chat_id: int, file_path: Path, caption: str) -> None:
        self.video_paths.append((chat_id, file_path, caption))


class FailingUploadTelegram(RecordingTelegram):
    def send_video_file(self, chat_id: int, file_path: Path, caption: str) -> None:
        raise RuntimeError("upload failed")


class CompletedFileDelivererTests(unittest.TestCase):
    def test_sends_small_file_through_default_bot_api(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            telegram = RecordingTelegram()
            deliverer = CompletedFileDeliverer(
                telegram=telegram,
                max_default_upload_mb=50,
                local_bot_api_base_url=None,
            )

            outcome = deliverer.deliver(chat_id=100, job_id=1, file_path=file_path)

            self.assertEqual(outcome.method, "telegram_direct")
            self.assertEqual(telegram.video_files, [(100, file_path, "SOOP clip #1")])
            self.assertEqual(telegram.messages, [])

    def test_sends_large_file_path_through_local_bot_api_when_configured(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            telegram = RecordingTelegram()
            deliverer = CompletedFileDeliverer(
                telegram=telegram,
                max_default_upload_mb=0,
                local_bot_api_base_url="http://127.0.0.1:8081",
            )

            outcome = deliverer.deliver(chat_id=100, job_id=2, file_path=file_path)

            self.assertEqual(outcome.method, "telegram_local_api")
            self.assertEqual(telegram.video_paths, [(100, file_path, "SOOP clip #2")])
            self.assertEqual(telegram.messages, [])

    def test_reports_saved_path_when_file_is_too_large_without_local_bot_api(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            telegram = RecordingTelegram()
            deliverer = CompletedFileDeliverer(
                telegram=telegram,
                max_default_upload_mb=0,
                local_bot_api_base_url=None,
            )

            outcome = deliverer.deliver(chat_id=100, job_id=3, file_path=file_path)

            self.assertEqual(outcome.method, "saved_path_only")
            self.assertEqual(
                telegram.messages,
                [(100, f"Download complete #3: {file_path}")],
            )
            self.assertEqual(telegram.video_files, [])
            self.assertEqual(telegram.video_paths, [])

    def test_reports_saved_path_when_direct_upload_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            telegram = FailingUploadTelegram()
            deliverer = CompletedFileDeliverer(
                telegram=telegram,
                max_default_upload_mb=50,
                local_bot_api_base_url=None,
            )

            outcome = deliverer.deliver(chat_id=100, job_id=4, file_path=file_path)

            self.assertEqual(outcome.method, "saved_path_only")
            self.assertEqual(
                telegram.messages,
                [(100, f"Download complete #4: {file_path}")],
            )


if __name__ == "__main__":
    unittest.main()
