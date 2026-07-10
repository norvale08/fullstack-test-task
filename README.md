## Тестовое задание на позицию Fullstack разработчика (Python + React)

**Вводные:**
1. Здесь представлен MVP проект файлообменника. Он позволяет загружать файлы, проверяет их на подозрительный контент и отправляет алерты;
2. Репозиторий содержит в себе бэкенд и фронтенд части;
3. В обоих частях присутствуют баги, неоптимизированный код, неудачные архитектурные решения.

**Задачи:**
1. Проведите рефакторинг бэкенда, не ломая бизнес-логики: предложите свое видение архитектуры и реализуйте его;
2. (Дополнительно) На бэкенде есть возможность неочевидной оптимизации - выполните ее;
3. (Дополнительно) Разбейте логику фронтенда на слои;

**Запуск:**
1. ```docker compose -f docker-compose.dev.yml up```
2. ```docker exec -it backend alembic upgrade head```

**Открыть фронт:** ```http://localhost:3000/test```
**Открыть бэк:** ```http://localhost:8000/docs```

---

# Refactoring Summary

## Backend Refactoring

### Architecture Improvements

#### 1. Configuration Management (`backend/src/config.py`)
- **Before**: Configuration scattered across `service.py` and `tasks.py` with hardcoded environment variable access
- **After**: Centralized configuration using Pydantic Settings
  - Single source of truth for all configuration
  - Type-safe configuration with validation
  - Environment-based configuration loading
  - Computed properties for derived values (e.g., `database_url`)

#### 2. Database Layer (`backend/src/database.py`)
- **Before**: Duplicate database connection setup in `service.py` and `tasks.py`, no connection pooling configuration
- **After**: Shared database module with optimized connection pooling
  - Single engine instance across the application
  - Connection pooling with `pool_size=10`, `max_overflow=20`
  - `pool_pre_ping=True` for connection health checks
  - `pool_recycle=3600` to prevent stale connections
  - Dependency injection support via `get_session()`

#### 3. Repository Pattern (`backend/src/repositories.py`)
- **Before**: Direct SQLAlchemy queries mixed with business logic in service layer
- **After**: Dedicated repository classes for data access
  - `FileRepository`: Encapsulates all file-related database operations
  - `AlertRepository`: Encapsulates all alert-related database operations
  - Clear separation between data access and business logic
  - Easier to test and maintain

#### 4. Service Layer Refactoring (`backend/src/service.py`)
- **Before**: Mixed concerns (configuration, data access, business logic, file operations)
- **After**: Pure business logic layer
  - Uses shared configuration from `config.py`
  - Uses shared database session from `database.py`
  - Uses repositories for data access
  - Focuses solely on business operations

#### 5. File Storage Service (`backend/src/services/file_storage.py`)
- **Before**: File operations scattered across `service.py` and `tasks.py`
- **After**: Dedicated file storage service with async I/O
  - `FileStorageService`: Encapsulates all file system operations
  - Methods for filename generation, saving, deleting, and checking file existence
  - Reusable across service layer and tasks
  - Uses `aiofiles` for non-blocking async file operations
  - Easier to test with mock storage

#### 6. File Scanner Service (`backend/src/services/file_scanner.py`)
- **Before**: Threat detection and metadata extraction logic embedded in `tasks.py`
- **After**: Dedicated file scanner service with async I/O
  - `FileScannerService`: Encapsulates threat detection and metadata extraction
  - `scan_for_threats()`: Centralized threat detection logic
  - `extract_metadata()`: Centralized metadata extraction logic using async file reads
  - Configurable thresholds (e.g., `MAX_FILE_SIZE_BYTES`, `SUSPICIOUS_EXTENSIONS`)
  - Easier to test and extend with new detection rules

#### 7. Tasks Refactoring (`backend/src/tasks.py`)
- **Before**: Duplicate database setup, direct session manipulation, embedded business logic
- **After**: Uses shared infrastructure and services
  - Imports from `config.py` and `database.py`
  - Uses repository pattern for data access
  - Uses `FileStorageService` for file operations
  - Uses `FileScannerService` for threat detection and metadata extraction
  - Consistent with main application architecture

#### 8. Logging (`backend/src/logger.py`)
- **Before**: No logging
- **After**: Structured logging
  - Centralized logger configuration
  - Consistent log format
  - Added to key endpoints in `app.py`

#### 9. API Layer Cleanup (`backend/src/app.py`)
- **Before**: Direct file path manipulation in download endpoint
- **After**: Uses service layer for file operations
  - `download_file` now uses `get_file_path()` from service layer
  - Consistent error handling via service layer
  - Cleaner separation of concerns

### Optimizations Implemented

**1. Database Connection Pooling**: Implemented proper connection pooling with tuned parameters. This eliminates the overhead of creating new connections for each request and improves performance under load.

**2. Async File I/O**: Converted all blocking file operations to async using `aiofiles`:
- File reads in `FileScannerService.extract_metadata()` are now non-blocking
- File writes in `FileStorageService.save_file()` are now non-blocking
- File operations no longer block the event loop, enabling true concurrent processing

## Frontend Refactoring

### Layer Separation

#### 1. API Client Layer (`frontend/src/lib/api.ts`)
- **Before**: Direct `fetch` calls throughout the component, hardcoded API URL
- **After**: Centralized API client with configurable base URL
  - Single source of truth for API endpoints
  - Type-safe API methods
  - Consistent error handling
  - Reusable across the application
  - Configurable via `NEXT_PUBLIC_API_BASE_URL` environment variable

#### 2. Custom Hooks Layer (`frontend/src/hooks/`)
- **Before**: All state and logic in the main component
- **After**: Extracted custom hooks
  - `useFilesAndAlerts`: Manages data fetching and state for files and alerts
  - `useFileUpload`: Manages file upload logic and state
  - Reusable and testable logic separation

#### 3. Component Layer (`frontend/src/components/`)
- **Before**: 368-line monolithic component
- **After**: Modular components
  - `FileTable`: Displays file list with loading states, uses `apiClient.getDownloadUrl()`
  - `AlertTable`: Displays alert list with loading states
  - `UploadModal`: Handles file upload form
  - Each component is focused and reusable

#### 4. Utility Functions (`frontend/src/lib/utils.ts`)
- **Before**: Helper functions in the main component
- **After**: Extracted utility module
  - `formatDate`, `formatSize`, `getLevelVariant`, `getProcessingVariant`
  - Reusable across components
  - Easier to test

#### 5. Main Page Refactoring (`frontend/src/app/page.tsx`)
- **Before**: 368 lines with mixed concerns
- **After**: ~100 lines orchestrating components
  - Uses custom hooks for state management
  - Uses extracted components for UI
  - Clean separation of concerns
  - Much easier to understand and maintain

## Benefits

### Backend
- **Maintainability**: Clear separation of concerns makes the code easier to understand and modify
- **Testability**: Each layer can be tested independently; services can be mocked easily
- **Scalability**: Connection pooling and proper architecture support growth
- **Consistency**: Shared configuration and database setup across all modules
- **Performance**: Optimized connection pooling reduces database overhead; async file I/O eliminates blocking operations
- **Extensibility**: New threat detection rules or metadata extraction logic can be added to `FileScannerService` without touching other layers

### Frontend
- **Maintainability**: Smaller, focused components are easier to work with
- **Reusability**: Hooks and components can be reused across the application
- **Testability**: Isolated logic in hooks and utilities is easier to test
- **Type Safety**: Centralized types in API client ensure consistency
- **Developer Experience**: Clear structure makes onboarding easier
- **Configurability**: API base URL can be configured for different environments

## Environment Variables

To configure the frontend API URL, set `NEXT_PUBLIC_API_BASE_URL` in the frontend environment:

```bash
# Example for docker-compose.dev.yml
environment:
  - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> **Note on BuildKit issues:** On some Docker Desktop setups, BuildKit may produce cache snapshot errors. If you encounter `failed to commit ... snapshot ... does not exist`, run with `DOCKER_BUILDKIT=0`:
> ```powershell
> $env:DOCKER_BUILDKIT = "0"; docker compose -f docker-compose.dev.yml up --build -d
> ```

## Verification Results

### Backend Tests (performed inside container)
- **Database migrations** completed successfully
- **File upload** returns 201 and stores file metadata
- **Celery worker** processed the file asynchronously:
  - `scan_file_for_threats` completed
  - `extract_file_metadata` completed
  - `send_file_alert` completed
- **File listing** returns updated file with `processing_status: "processed"`, `scan_status: "clean"`, and `metadata_json` populated
- **Alerts listing** returns the generated alert

### Frontend Tests
- **Build** completed successfully (production Next.js build)
- **Container** starts without errors on port 3000
- **Page serving** at `/test` returns 200 with rendered HTML

## Dependencies Added

### Backend
- `pydantic-settings>=2.0.0` - For configuration management
- `aiofiles>=24.1.0` - For async file operations

No new frontend dependencies were required.
