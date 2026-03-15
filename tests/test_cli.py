import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pyvault.models import Base

@pytest.fixture(scope='module')
def test_db():
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_add_password(test_db):
    from pyvault.cli import add
    # Mock click prompts, but for simplicity, assume direct call
    # Actually, better to test functions separately
    pass  # Placeholder