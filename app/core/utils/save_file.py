import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile

from core.config import settings

# Project root (face_reg_test/)
BASE_DIR = Path(__file__).resolve().parents[3]

UPLOAD_DIR = Path(settings.file_url.upload_dir)
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR / UPLOAD_DIR

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_file(file: UploadFile, subdir: str = "questions") -> str | None:
    if not file:
        return None

    target_dir = UPLOAD_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix
    file_name = f"{uuid.uuid4()}{ext}"
    file_path = target_dir / file_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return f"{settings.file_url.http}/uploads/{subdir}/{file_name}"
