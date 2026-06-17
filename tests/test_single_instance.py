import os
from pathlib import Path
import tempfile
import unittest

from soop_clip_downloader.single_instance import AlreadyRunningError, SingleInstanceLock


class SingleInstanceLockTests(unittest.TestCase):
    def test_lock_blocks_second_running_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / "service.lock"
            first = SingleInstanceLock(lock_path)
            first.acquire()
            try:
                self.assertEqual(lock_path.read_text(encoding="utf-8"), str(os.getpid()))
                with self.assertRaises(AlreadyRunningError):
                    SingleInstanceLock(lock_path).acquire()
            finally:
                first.release()

            self.assertFalse(lock_path.exists())

    def test_lock_replaces_stale_invalid_pid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_path = Path(temp_dir) / "service.lock"
            lock_path.write_text("999999999", encoding="utf-8")

            lock = SingleInstanceLock(lock_path)
            lock.acquire()
            try:
                self.assertEqual(lock_path.read_text(encoding="utf-8"), str(os.getpid()))
            finally:
                lock.release()


if __name__ == "__main__":
    unittest.main()
