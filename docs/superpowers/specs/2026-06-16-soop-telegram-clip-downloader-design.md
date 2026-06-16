# SOOP Telegram Clip Downloader Design

## Goal

Build a small Windows PC service that receives SOOP User Clip links from a Telegram bot, downloads the clip at the best available quality up to 1080p, and sends the result or status back to the user's phone through Telegram.

This project targets SOOP User Clip URLs such as:

- `https://vod.sooplive.com/player/{title_no}`

It does not target SOOP Catch URLs such as:

- `https://vod.sooplive.com/player/{title_no}/catch`

## Confirmed Download Path

As of 2026-06-16 KST, public SOOP User Clip pages using `vod.sooplive.com/player/{title_no}` are recognized by `yt-dlp` version `2026.06.09`.

Observed examples exposed HLS formats such as:

- `hls-original` at `1920x1080`
- `hls-original` at `2560x1440`

The currently installed global `yt-dlp` on this PC is older and did not recognize the new SOOP `.com` URLs, so the service should either install or vendor a current `yt-dlp` runtime. `ffmpeg` is required for reliable HLS download and MP4 output.

The active downloader format policy is capped at 1080p to avoid unnecessarily large 1440p source downloads.

## Recommended Approach

Use a Telegram bot as both the input channel and notification channel.

The first version should use a mixed delivery strategy:

- Send small completed MP4 files directly through Telegram through the default Bot API.
- For larger files, prefer a local Telegram Bot API server when configured. Telegram documents that a local Bot API server can upload files up to 2000 MB and can use local file paths.
- If the local Bot API server is not configured, keep the MP4 on the PC and send a completion message with the local file path.

Cloud upload can be added later if phone-side access to large files becomes necessary.

## Architecture

The service has four main components:

1. Telegram bot listener
   - Polls Telegram for messages.
   - Accepts only messages from the configured Telegram chat ID.
   - Extracts SOOP User Clip URLs from message text.

2. Job queue
   - Creates one download job per URL.
   - Processes jobs one at a time to avoid bandwidth and file-lock issues.
   - Reports queued, started, succeeded, and failed states.

3. Downloader
   - Validates that the URL matches `https://vod.sooplive.com/player/{number}`.
   - Calls `yt-dlp` with a best-quality-up-to-1080p format preference.
   - Uses `ffmpeg` for HLS merge/remux.
   - Writes files into a configured downloads directory.

4. Telegram responder
   - Sends progress and error messages.
   - Sends the completed file when it is below the configured default Bot API upload limit.
   - Uses a local Telegram Bot API endpoint for larger files when configured.
   - Sends the local path when direct upload is skipped or unavailable.

## Data Flow

1. User shares a SOOP User Clip URL to the Telegram bot.
2. The service checks the sender chat ID.
3. The service validates the URL shape.
4. A job is queued and acknowledged in Telegram.
5. The downloader runs `yt-dlp` using a 1080p-or-lower quality preference.
6. The output MP4 is saved locally.
7. Telegram receives either the MP4 file or a saved-file notification.

## Configuration

The service should read configuration from an `.env` file that is not committed:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_CHAT_ID`
- `DOWNLOAD_DIR`
- `MAX_TELEGRAM_UPLOAD_MB`
- `TELEGRAM_API_BASE_URL`, optional local Bot API endpoint
- `TELEGRAM_API_ID`, local Bot API server credential
- `TELEGRAM_API_HASH`, local Bot API server credential
- `YTDLP_PATH`, optional
- `FFMPEG_PATH`, optional

## Error Handling

Expected errors should produce clear Telegram messages:

- Unsupported URL: tell the user only SOOP User Clip player URLs are supported.
- Login or age restriction: tell the user the clip may require account access and was not downloaded.
- No 1080p-or-lower format: report the `yt-dlp` selection failure.
- `yt-dlp` failure: include the short final error line.
- Missing `ffmpeg`: tell the user to install or configure `ffmpeg`.
- Telegram upload too large: use the local Bot API endpoint when configured, otherwise save locally and send the path.

## Security

The bot must ignore messages from any chat ID other than the configured allowed chat.

The service should not expose a public web server in the first version. Telegram polling is enough and avoids router or firewall setup.

Secrets must stay in `.env`, which should be ignored by Git.

## Testing

Implementation should include focused tests for:

- SOOP URL extraction from arbitrary Telegram messages.
- URL validation that accepts User Clip player URLs and rejects Catch URLs.
- Format selection preference for 1080p-or-lower output.
- Telegram upload decision based on file size.
- Local Bot API endpoint selection for large files.
- Job status transitions for success and failure.

Manual verification should include:

- `yt-dlp -F` against a known public User Clip URL.
- A real Telegram message from the phone to the bot.
- A completed MP4 saved to the configured download directory.

## References

- SOOP User Clip service notice: https://afwbbs1.sooplive.com/app/index.php?b_no=6521&board=notice&control=view
- SOOP VOD download notice: https://afwbbs1.sooplive.com/app/index.php?b_no=6554&board=notice&control=view
- yt-dlp supported sites: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
- yt-dlp releases: https://github.com/yt-dlp/yt-dlp/releases
- Telegram local Bot API server: https://core.telegram.org/bots/api#using-a-local-bot-api-server
