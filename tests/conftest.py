import os
import pytest
from utils.db import init_db

@pytest.fixture(scope='session', autouse=True)
def reset_db():
    # Ensure a clean DB for the test session
    dbfile = os.path.join(os.getcwd(), 'app.db')
    try:
        os.remove(dbfile)
    except Exception:
        pass
    init_db()
    yield
    # optionally clean up after tests
    try:
        os.remove(dbfile)
    except Exception:
        pass
