"""Runtime composition for the SOOP Telegram clip downloader."""

from __future__ import annotations

from dataclasses import dataclass

from soop_clip_downloader.app import ClipBotApp
from soop_clip_downloader.config import Settings, load_settings
from soop_clip_downloader.delivery import CompletedFileDeliverer
from soop_clip_downloader.downloader import YtdlpDownloader
from soop_clip_downloader.jobs import InMemoryJobQueue
from soop_clip_downloader.service import DownloadWorker, PollingService
from soop_clip_downloader.telegram_api import TelegramClient


@dataclass(frozen=True)
class Runtime:
    settings: Settings
    telegram: object
    queue: InMemoryJobQueue
    app: ClipBotApp
    downloader: object
    worker: DownloadWorker
    service: PollingService


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
    )
    queue = queue or InMemoryJobQueue()
    app = ClipBotApp(
        allowed_chat_id=settings.telegram_allowed_chat_id,
        telegram=telegram,
        job_queue=queue,
    )
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
    )
    service = PollingService(
        telegram=telegram,
        app=app,
        worker=worker,
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
    runtime = build_runtime(settings or load_settings())
    runtime.service.run_forever()


def main() -> None:
    run()
