# Personal Project 1: SOOP Telegram Clip Downloader

Windows-friendly Telegram bot service for downloading SOOP User Clip links in original quality.

## Goal

Send a SOOP User Clip URL from a phone to a Telegram bot. This PC receives the message, downloads the clip with `yt-dlp` in original quality when available, and reports or sends the result back through Telegram.

Supported URL shape:

```text
https://vod.sooplive.com/player/{title_no}
```

Not in scope for the first version:

```text
https://vod.sooplive.com/player/{title_no}/catch
```

## Repository

Intended GitHub repository:

```text
ParkJaechang/personal-project-1
```

Display title requested by the user:

```text
Personal Project 1
```

GitHub repository creation is pending if this document is still only local. The GitHub connector available in this environment can read and edit existing repositories, but it did not expose a create-repository tool, and `gh` is not installed on this PC.

## Current Status

- Product design is written in `docs/superpowers/specs/2026-06-16-soop-telegram-clip-downloader-design.md`.
- Implementation plan is written in `docs/superpowers/plans/2026-06-16-soop-telegram-clip-downloader-implementation.md`.
- Work branch: `codex/soop-telegram-downloader`.
- First implementation slice: URL parsing, Telegram delivery decisions, and yt-dlp command construction.
- Local warning: this workspace may contain untracked files for a different `personal-project-2` / `soop_summary` effort. Do not stage those files for this repository.

## Requirements

- Python 3.11 or newer
- `yt-dlp` version `2026.06.09` or newer
- `ffmpeg`
- Telegram bot token from BotFather

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Copy `.env.example` to `.env` and fill in the real values. Do not commit `.env`.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Important Notes

- Keep secrets out of Git.
- Default Telegram Bot API uploads may be too small for original-quality SOOP clips.
- A local Telegram Bot API server can be added later for large file transfer.
- If large-file Telegram upload is not configured, the service should save the MP4 locally and send the path.
