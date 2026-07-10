from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Alert, StoredFile


class FileRepository:
    """Repository for StoredFile data access operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[StoredFile]:
        """Get all files ordered by creation date descending."""
        result = await self.session.execute(
            select(StoredFile).order_by(StoredFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, file_id: str) -> StoredFile | None:
        """Get a file by ID."""
        return await self.session.get(StoredFile, file_id)

    async def create(self, file_item: StoredFile) -> StoredFile:
        """Create a new file record."""
        self.session.add(file_item)
        await self.session.commit()
        await self.session.refresh(file_item)
        return file_item

    async def update(self, file_item: StoredFile) -> StoredFile:
        """Update an existing file record."""
        await self.session.commit()
        await self.session.refresh(file_item)
        return file_item

    async def delete(self, file_item: StoredFile) -> None:
        """Delete a file record."""
        await self.session.delete(file_item)
        await self.session.commit()


class AlertRepository:
    """Repository for Alert data access operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Alert]:
        """Get all alerts ordered by creation date descending."""
        result = await self.session.execute(
            select(Alert).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, alert: Alert) -> Alert:
        """Create a new alert record."""
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
