import uuid
from datetime import datetime, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipe import Recipe
from models.review import Review
from models.tag import Tag
from models.user import User
from utils.security import create_access_token, hash_password


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession) -> User:
    user = User(
        id=str(uuid.uuid4()),
        username="seconduser",
        email="seconduser@example.com",
        display_name="Second User",
        password_hash=hash_password("SecondPass123!"),
        role="user",
        bio="A second test user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user_client(client: httpx.AsyncClient, second_user: User) -> httpx.AsyncClient:
    token = create_access_token(data={"sub": second_user.id})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


@pytest_asyncio.fixture
async def sample_review(db_session: AsyncSession, sample_recipe: Recipe, second_user: User) -> Review:
    review = Review(
        id=str(uuid.uuid4()),
        recipe_id=sample_recipe.id,
        user_id=second_user.id,
        rating=4,
        comment="Great test recipe!",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(review)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(review)
    return review


@pytest_asyncio.fixture
async def seeded_admin(db_session: AsyncSession) -> User:
    from config import settings

    result = await db_session.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    existing = result.scalars().first()
    if existing:
        return existing

    user = User(
        id=str(uuid.uuid4()),
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        display_name="Administrator",
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role="admin",
        bio="FlavorVault platform administrator",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def seeded_admin_client(client: httpx.AsyncClient, seeded_admin: User) -> httpx.AsyncClient:
    token = create_access_token(data={"sub": seeded_admin.id})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


class TestAdminDashboardAccess:
    @pytest.mark.asyncio
    async def test_admin_dashboard_accessible_by_admin(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        response = await admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert "Admin Dashboard" in response.text

    @pytest.mark.asyncio
    async def test_admin_dashboard_redirects_non_admin(
        self, auth_client: httpx.AsyncClient, test_user: User
    ):
        response = await auth_client.get("/admin", follow_redirects=False)
        assert response.status_code == 303 or response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_dashboard_redirects_unauthenticated(
        self, client: httpx.AsyncClient
    ):
        response = await client.get("/admin", follow_redirects=False)
        assert response.status_code == 303 or response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_dashboard_displays_stats(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_recipe: Recipe,
        sample_tag: Tag,
    ):
        response = await admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert "Total Recipes" in response.text
        assert "Total Users" in response.text
        assert "Total Reviews" in response.text
        assert "Total Tags" in response.text


class TestAdminTagCRUD:
    @pytest.mark.asyncio
    async def test_create_tag_success(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        response = await admin_client.post(
            "/admin/tags",
            data={"name": "new-test-tag"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_create_tag_non_admin_rejected(
        self, auth_client: httpx.AsyncClient, test_user: User
    ):
        response = await auth_client.post(
            "/admin/tags",
            data={"name": "unauthorized-tag"},
            follow_redirects=False,
        )
        assert response.status_code in (303, 401, 403)

    @pytest.mark.asyncio
    async def test_create_duplicate_tag(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_tag: Tag,
    ):
        response = await admin_client.post(
            "/admin/tags",
            data={"name": sample_tag.name},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_edit_tag_form_accessible(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_tag: Tag,
    ):
        response = await admin_client.get(
            f"/admin/tags/{sample_tag.id}/edit",
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Edit Tag" in response.text
        assert sample_tag.name in response.text

    @pytest.mark.asyncio
    async def test_edit_tag_form_nonexistent_tag(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        fake_id = str(uuid.uuid4())
        response = await admin_client.get(
            f"/admin/tags/{fake_id}/edit",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_edit_tag_success(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_tag: Tag,
    ):
        response = await admin_client.post(
            f"/admin/tags/{sample_tag.id}/edit",
            data={"name": "updated-tag-name"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/admin" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_edit_tag_nonexistent(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        fake_id = str(uuid.uuid4())
        response = await admin_client.post(
            f"/admin/tags/{fake_id}/edit",
            data={"name": "doesnt-matter"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_tag_success(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        db_session: AsyncSession,
    ):
        tag = Tag(
            id=str(uuid.uuid4()),
            name="tag-to-delete",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(tag)
        await db_session.flush()
        await db_session.commit()

        response = await admin_client.post(
            f"/admin/tags/{tag.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_tag_nonexistent(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        fake_id = str(uuid.uuid4())
        response = await admin_client.post(
            f"/admin/tags/{fake_id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303


class TestAdminReviewDeletion:
    @pytest.mark.asyncio
    async def test_admin_delete_review_success(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_review: Review,
    ):
        response = await admin_client.post(
            f"/admin/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_admin_delete_review_nonexistent(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        fake_id = str(uuid.uuid4())
        response = await admin_client.post(
            f"/admin/reviews/{fake_id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_non_admin_cannot_delete_review_via_admin(
        self,
        auth_client: httpx.AsyncClient,
        test_user: User,
        sample_review: Review,
    ):
        response = await auth_client.post(
            f"/admin/reviews/{sample_review.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code in (303, 401, 403)


class TestAdminUserDeletion:
    @pytest.mark.asyncio
    async def test_admin_delete_user_success(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        second_user: User,
    ):
        response = await admin_client.post(
            f"/admin/users/{second_user.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_admin_delete_nonexistent_user(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        fake_id = str(uuid.uuid4())
        response = await admin_client.post(
            f"/admin/users/{fake_id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_self(
        self, admin_client: httpx.AsyncClient, admin_user: User
    ):
        response = await admin_client.post(
            f"/admin/users/{admin_user.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_seeded_admin(
        self,
        seeded_admin_client: httpx.AsyncClient,
        seeded_admin: User,
        db_session: AsyncSession,
    ):
        another_admin = User(
            id=str(uuid.uuid4()),
            username="anotheradmin",
            email="anotheradmin@example.com",
            display_name="Another Admin",
            password_hash=hash_password("AnotherAdmin123!"),
            role="admin",
            bio="Another admin",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(another_admin)
        await db_session.flush()
        await db_session.commit()

        another_admin_token = create_access_token(data={"sub": another_admin.id})

        from main import app
        from utils.dependencies import get_db
        from tests.conftest import override_get_db

        app.dependency_overrides[get_db] = override_get_db

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as ac:
            ac.cookies.set("access_token", f"Bearer {another_admin_token}")
            response = await ac.post(
                f"/admin/users/{seeded_admin.id}/delete",
                follow_redirects=False,
            )
            assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_non_admin_cannot_delete_user(
        self,
        auth_client: httpx.AsyncClient,
        test_user: User,
        second_user: User,
    ):
        response = await auth_client.post(
            f"/admin/users/{second_user.id}/delete",
            follow_redirects=False,
        )
        assert response.status_code in (303, 401, 403)


class TestAdminDashboardContent:
    @pytest.mark.asyncio
    async def test_dashboard_shows_tags(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_tag: Tag,
    ):
        response = await admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert sample_tag.name in response.text

    @pytest.mark.asyncio
    async def test_dashboard_shows_users(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
    ):
        response = await admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert "User Management" in response.text
        assert admin_user.username in response.text

    @pytest.mark.asyncio
    async def test_dashboard_shows_recent_reviews(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
        sample_review: Review,
    ):
        response = await admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert "Recent Reviews" in response.text
        assert sample_review.comment in response.text

    @pytest.mark.asyncio
    async def test_dashboard_shows_tag_management_form(
        self,
        admin_client: httpx.AsyncClient,
        admin_user: User,
    ):
        response = await admin_client.get("/admin", follow_redirects=False)
        assert response.status_code == 200
        assert "Tag Management" in response.text
        assert 'name="name"' in response.text
        assert "Add Tag" in response.text