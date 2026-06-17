"""Telegram message orchestration for SOOP clip downloads."""

from __future__ import annotations

from typing import Protocol
from urllib.parse import urlsplit

from soop_clip_downloader.url_tools import extract_soop_user_clip_urls


class TelegramResponder(Protocol):
    def send_message(self, chat_id: int, text: str) -> None:
        """Send a text message to a Telegram chat."""


class JobQueue(Protocol):
    def enqueue(self, url: str, chat_id: int) -> None:
        """Queue a clip download job for the given chat."""

    def cancel_pending(self, reason: str) -> int:
        """Cancel queued jobs and return how many were cancelled."""


class DownloadController(Protocol):
    def request_stop(self) -> bool:
        """Request cancellation of the active download, if any."""


class ClipBotApp:
    def __init__(
        self,
        *,
        allowed_chat_id: int,
        telegram: TelegramResponder,
        job_queue: JobQueue,
        download_controller: DownloadController | None = None,
    ) -> None:
        self._allowed_chat_id = allowed_chat_id
        self._telegram = telegram
        self._job_queue = job_queue
        self._download_controller = download_controller

    def handle_text_message(self, *, chat_id: int, text: str) -> None:
        """Handle one inbound Telegram text message."""

        if chat_id != self._allowed_chat_id:
            return

        if _is_stop_command(text):
            active = (
                self._download_controller.request_stop()
                if self._download_controller is not None
                else False
            )
            pending_count = self._job_queue.cancel_pending("cancelled by user")
            self._telegram.send_message(
                chat_id,
                _format_stop_response(active=active, pending_count=pending_count),
            )
            return

        urls = extract_soop_user_clip_urls(text)
        if not urls:
            self._telegram.send_message(
                chat_id,
                "No supported SOOP User Clip URL found. "
                "Use https://vod.sooplive.com/player/{id}.",
            )
            return

        for url in urls:
            self._job_queue.enqueue(url, chat_id)
            self._telegram.send_message(
                chat_id,
                f"Queued download: {_title_no_from_url(url)}",
            )


def _title_no_from_url(url: str) -> str:
    return urlsplit(url).path.rsplit("/", maxsplit=1)[-1]


def _is_stop_command(text: str) -> bool:
    command = text.strip().split(maxsplit=1)[0].lower() if text.strip() else ""
    command = command.split("@", maxsplit=1)[0]
    return command in {"/stop", "/cancel", "stop", "cancel", "중단", "취소"}


def _format_stop_response(*, active: bool, pending_count: int) -> str:
    if active and pending_count:
        return (
            "Stop requested. Active download will cancel shortly. "
            f"Cleared {pending_count} queued download(s)."
        )
    if active:
        return "Stop requested. Active download will cancel shortly."
    if pending_count:
        return f"Cleared {pending_count} queued download(s)."
    return "No active or queued download to stop."
