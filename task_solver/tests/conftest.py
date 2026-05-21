import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ADDON_ROOT = Path(__file__).resolve().parents[1]
if str(ADDON_ROOT) not in sys.path:
    sys.path.insert(0, str(ADDON_ROOT))

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    database_url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    app = create_app(database_url=database_url, seed_defaults=False)
    with TestClient(app) as test_client:
        yield test_client
