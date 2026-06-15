import unittest

from soop_clip_downloader.url_tools import (
    extract_soop_user_clip_urls,
    is_supported_soop_user_clip_url,
    normalize_soop_user_clip_url,
)


class UrlToolsTests(unittest.TestCase):
    def test_extracts_unique_user_clip_urls_from_message(self):
        text = """
        save this https://vod.sooplive.com/player/195880425
        and this one too: https://vod.sooplive.com/player/197299925?foo=bar
        duplicate https://vod.sooplive.com/player/195880425
        """

        self.assertEqual(
            extract_soop_user_clip_urls(text),
            [
                "https://vod.sooplive.com/player/195880425",
                "https://vod.sooplive.com/player/197299925",
            ],
        )

    def test_rejects_catch_urls(self):
        self.assertFalse(
            is_supported_soop_user_clip_url(
                "https://vod.sooplive.com/player/197121517/catch"
            )
        )

    def test_normalizes_legacy_domain_to_current_domain(self):
        self.assertEqual(
            normalize_soop_user_clip_url(
                "https://vod.sooplive.co.kr/player/198263283"
            ),
            "https://vod.sooplive.com/player/198263283",
        )


if __name__ == "__main__":
    unittest.main()
