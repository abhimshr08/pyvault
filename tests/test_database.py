import pytest
from pyvault.database import init_db, get_db

def test_init_db():
    # Test database initialization
    init_db()
    # Check if tables are created
    pass