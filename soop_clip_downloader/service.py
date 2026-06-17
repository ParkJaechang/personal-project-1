"""Polling service and download worker wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from soop_clip_downloader.downloader import DownloadProgress
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
    def download(self, job, progress_callback=None):
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
        progress = TelegramProgressReporter(
            telegram=self._telegram,
            chat_id=job.chat_id,
            job_id=job.id,
        )
        progress.start()
        try:
            result = self._downloader.download(job, progress_callback=progress.update)
        except DownloadError as exc:
            message = str(exc)
            self._queue.mark_failed(job.id, message)
            progress.fail(message)
            self._telegram.send_message(
                job.chat_id,
                f"Download failed #{job.id}: {message}",
            )
            return True

        self._queue.mark_succeeded(job.id, result.file_path)
        progress.complete()
        self._telegram.send_message(
            job.chat_id,
            (
                f"Download finished #{job.id}: {result.file_path} "
                f"({_file_size_mb(result.file_path):.1f} MB). Sending to Telegram..."
            ),
        )
        self._deliverer.deliver(
            chat_id=job.chat_id,
            job_id=job.id,
            file_path=result.file_path,
        )
        return True


class TelegramProgressReporter:
    def __init__(
        self,
        *,
        telegram: TelegramGateway,
        chat_id: int,
        job_id: int,
        min_percent_delta: float = 5.0,
    ) -> None:
        self._telegram = telegram
        self._chat_id = chat_id
        self._job_id = job_id
        self._min_percent_delta = min_percent_delta
        self._message_id: int | None = None
        self._last_percent: float | None = None
        self._disabled = False

    def start(self) -> None:
        try:
            response = self._telegram.send_message(
                self._chat_id,
                f"Download progress #{self._job_id}: starting",
            )
        except Exception:
            self._disabled = True
            return
        self._message_id = _message_id_from_response(response)

    def update(self, progress: DownloadProgress) -> None:
        if self._disabled:
            return
        if not self._should_report(progress.percent):
            return
        self._last_percent = progress.percent
        self._publish(_format_progress_message(self._job_id, progress))

    def complete(self) -> None:
        self._publish(f"Download progress #{self._job_id}: complete")

    def fail(self, message: str) -> None:
        self._publish(f"Download progress #{self._job_id}: failed - {message}")

    def _should_report(self, percent: float) -> bool:
        if self._last_percent is None:
            return True
        if percent >= 100:
            return True
        return percent - self._last_percent >= self._min_percent_delta

    def _publish(self, text: str) -> None:
        if self._disabled:
            return
        if self._message_id is not None and hasattr(self._telegram, "edit_message_text"):
            try:
                self._telegram.edit_message_text(
                    chat_id=self._chat_id,
                    message_id=self._message_id,
                    text=text,
                )
            except Exception:
                self._disabled = True
            return
        try:
            self._telegram.send_message(self._chat_id, text)
        except Exception:
            self._disabled = True


def _title_no_from_url(url: str) -> str:
    return urlsplit(url).path.rsplit("/", maxsplit=1)[-1]


def _message_id_from_response(response: object) -> int | None:
    if not isinstance(response, dict):
        return None
    result = response.get("result")
    if not isinstance(result, dict):
        return None
    message_id = result.get("message_id")
    return message_id if isinstance(message_id, int) else None


def _format_progress_message(job_id: int, progress: DownloadProgress) -> str:
    parts = [f"Download progress #{job_id}: {progress.percent:.1f}%"]
    if progress.eta:
        parts.append(f"ETA {progress.eta}")
    if progress.speed:
        parts.append(progress.speed)
    return " | ".join(parts)


def _file_size_mb(file_path) -> float:
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0.0
