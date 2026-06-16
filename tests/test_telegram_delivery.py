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
            file_size_bytes=75 * 1024 * 1024,
            max_default_upload_mb=500,
            local_bot_api_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(decision.method, "telegram_local_api")
        self.assertEqual(
            decision.reason,
            "file exceeds default Bot API limit but is within configured upload limit",
        )

    def test_uses_local_bot_api_for_500mb_supported_files(self):
        decision = choose_delivery_method(
            file_size_bytes=400 * 1024 * 1024,
            max_default_upload_mb=500,
            local_bot_api_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(decision.method, "telegram_local_api")
        self.assertEqual(
            decision.reason,
            "file exceeds default Bot API limit but is within configured upload limit",
        )

    def test_uses_local_bot_api_for_2000mb_supported_files(self):
        decision = choose_delivery_method(
            file_size_bytes=1500 * 1024 * 1024,
            max_default_upload_mb=2000,
            local_bot_api_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(decision.method, "telegram_local_api")
        self.assertEqual(
            decision.reason,
            "file exceeds default Bot API limit but is within configured upload limit",
        )

    def test_reports_path_for_500mb_supported_files_without_local_api(self):
        decision = choose_delivery_method(
            file_size_bytes=400 * 1024 * 1024,
            max_default_upload_mb=500,
            local_bot_api_base_url=None,
        )

        self.assertEqual(decision.method, "saved_path_only")
        self.assertEqual(
            decision.reason,
            "file is within configured upload limit but local Bot API is not configured",
        )

    def test_reports_path_for_files_above_configured_upload_limit(self):
        decision = choose_delivery_method(
            file_size_bytes=600 * 1024 * 1024,
            max_default_upload_mb=500,
            local_bot_api_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(decision.method, "saved_path_only")
        self.assertEqual(
            decision.reason,
            "file exceeds configured upload limit",
        )

    def test_reports_path_above_2000mb_local_api_limit(self):
        decision = choose_delivery_method(
            file_size_bytes=2100 * 1024 * 1024,
            max_default_upload_mb=2000,
            local_bot_api_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(decision.method, "saved_path_only")
        self.assertEqual(
            decision.reason,
            "file exceeds configured upload limit",
        )

    def test_reports_saved_path_when_file_exceeds_configured_limit(self):
        decision = choose_delivery_method(
            file_size_bytes=400 * 1024 * 1024,
            max_default_upload_mb=50,
            local_bot_api_base_url=None,
        )

        self.assertEqual(decision.method, "saved_path_only")
        self.assertEqual(
            decision.reason,
            "file exceeds configured upload limit",
        )


if __name__ == "__main__":
    unittest.main()
