# Telegram Smoke Test

Use this after the code is installed on the Windows PC and the bot token is ready.

## 1. Prepare Tools

Install or update `yt-dlp`:

```powershell
python -m pip install -U yt-dlp
yt-dlp --version
```

Install `ffmpeg` and confirm it is on `PATH`:

```powershell
ffmpeg -version
```

If `ffmpeg` is not installed, one Windows option is:

```powershell
winget install Gyan.FFmpeg
```

Close and reopen PowerShell after installing command-line tools.

## 2. Create the Telegram Bot

1. In Telegram, open `@BotFather`.
2. Send `/newbot`.
3. Save the bot token in `.env` as `TELEGRAM_BOT_TOKEN`.
4. Start a chat with the new bot from the phone.
5. Send any text message to the bot, such as `hello`.

## 3. Discover the Allowed Chat ID

In PowerShell, set the token for the current shell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "replace-with-real-token"
```

Fetch recent updates:

```powershell
Invoke-RestMethod "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/getUpdates" |
  ConvertTo-Json -Depth 20
```

Find `result.message.chat.id` and save it in `.env` as `TELEGRAM_ALLOWED_CHAT_ID`.

## 4. Fill `.env`

Use `.env.example` as the template:

```text
TELEGRAM_BOT_TOKEN=replace-with-real-token
TELEGRAM_ALLOWED_CHAT_ID=123456789
DOWNLOAD_DIR=downloads
MAX_TELEGRAM_UPLOAD_MB=2000
TELEGRAM_API_BASE_URL=
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_LOCAL_API_PORT=8081
TELEGRAM_LOCAL_FILE_URI_BASE=file:///telegram-files
YTDLP_PATH=yt-dlp
FFMPEG_PATH=ffmpeg
```

Leave `TELEGRAM_API_BASE_URL` empty unless a local Telegram Bot API server is running.

## 5. Verify SOOP User Clip Download Support

Run this with a known public SOOP User Clip URL:

```powershell
yt-dlp -F "https://vod.sooplive.com/player/{title_no}"
```

Expected: `yt-dlp` lists formats, including a 1080p or lower format that can be selected by `best[height<=1080]`.

## 6. Run the Bot Service

```powershell
.\scripts\run-service.ps1
```

From the phone, send a supported User Clip URL:

```text
https://vod.sooplive.com/player/{title_no}
```

Expected Telegram replies:

1. `Queued download: {title_no}`
2. `Starting download #1: {title_no}`
3. Either the uploaded MP4 or `Download complete #1: <local path>`

Catch URLs such as `https://vod.sooplive.com/player/{title_no}/catch` are intentionally rejected.

## 7. 2000 MB Clip Behavior

The service is configured for clips up to 2000 MB by default.

The default Telegram Bot API can send videos only up to 50 MB. To receive clips larger than 50 MB, up to the local Bot API limit of 2000 MB, directly as Telegram files, configure a local Telegram Bot API server in `TELEGRAM_API_BASE_URL`.

The local Telegram Bot API server supports larger uploads, including local file URI uploads, according to Telegram's Bot API documentation:

```text
https://core.telegram.org/bots/api#using-a-local-bot-api-server
```

If `TELEGRAM_API_BASE_URL` is empty and the output file is above the default Bot API 50 MB limit, the bot reports the saved local path instead of trying to upload it.

If the output file is above `MAX_TELEGRAM_UPLOAD_MB`, the bot also reports the saved local path instead of trying a Telegram file upload.
