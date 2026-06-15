"""Utilities for SOOP User Clip URLs."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

_CANDIDATE_URL_RE = re.compile(
    r"https?://vod\.sooplive\.(?:com|co\.kr)/player/\d+(?:[/?#][^\s<>'\"]*)?",
    re.IGNORECASE,
)
_PLAYER_PATH_RE = re.compile(r"^/player/(?P<title_no>\d+)/?$")


def normalize_soop_user_clip_url(url: str) -> str:
    """Return the canonical SOOP User Clip player URL.

    Query strings and fragments are intentionally dropped because `yt-dlp`
    only needs the player title number.
    """

    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("SOOP URL must use http or https")

    host = (parsed.hostname or "").lower()
    if host not in {"vod.sooplive.com", "vod.sooplive.co.kr"}:
        raise ValueError("SOOP URL must use the VOD host")

    match = _PLAYER_PATH_RE.fullmatch(parsed.path)
    if not match:
        raise ValueError("SOOP URL must be a User Clip player URL")

    return f"https://vod.sooplive.com/player/{match.group('title_no')}"


def is_supported_soop_user_clip_url(url: str) -> bool:
    """Return true when `url` is a supported SOOP User Clip player URL."""

    try:
        normalize_soop_user_clip_url(url)
    except ValueError:
        return False
    return True


def extract_soop_user_clip_urls(text: str) -> list[str]:
    """Extract unique supported SOOP User Clip URLs from arbitrary text."""

    urls: list[str] = []
    seen: set[str] = set()
    for match in _CANDIDATE_URL_RE.finditer(text):
        candidate = match.group(0).rstrip(".,)]}")
        try:
            normalized = normalize_soop_user_clip_url(candidate)
        except ValueError:
            continue
        if normalized not in seen:
            seen.add(normalized)
            urls.append(normalized)
    return urls
