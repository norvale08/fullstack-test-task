import asyncio
from pathlib import Path
from celery import Celery

from src.config import settings
from src.database import async_session_maker
from src.models import Alert, StoredFile
from src.repositories import AlertRepository, FileRepository
from src.services.file_scanner import FileScannerService
from src.services.file_storage import FileStorageService

REDIS_URL = settings.redis_url
_worker_loop: asyncio.AbstractEventLoop | None = None

# Initialize services
storage_service = FileStorageService()
scanner_service = FileScannerService()


def run_in_worker_loop(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


celery_app = Celery("file_tasks", broker=REDIS_URL, backend=REDIS_URL)


async def _scan_file_for_threats(file_id: str) -> None:
    async with async_session_maker() as session:
        repo = FileRepository(session)
        file_item = await repo.get_by_id(file_id)
        if not file_item:
            return

        file_item.processing_status = "processing"
        scan_status, scan_details, requires_attention = scanner_service.scan_for_threats(file_item)
        file_item.scan_status = scan_status
        file_item.scan_details = scan_details
        file_item.requires_attention = requires_attention
        await repo.update(file_item)

    extract_file_metadata.delay(file_id)


async def _extract_file_metadata(file_id: str) -> None:
    async with async_session_maker() as session:
        repo = FileRepository(session)
        file_item = await repo.get_by_id(file_id)
        if not file_item:
            return

        stored_path = storage_service.get_file_path(file_item.stored_name)
        if not storage_service.file_exists(file_item.stored_name):
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            file_item.scan_details = "stored file not found during metadata extraction"
            await repo.update(file_item)
            send_file_alert.delay(file_id)
            return

        metadata = await scanner_service.extract_metadata(file_item, stored_path)
        file_item.metadata_json = metadata
        file_item.processing_status = "processed"
        await repo.update(file_item)

    send_file_alert.delay(file_id)


async def _send_file_alert(file_id: str) -> None:
    async with async_session_maker() as session:
        file_repo = FileRepository(session)
        alert_repo = AlertRepository(session)
        file_item = await file_repo.get_by_id(file_id)
        if not file_item:
            return

        if file_item.processing_status == "failed":
            alert = Alert(file_id=file_id, level="critical", message="File processing failed")
        elif file_item.requires_attention:
            alert = Alert(
                file_id=file_id,
                level="warning",
                message=f"File requires attention: {file_item.scan_details}",
            )
        else:
            alert = Alert(file_id=file_id, level="info", message="File processed successfully")

        await alert_repo.create(alert)


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    run_in_worker_loop(_scan_file_for_threats(file_id))


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    run_in_worker_loop(_extract_file_metadata(file_id))


@celery_app.task
def send_file_alert(file_id: str) -> None:
    run_in_worker_loop(_send_file_alert(file_id))
