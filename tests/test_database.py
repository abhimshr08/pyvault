import os
import pytest

# Configure database to run in-memory for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from pyvault.database import init_db, engine
from sqlalchemy import inspect

def test_init_db():
    init_db()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "passwords" in tables
    assert "users" in tables