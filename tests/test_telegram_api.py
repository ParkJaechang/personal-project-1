import unittest

from soop_clip_downloader.telegram_api import TelegramClient


class FakeTransport:
    def __init__(self):
        self.posts = []

    def post_json(self, url: str, data: dict) -> dict:
        self.posts.append((url, data))
        return {"ok": True, "result": []}


class TelegramClientTests(unittest.TestCase):
    def test_send_message_uses_default_bot_api_url(self):
        transport = FakeTransport()
        client = TelegramClient(token="123:abc", transport=transport)

        client.send_message(chat_id=100, text="queued")

        self.assertEqual(
            transport.posts,
            [
                (
                    "https://api.telegram.org/bot123:abc/sendMessage",
                    {"chat_id": 100, "text": "queued"},
                )
            ],
        )

    def test_local_api_base_url_is_trimmed(self):
        transport = FakeTransport()
        client = TelegramClient(
            token="123:abc",
            transport=transport,
            api_base_url="http://127.0.0.1:8081/",
        )

        client.send_message(chat_id=100, text="queued")

        self.assertEqual(
            transport.posts[0][0],
            "http://127.0.0.1:8081/bot123:abc/sendMessage",
        )

    def test_get_updates_posts_offset_and_timeout(self):
        transport = FakeTransport()
        client = TelegramClient(token="123:abc", transport=transport)

        client.get_updates(offset=42, timeout_seconds=20)

        self.assertEqual(
            transport.posts,
            [
                (
                    "https://api.telegram.org/bot123:abc/getUpdates",
                    {"offset": 42, "timeout": 20},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
