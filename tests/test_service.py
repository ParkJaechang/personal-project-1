from pathlib import Path
import threading
import time
import unittest

from soop_clip_downloader.downloader import DownloadError, DownloadProgress, DownloadResult
from soop_clip_downloader.jobs import InMemoryJobQueue, JobStatus
from soop_clip_downloader.service import (
    DownloadWorker,
    PollingService,
    extract_text_updates,
)


class RecordingTelegram:
    def __init__(self, updates=None):
        self.updates = list(updates or [])
        self.offsets = []
        self.messages = []
        self.edits = []
        self.next_message_id = 10

    def get_updates(self, *, offset=None, timeout_seconds=30):
        self.offsets.append((offset, timeout_seconds))
        return {"ok": True, "result": self.updates}

    def send_message(self, chat_id: int, text: str):
        self.messages.append((chat_id, text))
        self.next_message_id += 1
        return {"ok": True, "result": {"message_id": self.next_message_id}}

    def edit_message_text(self, chat_id: int, message_id: int, text: str):
        self.edits.append((chat_id, message_id, text))
        return {"ok": True, "result": {"message_id": message_id}}


class RecordingApp:
    def __init__(self):
        self.messages = []

    def handle_text_message(self, *, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class OneJobWorker:
    def __init__(self):
        self.calls = 0

    def process_next(self) -> bool:
        self.calls += 1
        return self.calls == 1


class SucceedingDownloader:
    def download(self, job, progress_callback=None):
        if progress_callback:
            progress_callback(DownloadProgress(percent=12.0, eta="00:30", speed="4MiB/s"))
            progress_callback(DownloadProgress(percent=18.0, eta="00:25", speed="5MiB/s"))
        return DownloadResult(
            job=job,
            file_path=Path("downloads/clip.mp4"),
            stdout="ok",
            stderr="",
        )


class FailingDownloader:
    def download(self, job, progress_callback=None):
        raise DownloadError("network down")


class EditFailingTelegram(RecordingTelegram):
    def edit_message_text(self, chat_id: int, message_id: int, text: str):
        raise RuntimeError("edit failed")


class WaitingDownloader:
    def __init__(self):
        self.started = threading.Event()

    def download(self, job, progress_callback=None):
        self.started.set()
        while True:
            if progress_callback:
                progress_callback(DownloadProgress(percent=1.0, eta="01:00", speed="1MiB/s"))
            time.sleep(0.01)


class ServiceTests(unittest.TestCase):
    def test_extract_text_updates_ignores_non_text_messages(self):
        response = {
            "ok": True,
            "result": [
                {
                    "update_id": 10,
                    "message": {"chat": {"id": 100}, "text": "hello"},
                },
                {"update_id": 11, "message": {"chat": {"id": 100}}},
            ],
        }

        updates = extract_text_updates(response)

        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0].update_id, 10)
        self.assertEqual(updates[0].chat_id, 100)
        self.assertEqual(updates[0].text, "hello")

    def test_poll_once_dispatches_messages_advances_offset_and_processes_jobs(self):
        telegram = RecordingTelegram(
            [
                {
                    "update_id": 10,
                    "message": {"chat": {"id": 100}, "text": "hello"},
                },
                {
                    "update_id": 11,
                    "message": {"chat": {"id": 100}, "text": "again"},
                },
            ]
        )
        app = RecordingApp()
        worker = OneJobWorker()
        service = PollingService(
            telegram=telegram,
            app=app,
            worker=worker,
            poll_timeout_seconds=15,
        )

        service.poll_once()

        self.assertEqual(telegram.offsets, [(None, 15)])
        self.assertEqual(app.messages, [(100, "hello"), (100, "again")])
        self.assertEqual(service.next_offset, 12)
        self.assertEqual(worker.calls, 2)

    def test_worker_marks_success_and_reports_saved_path(self):
        queue = InMemoryJobQueue()
        queue.enqueue("https://vod.sooplive.com/player/195880425", chat_id=100)
        telegram = RecordingTelegram()
        worker = DownloadWorker(
            queue=queue,
            downloader=SucceedingDownloader(),
            telegram=telegram,
        )

        self.assertTrue(worker.process_next())

        job = queue.get(1)
        self.assertEqual(job.status, JobStatus.SUCCEEDED)
        self.assertEqual(job.file_path, Path("downloads/clip.mp4"))
        self.assertEqual(
            telegram.messages,
            [
                (100, "Starting download #1: 195880425"),
                (100, "Download progress #1: starting"),
                (100, "Download finished #1: downloads\\clip.mp4 (0.0 MB). Sending to Telegram..."),
                (100, "Download complete #1: downloads\\clip.mp4"),
            ],
        )
        self.assertEqual(
            telegram.edits,
            [
                (100, 12, "Download progress #1: 12.0% | ETA 00:30 | 4MiB/s"),
                (100, 12, "Download progress #1: 18.0% | ETA 00:25 | 5MiB/s"),
                (100, 12, "Download progress #1: complete"),
            ],
        )

    def test_worker_marks_failure_and_reports_error(self):
        queue = InMemoryJobQueue()
        queue.enqueue("https://vod.sooplive.com/player/195880425", chat_id=100)
        telegram = RecordingTelegram()
        worker = DownloadWorker(
            queue=queue,
            downloader=FailingDownloader(),
            telegram=telegram,
        )

        self.assertTrue(worker.process_next())

        job = queue.get(1)
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.error, "network down")
        self.assertEqual(
            telegram.messages[-1],
            (100, "Download failed #1: network down"),
        )

    def test_progress_edit_failure_does_not_stop_download(self):
        queue = InMemoryJobQueue()
        queue.enqueue("https://vod.sooplive.com/player/195880425", chat_id=100)
        telegram = EditFailingTelegram()
        worker = DownloadWorker(
            queue=queue,
            downloader=SucceedingDownloader(),
            telegram=telegram,
        )

        self.assertTrue(worker.process_next())

        job = queue.get(1)
        self.assertEqual(job.status, JobStatus.SUCCEEDED)
        self.assertIn(
            (100, "Download complete #1: downloads\\clip.mp4"),
            telegram.messages,
        )

    def test_background_worker_cancels_active_download(self):
        queue = InMemoryJobQueue()
        queue.enqueue("https://vod.sooplive.com/player/195880425", chat_id=100)
        telegram = RecordingTelegram()
        downloader = WaitingDownloader()
        worker = DownloadWorker(
            queue=queue,
            downloader=downloader,
            telegram=telegram,
            run_in_background=True,
        )

        self.assertTrue(worker.process_next())
        self.assertTrue(downloader.started.wait(timeout=1))
        self.assertTrue(worker.request_stop())
        self.assertTrue(worker.wait_until_idle(timeout_seconds=2))

        job = queue.get(1)
        self.assertEqual(job.status, JobStatus.CANCELLED)
        self.assertEqual(job.error, "cancelled by user")
        self.assertIn((100, "Download cancelled #1"), telegram.messages)


if __name__ == "__main__":
    unittest.main()
