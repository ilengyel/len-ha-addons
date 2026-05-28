from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi.templating import Jinja2Templates
from sqlalchemy.engine import make_url

from app.db import build_database_url


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def build_debug_upload_dir(database_url: Optional[str] = None) -> Path:
    url = make_url(build_database_url(database_url))
    if url.drivername.startswith("sqlite") and url.database:
        upload_dir = Path(url.database).resolve().parent / "debug_uploads"
    else:
        upload_dir = Path("data").resolve() / "debug_uploads"

    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir
