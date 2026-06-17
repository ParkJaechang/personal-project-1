"""Single-instance guard for the local service process."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path


class AlreadyRunningError(RuntimeError):
    """Raised when another service instance already owns the lock."""


class SingleInstanceLock:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._acquired = False

    def acquire(self) -> "SingleInstanceLock":
        self._path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if _pid_is_running(_read_pid(self._path)):
                    raise AlreadyRunningError(f"service already running: {self._path}")
                self._remove_stale_lock()
                continue

            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
            self._acquired = True
            return self

    def release(self) -> None:
        if not self._acquired:
            return
        try:
            if _read_pid(self._path) == os.getpid():
                self._path.unlink()
        except OSError:
            pass
        self._acquired = False

    def __enter__(self) -> "SingleInstanceLock":
        return self.acquire()

    def __exit__(self, *_exc_info) -> None:
        self.release()

    def _remove_stale_lock(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            return


def _read_pid(path: Path) -> int | None:
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _pid_is_running(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_is_running(pid)

    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _windows_pid_is_running(pid: int) -> bool:
    kernel32 = ctypes.windll.kernel32
    process_query_limited_information = 0x1000
    still_active = 259

    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False

    try:
        exit_code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return True
        return exit_code.value == still_active
    finally:
        kernel32.CloseHandle(handle)
