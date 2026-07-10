"""File storage service for managing file operations on disk."""
import aiofiles
from pathlib import Path
from uuid import uuid4

from src.config import settings


class FileStorageService:
    """Service for managing file storage operations."""

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or settings.storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, original_filename: str) -> str:
        """Generate a unique stored filename based on original filename."""
        file_id = str(uuid4())
        suffix = Path(original_filename or "").suffix
        return f"{file_id}{suffix}"

    async def save_file(self, content: bytes, stored_name: str) -> Path:
        """Save file content to storage directory using async I/O."""
        stored_path = self.storage_dir / stored_name
        async with aiofiles.open(stored_path, mode="wb") as f:
            await f.write(content)
        return stored_path

    async def delete_file(self, stored_name: str) -> None:
        """Delete file from storage directory using async I/O."""
        stored_path = self.storage_dir / stored_name
        if stored_path.exists():
            stored_path.unlink()

    def get_file_path(self, stored_name: str) -> Path:
        """Get the full path to a stored file."""
        return self.storage_dir / stored_name

    def file_exists(self, stored_name: str) -> bool:
        """Check if a file exists in storage."""
        return (self.storage_dir / stored_name).exists()
