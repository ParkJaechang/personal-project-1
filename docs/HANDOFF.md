# Handoff

## What This Project Is

This project builds a small PC service controlled from Telegram. The user sends a SOOP User Clip link from their phone. The PC downloads the clip in original quality using `yt-dlp` and then replies in Telegram with either the file or the saved local path.

## User Intent

The user wants a personal automation service, not a public website. The important workflow is:

1. Phone sends SOOP User Clip URL to Telegram bot.
2. PC receives it.
3. PC downloads the original-quality video.
4. PC reports completion and sends the video when practical.

## Scope Decisions

- Support SOOP User Clip URLs: `https://vod.sooplive.com/player/{number}`.
- Reject SOOP Catch URLs: `https://vod.sooplive.com/player/{number}/catch`.
- Use Telegram polling first. Do not expose a public web server.
- Start with local saves and small-file Telegram upload.
- Support local Telegram Bot API server local-path upload when configured.

## Verified Facts

- On 2026-06-16 KST, latest `yt-dlp` from PyPI was `2026.06.09`.
- `yt-dlp 2026.06.09` recognized public SOOP User Clip URLs using `vod.sooplive.com/player/{number}`.
- The older globally installed `yt-dlp 2025.12.08` on this PC did not recognize the new SOOP `.com` URL form.
- `ffmpeg` was not found on PATH at the time of initial inspection.
- `gh` was not installed on this PC, but browser-based GitHub repo creation and HTTPS `git push` worked after login.
- GitHub connected account: `ParkJaechang`.
- Intended remote repository: `ParkJaechang/personal-project-1`.
- Created remote repository: `https://github.com/ParkJaechang/personal-project-1`.

## Current Local Git State

- Branch: `codex/soop-telegram-downloader`.
- Initial design commit exists on local history.
- `master` and `codex/soop-telegram-downloader` were pushed to `origin`.
- Core test slices implemented: URL parsing, Telegram delivery decision, yt-dlp command building, config loading, Telegram polling, job queue, downloader runner, runtime wiring, and completed-file delivery.
- Run the service with `.\scripts\run-service.ps1` or `python -m soop_clip_downloader` after environment variables are loaded.
- Real Telegram verification steps are in `docs/TELEGRAM_SMOKE_TEST.md`.
- Windows startup registration steps are in `docs/WINDOWS_STARTUP.md`.
- The current workspace may contain untracked files for a separate `personal-project-2` / `soop_summary` effort. They are not part of this project and should not be staged for `Personal Project 1`.

## Continue From Another PC

1. Clone `https://github.com/ParkJaechang/personal-project-1.git` if the repo exists.
2. Read this file first.
3. Read `README.md`.
4. Read the design spec in `docs/superpowers/specs/`.
5. Read the implementation plan in `docs/superpowers/plans/`.
6. Run `python -m unittest discover -s tests -v`.
7. Continue from `docs/TASKS.md`.

Continue on branch `codex/soop-telegram-downloader`.
