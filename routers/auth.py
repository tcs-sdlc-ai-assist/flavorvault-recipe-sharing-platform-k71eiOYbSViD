import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.auth_service import authenticate_user, register_user
from utils.dependencies import (
    add_flash_message,
    build_template_context,
    get_current_user,
    get_db,
)
from utils.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


@router.get("/register")
async def register_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    if user is not None:
        return RedirectResponse(url="/", status_code=303)

    context = build_template_context(request, user=user)
    return templates.TemplateResponse(request, "auth/register.html", context=context)


@router.post("/register")
async def register_handler(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    display_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    if user is not None:
        return RedirectResponse(url="/", status_code=303)

    form_data = {
        "username": username,
        "email": email,
        "display_name": display_name or "",
    }

    errors = []

    username = username.strip()
    email = email.strip()

    if not username:
        errors.append("Username is required.")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters long.")
    elif len(username) > 50:
        errors.append("Username must be at most 50 characters long.")

    if not email:
        errors.append("Email is required.")

    if not password:
        errors.append("Password is required.")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not confirm_password:
        errors.append("Please confirm your password.")
    elif password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        context = build_template_context(
            request,
            user=None,
            errors=errors,
            form_data=form_data,
        )
        return templates.TemplateResponse(
            request, "auth/register.html", context=context, status_code=422
        )

    try:
        new_user = await register_user(
            db=db,
            username=username,
            email=email,
            password=password,
            display_name=display_name.strip() if display_name else None,
            role="user",
        )
        logger.info("User registered: username=%s email=%s", new_user.username, new_user.email)
    except ValueError as e:
        context = build_template_context(
            request,
            user=None,
            error=str(e),
            form_data=form_data,
        )
        return templates.TemplateResponse(
            request, "auth/register.html", context=context, status_code=422
        )

    token = create_access_token(data={"sub": new_user.id})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/login")
async def login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    if user is not None:
        return RedirectResponse(url="/", status_code=303)

    context = build_template_context(request, user=user)
    return templates.TemplateResponse(request, "auth/login.html", context=context)


@router.post("/login")
async def login_handler(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    if user is not None:
        return RedirectResponse(url="/", status_code=303)

    email = email.strip()

    if not email or not password:
        context = build_template_context(
            request,
            user=None,
            error="Email and password are required.",
            email=email,
        )
        return templates.TemplateResponse(
            request, "auth/login.html", context=context, status_code=422
        )

    authenticated_user = await authenticate_user(db=db, email=email, password=password)

    if authenticated_user is None:
        logger.warning("Failed login attempt for email=%s", email)
        context = build_template_context(
            request,
            user=None,
            error="Invalid email or password.",
            email=email,
        )
        return templates.TemplateResponse(
            request, "auth/login.html", context=context, status_code=401
        )

    logger.info("User logged in: user_id=%s email=%s", authenticated_user.id, authenticated_user.email)

    token = create_access_token(data={"sub": authenticated_user.id})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/logout")
async def logout_get(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@router.post("/logout")
async def logout_post(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response