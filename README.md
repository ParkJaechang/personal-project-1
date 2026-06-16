# Personal Project 1: SOOP Telegram Clip Downloader

Windows-friendly Telegram bot service for downloading SOOP User Clip links at up to 1080p.

## Goal

Send a SOOP User Clip URL from a phone to a Telegram bot. This PC receives the message, downloads the clip with `yt-dlp` at the best available quality up to 1080p, and reports or sends the result back through Telegram.

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

GitHub repository:

```text
https://github.com/ParkJaechang/personal-project-1
```

## Current Status

- Product design is written in `docs/superpowers/specs/2026-06-16-soop-telegram-clip-downloader-design.md`.
- Implementation plan is written in `docs/superpowers/plans/2026-06-16-soop-telegram-clip-downloader-implementation.md`.
- Work branch: `codex/soop-telegram-downloader`.
- Implemented slices: URL parsing, Telegram delivery decisions, yt-dlp command construction, environment configuration, Telegram polling, job queue, downloader runner, runtime wiring, and completed-file delivery.
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
python -m pip install -e .
```

Copy `.env.example` to `.env` and fill in the real values. Do not commit `.env`.

Run the service from PowerShell:

```powershell
.\scripts\run-service.ps1
```

Manage registered local bots from PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\bots.ps1 list
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\bots.ps1 status soop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\bots.ps1 start soop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\bots.ps1 stop soop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\bots.ps1 restart soop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\bots.ps1 logs soop
```

Create one desktop shortcut for the SOOP tools GUI:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\create-bot-manager-shortcut.ps1
```

Then open `app manager` from the desktop to start, stop, restart, refresh, or open logs/downloads for registered apps.

Or run the Python package directly after exporting the environment variables:

```powershell
python -m soop_clip_downloader
```

## Test

```powershell
python -m unittest discover -s tests -v
```

## Operations

- Real Telegram smoke test: `docs/TELEGRAM_SMOKE_TEST.md`
- Windows startup registration: `docs/WINDOWS_STARTUP.md`
- Default configured delivery target: 500 MB.

## Important Notes

- Keep secrets out of Git.
- The default Telegram Bot API can send videos only up to 50 MB.
- A local Telegram Bot API server is required to deliver larger clips, such as 500 MB files, directly through Telegram.
- If large-file Telegram upload is not configured, the service saves the MP4 locally and sends the path.
