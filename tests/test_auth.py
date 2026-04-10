import uuid
from datetime import datetime, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from utils.security import hash_password, create_access_token


class TestRegistration:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_page_returns_200(self, client: httpx.AsyncClient):
        response = await client.get("/auth/register")
        assert response.status_code == 200
        assert "Create your account" in response.text

    @pytest.mark.asyncio
    async def test_register_page_redirects_authenticated_user(
        self, auth_client: httpx.AsyncClient
    ):
        response = await auth_client.get("/auth/register", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"

    @pytest.mark.asyncio
    async def test_register_success(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "display_name": "New User",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_register_success_sets_jwt_cookie(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "cookieuser",
                "email": "cookieuser@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        cookie_value = response.cookies.get("access_token")
        assert cookie_value is not None
        assert cookie_value.startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, client: httpx.AsyncClient, test_user: User
    ):
        response = await client.post(
            "/auth/register",
            data={
                "username": "anotheruser",
                "email": test_user.email,
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "already exists" in response.text

    @pytest.mark.asyncio
    async def test_register_duplicate_username(
        self, client: httpx.AsyncClient, test_user: User
    ):
        response = await client.post(
            "/auth/register",
            data={
                "username": test_user.username,
                "email": "unique@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "already exists" in response.text

    @pytest.mark.asyncio
    async def test_register_password_mismatch(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "mismatchuser",
                "email": "mismatch@example.com",
                "password": "StrongPass123!",
                "confirm_password": "DifferentPass456!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "do not match" in response.text

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "shortpwuser",
                "email": "shortpw@example.com",
                "password": "short",
                "confirm_password": "short",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "at least 8 characters" in response.text

    @pytest.mark.asyncio
    async def test_register_empty_username(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "",
                "email": "emptyuser@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "required" in response.text.lower() or "Username" in response.text

    @pytest.mark.asyncio
    async def test_register_short_username(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "ab",
                "email": "shortname@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "at least 3 characters" in response.text

    @pytest.mark.asyncio
    async def test_register_empty_email(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "noemailuser",
                "email": "",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "required" in response.text.lower() or "Email" in response.text

    @pytest.mark.asyncio
    async def test_register_without_display_name(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/register",
            data={
                "username": "nodisplayname",
                "email": "nodisplay@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/"

    @pytest.mark.asyncio
    async def test_register_post_redirects_authenticated_user(
        self, auth_client: httpx.AsyncClient
    ):
        response = await auth_client.post(
            "/auth/register",
            data={
                "username": "shouldnotwork",
                "email": "shouldnot@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/"


class TestLogin:
    """Tests for user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_page_returns_200(self, client: httpx.AsyncClient):
        response = await client.get("/auth/login")
        assert response.status_code == 200
        assert "Sign in" in response.text

    @pytest.mark.asyncio
    async def test_login_page_redirects_authenticated_user(
        self, auth_client: httpx.AsyncClient
    ):
        response = await auth_client.get("/auth/login", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"

    @pytest.mark.asyncio
    async def test_login_success(self, client: httpx.AsyncClient, test_user: User):
        response = await client.post(
            "/auth/login",
            data={
                "email": test_user.email,
                "password": "TestPass123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_success_sets_jwt_cookie(
        self, client: httpx.AsyncClient, test_user: User
    ):
        response = await client.post(
            "/auth/login",
            data={
                "email": test_user.email,
                "password": "TestPass123!",
            },
            follow_redirects=False,
        )
        cookie_value = response.cookies.get("access_token")
        assert cookie_value is not None
        assert cookie_value.startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, client: httpx.AsyncClient, test_user: User
    ):
        response = await client.post(
            "/auth/login",
            data={
                "email": test_user.email,
                "password": "WrongPassword123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.text

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/login",
            data={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.text

    @pytest.mark.asyncio
    async def test_login_empty_email(self, client: httpx.AsyncClient):
        response = await client.post(
            "/auth/login",
            data={
                "email": "",
                "password": "SomePassword123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "required" in response.text.lower() or "Email" in response.text

    @pytest.mark.asyncio
    async def test_login_empty_password(
        self, client: httpx.AsyncClient, test_user: User
    ):
        response = await client.post(
            "/auth/login",
            data={
                "email": test_user.email,
                "password": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "required" in response.text.lower() or "password" in response.text.lower()

    @pytest.mark.asyncio
    async def test_login_post_redirects_authenticated_user(
        self, auth_client: httpx.AsyncClient
    ):
        response = await auth_client.post(
            "/auth/login",
            data={
                "email": "any@example.com",
                "password": "AnyPassword123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/"


class TestLogout:
    """Tests for user logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_get_clears_cookie(self, auth_client: httpx.AsyncClient):
        response = await auth_client.get("/auth/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        set_cookie_header = response.headers.get("set-cookie", "")
        assert "access_token" in set_cookie_header

    @pytest.mark.asyncio
    async def test_logout_post_clears_cookie(self, auth_client: httpx.AsyncClient):
        response = await auth_client.post("/auth/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"
        set_cookie_header = response.headers.get("set-cookie", "")
        assert "access_token" in set_cookie_header

    @pytest.mark.asyncio
    async def test_logout_get_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.get("/auth/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"

    @pytest.mark.asyncio
    async def test_logout_post_unauthenticated(self, client: httpx.AsyncClient):
        response = await client.post("/auth/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/"


class TestJWTCookie:
    """Tests for JWT cookie behavior and authentication state."""

    @pytest.mark.asyncio
    async def test_valid_cookie_authenticates_user(
        self, auth_client: httpx.AsyncClient
    ):
        response = await auth_client.get("/profile", follow_redirects=False)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_cookie_does_not_authenticate(
        self, client: httpx.AsyncClient
    ):
        client.cookies.set("access_token", "Bearer invalid.token.here")
        response = await client.get("/profile", follow_redirects=False)
        assert response.status_code == 303
        assert "/auth/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_missing_cookie_does_not_authenticate(
        self, client: httpx.AsyncClient
    ):
        response = await client.get("/profile", follow_redirects=False)
        assert response.status_code == 303
        assert "/auth/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_expired_token_does_not_authenticate(
        self, client: httpx.AsyncClient, test_user: User
    ):
        from datetime import timedelta

        expired_token = create_access_token(
            data={"sub": test_user.id},
            expires_delta=timedelta(seconds=-10),
        )
        client.cookies.set("access_token", f"Bearer {expired_token}")
        response = await client.get("/profile", follow_redirects=False)
        assert response.status_code == 303
        assert "/auth/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_cookie_without_bearer_prefix_does_not_authenticate(
        self, client: httpx.AsyncClient, test_user: User
    ):
        token = create_access_token(data={"sub": test_user.id})
        client.cookies.set("access_token", token)
        response = await client.get("/profile", follow_redirects=False)
        assert response.status_code == 303
        assert "/auth/login" in response.headers.get("location", "")


class TestHealthCheck:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client: httpx.AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"