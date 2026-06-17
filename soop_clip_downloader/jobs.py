"""In-memory download job queue."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from threading import RLock


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DownloadJob:
    id: int
    url: str
    chat_id: int
    status: JobStatus = JobStatus.QUEUED
    file_path: Path | None = None
    error: str | None = None


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._next_id = 1
        self._pending: deque[int] = deque()
        self._jobs: dict[int, DownloadJob] = {}
        self._lock = RLock()

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def enqueue(self, url: str, chat_id: int) -> DownloadJob:
        with self._lock:
            job = DownloadJob(id=self._next_id, url=url, chat_id=chat_id)
            self._next_id += 1
            self._jobs[job.id] = job
            self._pending.append(job.id)
            return job

    def pop_next(self) -> DownloadJob | None:
        with self._lock:
            if not self._pending:
                return None
            return self._jobs[self._pending.popleft()]

    def get(self, job_id: int) -> DownloadJob:
        with self._lock:
            return self._jobs[job_id]

    def mark_started(self, job_id: int) -> DownloadJob:
        return self._replace(job_id, status=JobStatus.RUNNING, error=None)

    def mark_succeeded(self, job_id: int, file_path: Path) -> DownloadJob:
        return self._replace(
            job_id,
            status=JobStatus.SUCCEEDED,
            file_path=file_path,
            error=None,
        )

    def mark_failed(self, job_id: int, error: str) -> DownloadJob:
        return self._replace(job_id, status=JobStatus.FAILED, error=error)

    def mark_cancelled(self, job_id: int, error: str) -> DownloadJob:
        return self._replace(job_id, status=JobStatus.CANCELLED, error=error)

    def cancel_pending(self, reason: str) -> int:
        with self._lock:
            cancelled = 0
            while self._pending:
                job_id = self._pending.popleft()
                self._replace(job_id, status=JobStatus.CANCELLED, error=reason)
                cancelled += 1
            return cancelled

    def _replace(self, job_id: int, **changes: object) -> DownloadJob:
        with self._lock:
            updated = replace(self._jobs[job_id], **changes)
            self._jobs[job_id] = updated
            return updated
