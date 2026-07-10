from fastapi import FastAPI, HTTPException
from fastapi import File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette import status
from src.logger import logger
from src.schemas import AlertItem, FileItem, FileUpdate
from src.service import create_file, delete_file, get_file, get_file_path, list_alerts, list_files, update_file
from src.tasks import scan_file_for_threats

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/files", response_model=list[FileItem])
async def list_files_view():
    logger.info("Listing all files")
    return await list_files()


@app.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view():
    logger.info("Listing all alerts")
    return await list_alerts()


@app.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
):
    logger.info(f"Creating file with title: {title}")
    file_item = await create_file(title=title, upload_file=file)
    scan_file_for_threats.delay(file_item.id)
    logger.info(f"File created with ID: {file_item.id}")
    return file_item


@app.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str):
    return await get_file(file_id)


@app.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
):
    return await update_file(file_id=file_id, title=payload.title)


@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    file_item, stored_path = await get_file_path(file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@app.delete("/files/{file_id}", status_code=204)
async def delete_file_view(file_id: str):
    logger.info(f"Deleting file with ID: {file_id}")
    await delete_file(file_id)
    logger.info(f"File deleted: {file_id}")
