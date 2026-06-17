import unittest
from pathlib import Path
import tempfile

from soop_clip_downloader.telegram_api import TelegramClient


class FakeTransport:
    def __init__(self):
        self.posts = []
        self.multipart_posts = []

    def post_json(self, url: str, data: dict) -> dict:
        self.posts.append((url, data))
        return {"ok": True, "result": []}

    def post_multipart_file(
        self,
        url: str,
        fields: dict,
        *,
        file_field: str,
        file_path: Path,
        mime_type: str,
    ) -> dict:
        self.multipart_posts.append(
            (url, fields, file_field, file_path, mime_type)
        )
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

    def test_send_message_supports_responder_protocol_positionals(self):
        transport = FakeTransport()
        client = TelegramClient(token="123:abc", transport=transport)

        client.send_message(100, "queued")

        self.assertEqual(transport.posts[0][1], {"chat_id": 100, "text": "queued"})

    def test_edit_message_text_posts_chat_and_message_id(self):
        transport = FakeTransport()
        client = TelegramClient(token="123:abc", transport=transport)

        client.edit_message_text(chat_id=100, message_id=55, text="progress")

        self.assertEqual(
            transport.posts,
            [
                (
                    "https://api.telegram.org/bot123:abc/editMessageText",
                    {"chat_id": 100, "message_id": 55, "text": "progress"},
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

    def test_send_video_path_uses_file_uri_for_local_bot_api(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            transport = FakeTransport()
            client = TelegramClient(token="123:abc", transport=transport)

            client.send_video_path(chat_id=100, file_path=file_path, caption="done")

            self.assertEqual(
                transport.posts,
                [
                    (
                        "https://api.telegram.org/bot123:abc/sendVideo",
                        {
                            "chat_id": 100,
                            "video": file_path.resolve().as_uri(),
                            "caption": "done",
                            "supports_streaming": "true",
                        },
                    )
                ],
            )

    def test_send_video_path_maps_download_dir_to_container_uri(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = root / "nested" / "clip one.mp4"
            file_path.parent.mkdir()
            file_path.write_bytes(b"video")
            transport = FakeTransport()
            client = TelegramClient(
                token="123:abc",
                transport=transport,
                local_file_root=root,
                local_file_uri_base="file:///telegram-files",
            )

            client.send_video_path(chat_id=100, file_path=file_path, caption="done")

            self.assertEqual(
                transport.posts[0][1]["video"],
                "file:///telegram-files/nested/clip%20one.mp4",
            )

    def test_send_video_path_rejects_files_outside_mapped_root(self):
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as other_dir:
            file_path = Path(other_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            transport = FakeTransport()
            client = TelegramClient(
                token="123:abc",
                transport=transport,
                local_file_root=Path(root_dir),
                local_file_uri_base="file:///telegram-files",
            )

            with self.assertRaises(ValueError):
                client.send_video_path(chat_id=100, file_path=file_path, caption="done")

            self.assertEqual(transport.posts, [])

    def test_send_video_file_uses_multipart_upload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "clip.mp4"
            file_path.write_bytes(b"video")
            transport = FakeTransport()
            client = TelegramClient(token="123:abc", transport=transport)

            client.send_video_file(chat_id=100, file_path=file_path, caption="done")

            self.assertEqual(
                transport.multipart_posts,
                [
                    (
                        "https://api.telegram.org/bot123:abc/sendVideo",
                        {
                            "chat_id": 100,
                            "caption": "done",
                            "supports_streaming": "true",
                        },
                        "video",
                        file_path,
                        "video/mp4",
                    )
                ],
            )


if __name__ == "__main__":
    unittest.main()
