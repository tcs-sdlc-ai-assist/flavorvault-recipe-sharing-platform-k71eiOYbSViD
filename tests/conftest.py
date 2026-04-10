import asyncio
import logging
from typing import AsyncGenerator, Optional

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base
from models.associations import recipe_tags, favorites
from models.user import User
from models.recipe import Recipe
from models.ingredient import Ingredient
from models.step import Step
from models.review import Review
from models.tag import Tag
from utils.security import create_access_token, hash_password

logger = logging.getLogger(__name__)

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    from main import app
    from utils.dependencies import get_db

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    import uuid
    from datetime import datetime, timezone

    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="testuser@example.com",
        display_name="Test User",
        password_hash=hash_password("TestPass123!"),
        role="user",
        bio="A test user for unit tests",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    import uuid
    from datetime import datetime, timezone

    user = User(
        id=str(uuid.uuid4()),
        username="adminuser",
        email="adminuser@example.com",
        display_name="Admin User",
        password_hash=hash_password("AdminPass123!"),
        role="admin",
        bio="An admin user for unit tests",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_client(client: httpx.AsyncClient, test_user: User) -> httpx.AsyncClient:
    token = create_access_token(data={"sub": test_user.id})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


@pytest_asyncio.fixture
async def admin_client(client: httpx.AsyncClient, admin_user: User) -> httpx.AsyncClient:
    token = create_access_token(data={"sub": admin_user.id})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


@pytest_asyncio.fixture
async def sample_tag(db_session: AsyncSession) -> Tag:
    import uuid
    from datetime import datetime, timezone

    tag = Tag(
        id=str(uuid.uuid4()),
        name="vegetarian",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(tag)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(tag)
    return tag


@pytest_asyncio.fixture
async def sample_recipe(db_session: AsyncSession, test_user: User) -> Recipe:
    import uuid
    from datetime import datetime, timezone

    recipe_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    recipe = Recipe(
        id=recipe_id,
        title="Test Recipe",
        description="A delicious test recipe for unit testing",
        prep_time_minutes=15,
        cook_time_minutes=30,
        servings=4,
        difficulty="easy",
        author_id=test_user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(recipe)

    ingredient = Ingredient(
        id=str(uuid.uuid4()),
        recipe_id=recipe_id,
        name="Test Ingredient",
        quantity="2",
        unit="cups",
        sort_order=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(ingredient)

    step = Step(
        id=str(uuid.uuid4()),
        recipe_id=recipe_id,
        step_number=1,
        instruction="Mix all ingredients together",
        created_at=now,
        updated_at=now,
    )
    db_session.add(step)

    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(recipe)
    return recipe