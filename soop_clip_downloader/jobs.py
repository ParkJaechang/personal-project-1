"""In-memory download job queue."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


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

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def enqueue(self, url: str, chat_id: int) -> DownloadJob:
        job = DownloadJob(id=self._next_id, url=url, chat_id=chat_id)
        self._next_id += 1
        self._jobs[job.id] = job
        self._pending.append(job.id)
        return job

    def pop_next(self) -> DownloadJob | None:
        if not self._pending:
            return None
        return self._jobs[self._pending.popleft()]

    def get(self, job_id: int) -> DownloadJob:
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

    def _replace(self, job_id: int, **changes: object) -> DownloadJob:
        updated = replace(self._jobs[job_id], **changes)
        self._jobs[job_id] = updated
        return updated
