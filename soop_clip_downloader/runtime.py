"""Runtime composition for the SOOP Telegram clip downloader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from soop_clip_downloader.app import ClipBotApp
from soop_clip_downloader.config import Settings, load_settings
from soop_clip_downloader.delivery import CompletedFileDeliverer
from soop_clip_downloader.downloader import YtdlpDownloader
from soop_clip_downloader.jobs import InMemoryJobQueue
from soop_clip_downloader.service import DownloadWorker, FileOffsetStore, PollingService
from soop_clip_downloader.single_instance import AlreadyRunningError, SingleInstanceLock
from soop_clip_downloader.telegram_api import TelegramClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Runtime:
    settings: Settings
    telegram: object
    queue: InMemoryJobQueue
    app: ClipBotApp
    downloader: object
    worker: DownloadWorker
    service: PollingService


def local_state_path(filename: str) -> Path:
    return PROJECT_ROOT / ".local" / filename


def build_runtime(
    settings: Settings,
    *,
    telegram: object | None = None,
    queue: InMemoryJobQueue | None = None,
    downloader: object | None = None,
) -> Runtime:
    telegram = telegram or TelegramClient(
        token=settings.telegram_bot_token,
        api_base_url=settings.telegram_api_base_url,
        local_file_root=settings.download_dir,
        local_file_uri_base=settings.telegram_local_file_uri_base,
    )
    queue = queue or InMemoryJobQueue()
    downloader = downloader or YtdlpDownloader(
        download_dir=settings.download_dir,
        ytdlp_path=settings.ytdlp_path,
        ffmpeg_path=settings.ffmpeg_path,
    )
    deliverer = CompletedFileDeliverer(
        telegram=telegram,
        max_default_upload_mb=settings.max_telegram_upload_mb,
        local_bot_api_base_url=settings.telegram_api_base_url,
    )
    worker = DownloadWorker(
        queue=queue,
        downloader=downloader,
        telegram=telegram,
        deliverer=deliverer,
        run_in_background=True,
    )
    app = ClipBotApp(
        allowed_chat_id=settings.telegram_allowed_chat_id,
        telegram=telegram,
        job_queue=queue,
        download_controller=worker,
    )
    service = PollingService(
        telegram=telegram,
        app=app,
        worker=worker,
        offset_store=FileOffsetStore(local_state_path("telegram-offset.txt")),
    )
    return Runtime(
        settings=settings,
        telegram=telegram,
        queue=queue,
        app=app,
        downloader=downloader,
        worker=worker,
        service=service,
    )


def run(settings: Settings | None = None) -> None:
    with SingleInstanceLock(local_state_path("soop-service.lock")):
        runtime = build_runtime(settings or load_settings())
        runtime.service.run_forever()


def main() -> None:
    try:
        run()
    except AlreadyRunningError as exc:
        print(exc)
