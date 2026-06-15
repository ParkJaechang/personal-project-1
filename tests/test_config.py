from pathlib import Path
import unittest

from soop_clip_downloader.config import ConfigError, load_settings


class ConfigTests(unittest.TestCase):
    def test_loads_required_telegram_settings_and_defaults(self):
        settings = load_settings(
            {
                "TELEGRAM_BOT_TOKEN": "123:abc",
                "TELEGRAM_ALLOWED_CHAT_ID": "987654321",
            }
        )

        self.assertEqual(settings.telegram_bot_token, "123:abc")
        self.assertEqual(settings.telegram_allowed_chat_id, 987654321)
        self.assertEqual(settings.download_dir, Path("downloads"))
        self.assertEqual(settings.max_telegram_upload_mb, 50)
        self.assertIsNone(settings.telegram_api_base_url)
        self.assertEqual(settings.ytdlp_path, "yt-dlp")
        self.assertEqual(settings.ffmpeg_path, "ffmpeg")

    def test_loads_optional_values(self):
        settings = load_settings(
            {
                "TELEGRAM_BOT_TOKEN": "123:abc",
                "TELEGRAM_ALLOWED_CHAT_ID": "987654321",
                "DOWNLOAD_DIR": "D:/clips",
                "MAX_TELEGRAM_UPLOAD_MB": "100",
                "TELEGRAM_API_BASE_URL": "http://127.0.0.1:8081",
                "YTDLP_PATH": "python -m yt_dlp",
                "FFMPEG_PATH": "C:/tools/ffmpeg.exe",
            }
        )

        self.assertEqual(settings.download_dir, Path("D:/clips"))
        self.assertEqual(settings.max_telegram_upload_mb, 100)
        self.assertEqual(settings.telegram_api_base_url, "http://127.0.0.1:8081")
        self.assertEqual(settings.ytdlp_path, "python -m yt_dlp")
        self.assertEqual(settings.ffmpeg_path, "C:/tools/ffmpeg.exe")

    def test_missing_bot_token_raises_clear_error(self):
        with self.assertRaisesRegex(ConfigError, "TELEGRAM_BOT_TOKEN is required"):
            load_settings({"TELEGRAM_ALLOWED_CHAT_ID": "987654321"})

    def test_invalid_chat_id_raises_clear_error(self):
        with self.assertRaisesRegex(
            ConfigError, "TELEGRAM_ALLOWED_CHAT_ID must be an integer"
        ):
            load_settings(
                {
                    "TELEGRAM_BOT_TOKEN": "123:abc",
                    "TELEGRAM_ALLOWED_CHAT_ID": "not-a-number",
                }
            )


if __name__ == "__main__":
    unittest.main()
