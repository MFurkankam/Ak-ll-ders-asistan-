import os
import tempfile
from pathlib import Path
import pytest

TEST_DB_PATH = Path(tempfile.gettempdir()) / f"akilli_ders_test_{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from utils.db import init_db

@pytest.fixture(scope='session', autouse=True)
def reset_db():
    # Ensure a clean DB for the test session
    try:
        TEST_DB_PATH.unlink()
    except FileNotFoundError:
        pass
    init_db()
    yield
    # optionally clean up after tests
    try:
        TEST_DB_PATH.unlink()
    except Exception:
        pass
