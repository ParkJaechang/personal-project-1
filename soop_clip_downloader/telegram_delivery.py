"""Telegram delivery decision helpers."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_BOT_API_UPLOAD_MB = 50


@dataclass(frozen=True)
class DeliveryDecision:
    """Represents how a completed MP4 should be reported to Telegram."""

    method: str
    reason: str


def choose_delivery_method(
    *,
    file_size_bytes: int,
    max_default_upload_mb: int,
    local_bot_api_base_url: str | None,
) -> DeliveryDecision:
    """Choose the safest available delivery method for a completed file."""

    default_bot_api_upload_bytes = DEFAULT_BOT_API_UPLOAD_MB * 1024 * 1024
    configured_upload_bytes = max_default_upload_mb * 1024 * 1024
    if file_size_bytes <= min(default_bot_api_upload_bytes, configured_upload_bytes):
        return DeliveryDecision(
            method="telegram_direct",
            reason="file is within the default Bot API upload limit",
        )

    if file_size_bytes > configured_upload_bytes:
        return DeliveryDecision(
            method="saved_path_only",
            reason="file exceeds configured upload limit",
        )

    if local_bot_api_base_url:
        return DeliveryDecision(
            method="telegram_local_api",
            reason=(
                "file exceeds default Bot API limit but is within configured upload limit"
            ),
        )

    return DeliveryDecision(
        method="saved_path_only",
        reason="file is within configured upload limit but local Bot API is not configured",
    )
