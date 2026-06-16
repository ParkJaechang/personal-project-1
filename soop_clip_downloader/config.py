"""Environment configuration for the downloader service."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


class ConfigError(ValueError):
    """Raised when required service configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_allowed_chat_id: int
    download_dir: Path
    max_telegram_upload_mb: int
    telegram_api_base_url: str | None
    ytdlp_path: str
    ffmpeg_path: str


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load service settings from an environment mapping."""

    source = os.environ if environ is None else environ
    token = _required(source, "TELEGRAM_BOT_TOKEN")
    chat_id = _required_int(source, "TELEGRAM_ALLOWED_CHAT_ID")

    return Settings(
        telegram_bot_token=token,
        telegram_allowed_chat_id=chat_id,
        download_dir=Path(source.get("DOWNLOAD_DIR", "downloads")),
        max_telegram_upload_mb=_optional_int(
            source, "MAX_TELEGRAM_UPLOAD_MB", default=500
        ),
        telegram_api_base_url=_optional_non_empty(source, "TELEGRAM_API_BASE_URL"),
        ytdlp_path=source.get("YTDLP_PATH", "yt-dlp"),
        ffmpeg_path=source.get("FFMPEG_PATH", "ffmpeg"),
    )


def _required(source: Mapping[str, str], name: str) -> str:
    value = source.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is required")
    return value


def _required_int(source: Mapping[str, str], name: str) -> int:
    value = _required(source, name)
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _optional_int(source: Mapping[str, str], name: str, *, default: int) -> int:
    value = source.get(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _optional_non_empty(source: Mapping[str, str], name: str) -> str | None:
    value = source.get(name, "").strip()
    return value or None
