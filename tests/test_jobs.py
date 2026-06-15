from pathlib import Path
import unittest

from soop_clip_downloader.jobs import InMemoryJobQueue, JobStatus


class JobQueueTests(unittest.TestCase):
    def test_enqueue_assigns_ids_and_pops_fifo(self):
        queue = InMemoryJobQueue()

        first = queue.enqueue("https://vod.sooplive.com/player/1", chat_id=100)
        second = queue.enqueue("https://vod.sooplive.com/player/2", chat_id=100)

        self.assertEqual(first.id, 1)
        self.assertEqual(second.id, 2)
        self.assertEqual(first.status, JobStatus.QUEUED)
        self.assertEqual(queue.pending_count, 2)
        self.assertEqual(queue.pop_next(), first)
        self.assertEqual(queue.pop_next(), second)
        self.assertIsNone(queue.pop_next())

    def test_status_transitions_are_recorded(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue("https://vod.sooplive.com/player/1", chat_id=100)

        queue.mark_started(job.id)
        self.assertEqual(queue.get(job.id).status, JobStatus.RUNNING)

        queue.mark_succeeded(job.id, Path("downloads/clip.mp4"))
        updated = queue.get(job.id)
        self.assertEqual(updated.status, JobStatus.SUCCEEDED)
        self.assertEqual(updated.file_path, Path("downloads/clip.mp4"))

    def test_failed_status_keeps_error_message(self):
        queue = InMemoryJobQueue()
        job = queue.enqueue("https://vod.sooplive.com/player/1", chat_id=100)

        queue.mark_failed(job.id, "yt-dlp failed")

        updated = queue.get(job.id)
        self.assertEqual(updated.status, JobStatus.FAILED)
        self.assertEqual(updated.error, "yt-dlp failed")


if __name__ == "__main__":
    unittest.main()
