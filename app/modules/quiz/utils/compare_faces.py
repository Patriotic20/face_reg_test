import os
import tempfile
from deepface import DeepFace
from fastapi import UploadFile
from urllib.parse import urlparse

from app.core.config import settings


async def compare_faces(img1: str, img2_file: UploadFile) -> bool:
    # Convert URL to local path
    if img1.startswith(("http://", "https://")):
        parsed = urlparse(img1)
        img1_path = os.path.join(
            settings.file_url.upload_dir,   # e.g. /app/uploads
            parsed.path.replace("/uploads/", "").lstrip("/")
        )
    else:
        img1_path = img1

    if not os.path.exists(img1_path):
        raise FileNotFoundError(f"Image not found: {img1_path}")

    # Save uploaded image to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await img2_file.read())
        tmp_path = tmp.name

    result = DeepFace.verify(
        img1_path=img1_path,
        img2_path=tmp_path,
        model_name="Facenet512",
        detector_backend="opencv",
        align=False,
    )

    return result["verified"]
