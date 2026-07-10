"""File scanning service for threat detection and metadata extraction."""
import aiofiles
from pathlib import Path
from typing import Any

from src.models import StoredFile


class FileScannerService:
    """Service for scanning files for threats and extracting metadata."""

    SUSPICIOUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js"}
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def scan_for_threats(self, file_item: StoredFile) -> tuple[str, str, bool]:
        """
        Scan a file for suspicious content.
        
        Returns:
            Tuple of (scan_status, scan_details, requires_attention)
        """
        reasons: list[str] = []
        extension = Path(file_item.original_name).suffix.lower()

        if extension in self.SUSPICIOUS_EXTENSIONS:
            reasons.append(f"suspicious extension {extension}")

        if file_item.size > self.MAX_FILE_SIZE_BYTES:
            reasons.append("file is larger than 10 MB")

        if extension == ".pdf" and file_item.mime_type not in {
            "application/pdf",
            "application/octet-stream",
        }:
            reasons.append("pdf extension does not match mime type")

        scan_status = "suspicious" if reasons else "clean"
        scan_details = ", ".join(reasons) if reasons else "no threats found"
        requires_attention = bool(reasons)

        return scan_status, scan_details, requires_attention

    async def extract_metadata(self, file_item: StoredFile, stored_path: Path) -> dict[str, Any]:
        """
        Extract metadata from a file using async I/O.
        
        Args:
            file_item: The file model with basic metadata
            stored_path: Path to the stored file on disk
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            "extension": Path(file_item.original_name).suffix.lower(),
            "size_bytes": file_item.size,
            "mime_type": file_item.mime_type,
        }

        if file_item.mime_type.startswith("text/"):
            async with aiofiles.open(stored_path, encoding="utf-8", errors="ignore") as f:
                content = await f.read()
                metadata["line_count"] = len(content.splitlines())
                metadata["char_count"] = len(content)
        elif file_item.mime_type == "application/pdf":
            async with aiofiles.open(stored_path, mode="rb") as f:
                content = await f.read()
                metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

        return metadata
