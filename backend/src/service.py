import mimetypes
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from src.config import settings
from src.database import async_session_maker
from src.models import Alert, StoredFile
from src.repositories import AlertRepository, FileRepository
from src.services.file_scanner import FileScannerService
from src.services.file_storage import FileStorageService

# Initialize services
storage_service = FileStorageService()
scanner_service = FileScannerService()


async def list_files() -> list[StoredFile]:
    async with async_session_maker() as session:
        repo = FileRepository(session)
        return await repo.get_all()


async def list_alerts() -> list[Alert]:
    async with async_session_maker() as session:
        repo = AlertRepository(session)
        return await repo.get_all()


async def get_file(file_id: str) -> StoredFile:
    async with async_session_maker() as session:
        repo = FileRepository(session)
        file_item = await repo.get_by_id(file_id)
        if not file_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return file_item


async def create_file(title: str, upload_file: UploadFile) -> StoredFile:
    content = await upload_file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    stored_name = storage_service.generate_filename(upload_file.filename or "")
    await storage_service.save_file(content, stored_name)

    mime_type = (
        upload_file.content_type
        or mimetypes.guess_type(stored_name)[0]
        or "application/octet-stream"
    )

    file_item = StoredFile(
        id=Path(stored_name).stem,
        title=title,
        original_name=upload_file.filename or stored_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size=len(content),
        processing_status="uploaded",
    )
    async with async_session_maker() as session:
        repo = FileRepository(session)
        return await repo.create(file_item)


async def update_file(file_id: str, title: str) -> StoredFile:
    async with async_session_maker() as session:
        repo = FileRepository(session)
        file_item = await repo.get_by_id(file_id)
        if not file_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        file_item.title = title
        return await repo.update(file_item)


async def delete_file(file_id: str) -> None:
    async with async_session_maker() as session:
        repo = FileRepository(session)
        file_item = await repo.get_by_id(file_id)
        if not file_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        await storage_service.delete_file(file_item.stored_name)
        await repo.delete(file_item)


async def get_file_path(file_id: str) -> tuple[StoredFile, Path]:
    file_item = await get_file(file_id)
    stored_path = storage_service.get_file_path(file_item.stored_name)
    if not storage_service.file_exists(file_item.stored_name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")
    return file_item, stored_path


async def create_alert(file_id: str, level: str, message: str) -> Alert:
    alert = Alert(file_id=file_id, level=level, message=message)
    async with async_session_maker() as session:
        repo = AlertRepository(session)
        return await repo.create(alert)
