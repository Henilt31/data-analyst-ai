import pytest
import anyio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
import app.db.session as session_module
from app.main import app

@pytest.fixture(autouse=True)
def setup_test_sqlite_db(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    anyio.run(_init)

    session_factory = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(session_module, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(session_module, "engine", engine)

    yield session_factory

    app.dependency_overrides.pop(get_db, None)

    async def _dispose():
        await engine.dispose()

    anyio.run(_dispose)
