from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, File, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.web import templates

router = APIRouter()

ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
ALLOWED_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}


def sanitize_stem(filename: str) -> str:
    stem = Path(filename).stem.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return cleaned or "image"


def build_upload_name(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".jpeg":
        suffix = ".jpg"
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        suffix = ALLOWED_CONTENT_TYPES[content_type]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{sanitize_stem(filename)}{suffix}"


def list_uploaded_images(request: Request) -> List[Dict[str, str]]:
    upload_dir = Path(request.app.state.debug_upload_dir)
    images = []
    for path in sorted(upload_dir.iterdir(), key=lambda candidate: candidate.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        images.append(
            {
                "name": path.name,
                "url": str(request.url_for("debug-media", path=path.name)),
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size": f"{path.stat().st_size:,} bytes",
            }
        )
    return images


def render_debug_uploads(
    request: Request,
    *,
    error: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    message = None
    if request.query_params.get("uploaded") == "1":
        message = "Image uploaded."

    return templates.TemplateResponse(
        request,
        "debug_uploads.html",
        {
            "message": message,
            "error": error,
            "images": list_uploaded_images(request),
        },
        status_code=status_code,
    )


@router.get("/debug/uploads", response_class=HTMLResponse)
def debug_uploads(request: Request) -> HTMLResponse:
    return render_debug_uploads(request)


@router.post("/debug/uploads", response_class=HTMLResponse)
async def upload_debug_image(
    request: Request,
    image: UploadFile = File(...),
) -> Response:
    filename = image.filename or ""
    content_type = (image.content_type or "").lower()

    if not filename.strip():
        await image.close()
        return render_debug_uploads(
            request,
            error="Choose an image file before uploading.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    suffix = Path(filename).suffix.lower()
    normalized_suffix = ".jpg" if suffix == ".jpeg" else suffix
    if normalized_suffix not in ALLOWED_IMAGE_SUFFIXES or content_type not in ALLOWED_CONTENT_TYPES:
        await image.close()
        return render_debug_uploads(
            request,
            error="Only PNG, JPG, GIF, WEBP, and BMP images are supported.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    upload_path = Path(request.app.state.debug_upload_dir) / build_upload_name(filename, content_type)
    with upload_path.open("wb") as uploaded_file:
        shutil.copyfileobj(image.file, uploaded_file)
    await image.close()

    if upload_path.stat().st_size == 0:
        upload_path.unlink(missing_ok=True)
        return render_debug_uploads(
            request,
            error="The uploaded image was empty.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/debug/uploads?uploaded=1", status_code=status.HTTP_303_SEE_OTHER)
