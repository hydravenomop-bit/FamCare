"""
Test configuration and fixtures.

Sets up an isolated test database (in-memory SQLite) with fresh seed data
for each test. Uses httpx.AsyncClient for async endpoint testing.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import Service, Caregiver, Patient, CaregiverService, Booking, BookingItem
from app.seed import (
    SVC_PHYSIOTHERAPY, SVC_WOUND_DRESSING, SVC_IV_THERAPY, SVC_GENERAL_CHECKUP,
    CG_ALICE, CG_BOB, CG_CAROL, CG_DAVID, CG_EVE,
    PT_JOHN, PT_JANE, PT_MIKE,
    seed_database,
)


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionFactory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



@pytest_asyncio.fixture
async def db_session():
    """
    Provides a clean database session for each test.

    Creates all tables, seeds data, yields the session,
    then drops all tables for isolation.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionFactory() as session:
        await seed_database(session)
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    Provides an async HTTP client wired to the test database.

    Overrides the get_db dependency so all API calls use the test DB.
    """
    async def override_get_db():
        async with TestSessionFactory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


PHYSIO_ID = SVC_PHYSIOTHERAPY
WOUND_ID = SVC_WOUND_DRESSING
IV_ID = SVC_IV_THERAPY
CHECKUP_ID = SVC_GENERAL_CHECKUP

ALICE_ID = CG_ALICE
BOB_ID = CG_BOB
CAROL_ID = CG_CAROL
DAVID_ID = CG_DAVID
EVE_ID = CG_EVE

JOHN_ID = PT_JOHN
JANE_ID = PT_JANE
MIKE_ID = PT_MIKE
