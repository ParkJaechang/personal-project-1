"""Telegram Bot API client boundary."""

from __future__ import annotations

import json
from typing import Protocol
from urllib import parse, request


class JsonTransport(Protocol):
    def post_json(self, url: str, data: dict) -> dict:
        """POST form data and return the decoded JSON response."""


class UrllibJsonTransport:
    def post_json(self, url: str, data: dict) -> dict:
        encoded = parse.urlencode(data).encode("utf-8")
        req = request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))


class TelegramClient:
    def __init__(
        self,
        *,
        token: str,
        transport: JsonTransport | None = None,
        api_base_url: str | None = None,
    ) -> None:
        self._token = token
        self._transport = transport or UrllibJsonTransport()
        self._api_base_url = (api_base_url or "https://api.telegram.org").rstrip("/")

    def get_updates(self, *, offset: int | None = None, timeout_seconds: int = 30) -> dict:
        payload: dict[str, int] = {"timeout": timeout_seconds}
        if offset is not None:
            payload["offset"] = offset
        return self._transport.post_json(self._method_url("getUpdates"), payload)

    def send_message(self, *, chat_id: int, text: str) -> dict:
        return self._transport.post_json(
            self._method_url("sendMessage"),
            {"chat_id": chat_id, "text": text},
        )

    def _method_url(self, method: str) -> str:
        return f"{self._api_base_url}/bot{self._token}/{method}"
