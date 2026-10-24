"""Pytest fixtures for backend test suite."""
import os
import tempfile
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.seed_data import seed_database


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a temporary SQLite database file for isolated test execution."""
    fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite+aiosqlite:///{temp_db_path.replace(os.sep, '/')}"

    test_engine = create_async_engine(
        db_url,
        connect_args={"check_same_thread": False}
    )
    test_session_local = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_local() as session:
        # Seed test data
        await seed_database(session, run_initial_audit=False)

    async with test_session_local() as session:
        yield session

    await test_engine.dispose()
    try:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    """Test HTTP client with overridden database dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
