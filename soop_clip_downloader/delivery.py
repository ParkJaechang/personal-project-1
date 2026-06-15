"""Completed file delivery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from soop_clip_downloader.telegram_delivery import choose_delivery_method


@dataclass(frozen=True)
class DeliveryOutcome:
    method: str
    message: str


class TelegramFileSender(Protocol):
    def send_message(self, chat_id: int, text: str) -> object:
        """Send a text message."""

    def send_video_file(
        self,
        chat_id: int,
        file_path: Path,
        caption: str | None = None,
    ) -> object:
        """Upload a local video file through multipart form data."""

    def send_video_path(
        self,
        chat_id: int,
        file_path: Path,
        caption: str | None = None,
    ) -> object:
        """Send a local file URI through a local Telegram Bot API server."""


class PathOnlyDeliverer:
    def __init__(self, *, telegram: TelegramFileSender) -> None:
        self._telegram = telegram

    def deliver(self, *, chat_id: int, job_id: int, file_path: Path) -> DeliveryOutcome:
        message = f"Download complete #{job_id}: {file_path}"
        self._telegram.send_message(chat_id, message)
        return DeliveryOutcome(method="saved_path_only", message=message)


class CompletedFileDeliverer:
    def __init__(
        self,
        *,
        telegram: TelegramFileSender,
        max_default_upload_mb: int,
        local_bot_api_base_url: str | None,
    ) -> None:
        self._telegram = telegram
        self._max_default_upload_mb = max_default_upload_mb
        self._local_bot_api_base_url = local_bot_api_base_url

    def deliver(self, *, chat_id: int, job_id: int, file_path: Path) -> DeliveryOutcome:
        decision = choose_delivery_method(
            file_size_bytes=file_path.stat().st_size,
            max_default_upload_mb=self._max_default_upload_mb,
            local_bot_api_base_url=self._local_bot_api_base_url,
        )
        caption = f"SOOP clip #{job_id}"

        if decision.method == "telegram_direct":
            try:
                self._telegram.send_video_file(chat_id, file_path, caption=caption)
                return DeliveryOutcome(
                    method=decision.method,
                    message=f"Download complete #{job_id}: sent video",
                )
            except Exception:
                return self._send_saved_path(
                    chat_id=chat_id,
                    job_id=job_id,
                    file_path=file_path,
                )

        if decision.method == "telegram_local_api":
            try:
                self._telegram.send_video_path(chat_id, file_path, caption=caption)
                return DeliveryOutcome(
                    method=decision.method,
                    message=f"Download complete #{job_id}: sent through local Bot API",
                )
            except Exception:
                return self._send_saved_path(
                    chat_id=chat_id,
                    job_id=job_id,
                    file_path=file_path,
                )

        return self._send_saved_path(chat_id=chat_id, job_id=job_id, file_path=file_path)

    def _send_saved_path(
        self,
        *,
        chat_id: int,
        job_id: int,
        file_path: Path,
    ) -> DeliveryOutcome:
        message = f"Download complete #{job_id}: {file_path}"
        self._telegram.send_message(chat_id, message)
        return DeliveryOutcome(method="saved_path_only", message=message)
