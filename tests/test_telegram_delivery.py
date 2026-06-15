import unittest

from soop_clip_downloader.telegram_delivery import choose_delivery_method


class TelegramDeliveryTests(unittest.TestCase):
    def test_uses_default_bot_api_for_small_files(self):
        decision = choose_delivery_method(
            file_size_bytes=25 * 1024 * 1024,
            max_default_upload_mb=50,
            local_bot_api_base_url=None,
        )

        self.assertEqual(decision.method, "telegram_direct")
        self.assertEqual(
            decision.reason,
            "file is within the default Bot API upload limit",
        )

    def test_uses_local_bot_api_for_large_files_when_configured(self):
        decision = choose_delivery_method(
            file_size_bytes=400 * 1024 * 1024,
            max_default_upload_mb=50,
            local_bot_api_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(decision.method, "telegram_local_api")
        self.assertEqual(
            decision.reason,
            "file exceeds default limit but local Bot API is configured",
        )

    def test_reports_saved_path_for_large_files_without_local_api(self):
        decision = choose_delivery_method(
            file_size_bytes=400 * 1024 * 1024,
            max_default_upload_mb=50,
            local_bot_api_base_url=None,
        )

        self.assertEqual(decision.method, "saved_path_only")
        self.assertEqual(
            decision.reason,
            "file exceeds upload limit and local Bot API is not configured",
        )


if __name__ == "__main__":
    unittest.main()
