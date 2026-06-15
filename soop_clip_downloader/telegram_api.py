"""Telegram Bot API client boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol
import uuid
from urllib import parse, request


class JsonTransport(Protocol):
    def post_json(self, url: str, data: dict) -> dict:
        """POST form data and return the decoded JSON response."""

    def post_multipart_file(
        self,
        url: str,
        fields: dict,
        *,
        file_field: str,
        file_path: Path,
        mime_type: str,
    ) -> dict:
        """POST multipart form data with one local file."""


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

    def post_multipart_file(
        self,
        url: str,
        fields: dict,
        *,
        file_field: str,
        file_path: Path,
        mime_type: str,
    ) -> dict:
        boundary = f"soop-clip-{uuid.uuid4().hex}"
        body = _multipart_body(
            boundary=boundary,
            fields=fields,
            file_field=file_field,
            file_path=file_path,
            mime_type=mime_type,
        )
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        with request.urlopen(req, timeout=300) as response:
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

    def send_message(self, chat_id: int, text: str) -> dict:
        return self._transport.post_json(
            self._method_url("sendMessage"),
            {"chat_id": chat_id, "text": text},
        )

    def send_video_path(
        self,
        chat_id: int,
        file_path: Path,
        caption: str | None = None,
    ) -> dict:
        payload = {
            "chat_id": chat_id,
            "video": Path(file_path).resolve().as_uri(),
            "supports_streaming": "true",
        }
        if caption:
            payload["caption"] = caption
        return self._transport.post_json(self._method_url("sendVideo"), payload)

    def send_video_file(
        self,
        chat_id: int,
        file_path: Path,
        caption: str | None = None,
    ) -> dict:
        fields = {
            "chat_id": chat_id,
            "supports_streaming": "true",
        }
        if caption:
            fields["caption"] = caption
        return self._transport.post_multipart_file(
            self._method_url("sendVideo"),
            fields,
            file_field="video",
            file_path=file_path,
            mime_type="video/mp4",
        )

    def _method_url(self, method: str) -> str:
        return f"{self._api_base_url}/bot{self._token}/{method}"


def _multipart_body(
    *,
    boundary: str,
    fields: dict,
    file_field: str,
    file_path: Path,
    mime_type: str,
) -> bytes:
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{file_path.name}"\r\n'
        ).encode("utf-8")
    )
    body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
    body.extend(file_path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body)
