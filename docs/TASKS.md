# Tasks

## Now

- [x] Create GitHub repository `ParkJaechang/personal-project-1`.
- [x] Add local `origin` remote and push `master` plus `codex/soop-telegram-downloader`.
- [x] Finish Task 2 in the implementation plan: URL parsing.
- [x] Finish Task 3 in the implementation plan: Telegram delivery decisions.
- [x] Finish Task 4 in the implementation plan: yt-dlp command builder.

## Next

- [x] Add configuration loading from environment variables.
- [x] Add Telegram message orchestration for allowed chat, unsupported links, and queued links.
- [x] Add Telegram Bot API client with polling.
- [x] Add job queue and downloader subprocess runner.
- [x] Wire runtime entrypoint and completed-file delivery.
- [x] Add real Telegram smoke test instructions.
- [x] Add Windows startup instructions.

## External Setup Needed

- [ ] Create a Telegram bot with BotFather.
- [ ] Record `TELEGRAM_BOT_TOKEN` in local `.env`.
- [ ] Send a message to the bot and discover `TELEGRAM_ALLOWED_CHAT_ID`.
- [ ] Install or configure current `yt-dlp`.
- [ ] Install or configure `ffmpeg`.
