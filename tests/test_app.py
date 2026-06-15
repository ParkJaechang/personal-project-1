import unittest

from soop_clip_downloader.app import ClipBotApp


class FakeTelegram:
    def __init__(self):
        self.messages = []

    def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class FakeJobQueue:
    def __init__(self):
        self.urls = []

    def enqueue(self, url: str, chat_id: int) -> None:
        self.urls.append((url, chat_id))


class ClipBotAppTests(unittest.TestCase):
    def test_ignores_messages_from_other_chats(self):
        telegram = FakeTelegram()
        queue = FakeJobQueue()
        app = ClipBotApp(
            allowed_chat_id=100,
            telegram=telegram,
            job_queue=queue,
        )

        app.handle_text_message(
            chat_id=200,
            text="https://vod.sooplive.com/player/195880425",
        )

        self.assertEqual(telegram.messages, [])
        self.assertEqual(queue.urls, [])

    def test_replies_when_message_has_no_supported_url(self):
        telegram = FakeTelegram()
        queue = FakeJobQueue()
        app = ClipBotApp(
            allowed_chat_id=100,
            telegram=telegram,
            job_queue=queue,
        )

        app.handle_text_message(
            chat_id=100,
            text="https://vod.sooplive.com/player/197121517/catch",
        )

        self.assertEqual(queue.urls, [])
        self.assertEqual(
            telegram.messages,
            [
                (
                    100,
                    "No supported SOOP User Clip URL found. "
                    "Use https://vod.sooplive.com/player/{id}.",
                )
            ],
        )

    def test_enqueues_each_supported_url_and_acknowledges(self):
        telegram = FakeTelegram()
        queue = FakeJobQueue()
        app = ClipBotApp(
            allowed_chat_id=100,
            telegram=telegram,
            job_queue=queue,
        )

        app.handle_text_message(
            chat_id=100,
            text=(
                "first https://vod.sooplive.com/player/195880425 "
                "second https://vod.sooplive.co.kr/player/198263283"
            ),
        )

        self.assertEqual(
            queue.urls,
            [
                ("https://vod.sooplive.com/player/195880425", 100),
                ("https://vod.sooplive.com/player/198263283", 100),
            ],
        )
        self.assertEqual(
            telegram.messages,
            [
                (100, "Queued download: 195880425"),
                (100, "Queued download: 198263283"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
