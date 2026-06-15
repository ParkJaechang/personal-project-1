"""Polling service and download worker wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from soop_clip_downloader.delivery import PathOnlyDeliverer
from soop_clip_downloader.downloader import DownloadError


@dataclass(frozen=True)
class TextUpdate:
    update_id: int
    chat_id: int
    text: str


class TelegramGateway(Protocol):
    def get_updates(self, *, offset: int | None = None, timeout_seconds: int = 30) -> dict:
        """Return a raw Telegram getUpdates response."""

    def send_message(self, chat_id: int, text: str) -> object:
        """Send a Telegram text message."""


class TextMessageHandler(Protocol):
    def handle_text_message(self, *, chat_id: int, text: str) -> None:
        """Handle one text message."""


class QueueLike(Protocol):
    def pop_next(self):
        """Return the next queued job, if any."""

    def mark_started(self, job_id: int):
        """Mark a job as running."""

    def mark_succeeded(self, job_id: int, file_path):
        """Mark a job as successful."""

    def mark_failed(self, job_id: int, error: str):
        """Mark a job as failed."""


class DownloaderLike(Protocol):
    def download(self, job):
        """Download a queued job."""


class FileDeliverer(Protocol):
    def deliver(self, *, chat_id: int, job_id: int, file_path):
        """Deliver a completed download."""


def extract_text_updates(response: dict) -> list[TextUpdate]:
    updates: list[TextUpdate] = []
    for item in response.get("result", []):
        message = item.get("message") or {}
        text = message.get("text")
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        update_id = item.get("update_id")
        if isinstance(update_id, int) and isinstance(chat_id, int) and isinstance(text, str):
            updates.append(TextUpdate(update_id=update_id, chat_id=chat_id, text=text))
    return updates


class PollingService:
    def __init__(
        self,
        *,
        telegram: TelegramGateway,
        app: TextMessageHandler,
        worker,
        poll_timeout_seconds: int = 30,
    ) -> None:
        self._telegram = telegram
        self._app = app
        self._worker = worker
        self._poll_timeout_seconds = poll_timeout_seconds
        self.next_offset: int | None = None

    def poll_once(self) -> None:
        response = self._telegram.get_updates(
            offset=self.next_offset,
            timeout_seconds=self._poll_timeout_seconds,
        )
        updates = extract_text_updates(response)
        for update in updates:
            self._app.handle_text_message(chat_id=update.chat_id, text=update.text)
            self.next_offset = max(self.next_offset or 0, update.update_id + 1)

        while self._worker.process_next():
            pass

    def run_forever(self) -> None:
        while True:
            self.poll_once()


class DownloadWorker:
    def __init__(
        self,
        *,
        queue: QueueLike,
        downloader: DownloaderLike,
        telegram: TelegramGateway,
        deliverer: FileDeliverer | None = None,
    ) -> None:
        self._queue = queue
        self._downloader = downloader
        self._telegram = telegram
        self._deliverer = deliverer or PathOnlyDeliverer(telegram=telegram)

    def process_next(self) -> bool:
        job = self._queue.pop_next()
        if job is None:
            return False

        self._queue.mark_started(job.id)
        self._telegram.send_message(
            job.chat_id,
            f"Starting download #{job.id}: {_title_no_from_url(job.url)}",
        )
        try:
            result = self._downloader.download(job)
        except DownloadError as exc:
            message = str(exc)
            self._queue.mark_failed(job.id, message)
            self._telegram.send_message(
                job.chat_id,
                f"Download failed #{job.id}: {message}",
            )
            return True

        self._queue.mark_succeeded(job.id, result.file_path)
        self._deliverer.deliver(
            chat_id=job.chat_id,
            job_id=job.id,
            file_path=result.file_path,
        )
        return True


def _title_no_from_url(url: str) -> str:
    return urlsplit(url).path.rsplit("/", maxsplit=1)[-1]
