import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_db: str
    pgport: str = "5432"

    # Redis
    redis_url: str = "redis://backend-redis:6379/0"

    # Storage
    base_dir: Path = Path(__file__).resolve().parent.parent
    storage_dir: Path = base_dir / "storage" / "files"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.pgport}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env.dev"
        extra = "ignore"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
