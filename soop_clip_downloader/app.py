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


class ClipBotApp:
    def __init__(
        self,
        *,
        allowed_chat_id: int,
        telegram: TelegramResponder,
        job_queue: JobQueue,
    ) -> None:
        self._allowed_chat_id = allowed_chat_id
        self._telegram = telegram
        self._job_queue = job_queue

    def handle_text_message(self, *, chat_id: int, text: str) -> None:
        """Handle one inbound Telegram text message."""

        if chat_id != self._allowed_chat_id:
            return

        urls = extract_soop_user_clip_urls(text)
        if not urls:
            self._telegram.send_message(
                chat_id,
                "지원하는 SOOP 유저클립 링크를 찾지 못했어요. "
                "https://vod.sooplive.com/player/{번호} 형식만 지원합니다.",
            )
            return

        for url in urls:
            self._job_queue.enqueue(url, chat_id)
            self._telegram.send_message(
                chat_id,
                f"다운로드 대기열에 추가했어요: {_title_no_from_url(url)}",
            )


def _title_no_from_url(url: str) -> str:
    return urlsplit(url).path.rsplit("/", maxsplit=1)[-1]
