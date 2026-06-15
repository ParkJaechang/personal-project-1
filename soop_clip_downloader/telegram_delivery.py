"""Telegram delivery decision helpers."""

from __future__ import annotations

from dataclasses import dataclass


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

    max_default_upload_bytes = max_default_upload_mb * 1024 * 1024
    if file_size_bytes <= max_default_upload_bytes:
        return DeliveryDecision(
            method="telegram_direct",
            reason="file is within the default Bot API upload limit",
        )

    if local_bot_api_base_url:
        return DeliveryDecision(
            method="telegram_local_api",
            reason="file exceeds default limit but local Bot API is configured",
        )

    return DeliveryDecision(
        method="saved_path_only",
        reason="file exceeds upload limit and local Bot API is not configured",
    )
