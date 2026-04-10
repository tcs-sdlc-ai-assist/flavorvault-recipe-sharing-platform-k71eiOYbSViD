import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from models.recipe import Recipe
from models.review import Review
from models.tag import Tag
from models.user import User
from services.review_service import delete_review as service_delete_review
from services.tag_service import create_tag, delete_tag, edit_tag, get_all_tags, get_tag_by_id
from services.review_service import get_recent_reviews
from utils.dependencies import (
    add_flash_message,
    build_template_context,
    get_db,
    require_admin,
)

logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


@router.get("/admin")
async def admin_dashboard(
    request: Request,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_recipes_result = await db.execute(select(func.count(Recipe.id)))
    total_recipes = total_recipes_result.scalar() or 0

    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    total_reviews_result = await db.execute(select(func.count(Review.id)))
    total_reviews = total_reviews_result.scalar() or 0

    total_tags_result = await db.execute(select(func.count(Tag.id)))
    total_tags = total_tags_result.scalar() or 0

    stats = {
        "total_recipes": total_recipes,
        "total_users": total_users,
        "total_reviews": total_reviews,
        "total_tags": total_tags,
    }

    tags = await get_all_tags(db)

    recent_reviews = await get_recent_reviews(db, limit=10)

    users_result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = list(users_result.scalars().all())

    context = build_template_context(
        request,
        user=user,
        stats=stats,
        tags=tags,
        recent_reviews=recent_reviews,
        users=users,
        admin_email=settings.ADMIN_EMAIL,
    )
    return templates.TemplateResponse(request, "admin/dashboard.html", context=context)


@router.post("/admin/tags")
async def admin_create_tag(
    request: Request,
    name: str = Form(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        await create_tag(db, name)
        add_flash_message(request, f"Tag '{name.strip()}' created successfully.", "success")
    except ValueError as e:
        add_flash_message(request, str(e), "error")
    except Exception:
        logger.exception("Error creating tag")
        add_flash_message(request, "An error occurred while creating the tag.", "error")

    return RedirectResponse(url="/admin", status_code=303)


@router.get("/admin/tags/{tag_id}/edit")
async def admin_edit_tag_form(
    request: Request,
    tag_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    tag = await get_tag_by_id(db, tag_id)
    if not tag:
        add_flash_message(request, "Tag not found.", "error")
        return RedirectResponse(url="/admin", status_code=303)

    context = build_template_context(
        request,
        user=user,
        tag=tag,
        error=None,
    )
    return templates.TemplateResponse(request, "admin/tag_form.html", context=context)


@router.post("/admin/tags/{tag_id}/edit")
async def admin_edit_tag(
    request: Request,
    tag_id: str,
    name: str = Form(...),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    tag = await get_tag_by_id(db, tag_id)
    if not tag:
        add_flash_message(request, "Tag not found.", "error")
        return RedirectResponse(url="/admin", status_code=303)

    try:
        updated_tag = await edit_tag(db, tag_id, name)
        if updated_tag is None:
            add_flash_message(request, "Tag not found.", "error")
            return RedirectResponse(url="/admin", status_code=303)
        add_flash_message(request, f"Tag updated to '{name.strip()}'.", "success")
        return RedirectResponse(url="/admin", status_code=303)
    except ValueError as e:
        context = build_template_context(
            request,
            user=user,
            tag=tag,
            error=str(e),
        )
        return templates.TemplateResponse(request, "admin/tag_form.html", context=context)
    except Exception:
        logger.exception("Error editing tag")
        context = build_template_context(
            request,
            user=user,
            tag=tag,
            error="An unexpected error occurred.",
        )
        return templates.TemplateResponse(request, "admin/tag_form.html", context=context)


@router.post("/admin/tags/{tag_id}/delete")
async def admin_delete_tag(
    request: Request,
    tag_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        deleted = await delete_tag(db, tag_id)
        if deleted:
            add_flash_message(request, "Tag deleted successfully.", "success")
        else:
            add_flash_message(request, "Tag not found.", "error")
    except Exception:
        logger.exception("Error deleting tag")
        add_flash_message(request, "An error occurred while deleting the tag.", "error")

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/reviews/{review_id}/delete")
async def admin_delete_review(
    request: Request,
    review_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        deleted = await service_delete_review(db, review_id, user_id=user.id, is_admin=True)
        if deleted:
            add_flash_message(request, "Review deleted successfully.", "success")
        else:
            add_flash_message(request, "Review not found.", "error")
    except Exception:
        logger.exception("Error deleting review")
        add_flash_message(request, "An error occurred while deleting the review.", "error")

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/users/{user_id}/delete")
async def admin_delete_user(
    request: Request,
    user_id: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_result = await db.execute(select(User).where(User.id == user_id))
    target_user = target_result.scalars().first()

    if not target_user:
        add_flash_message(request, "User not found.", "error")
        return RedirectResponse(url="/admin", status_code=303)

    if target_user.role == "admin" and target_user.email == settings.ADMIN_EMAIL:
        add_flash_message(request, "Cannot delete the seeded admin account.", "error")
        return RedirectResponse(url="/admin", status_code=303)

    if target_user.id == user.id:
        add_flash_message(request, "You cannot delete your own account from the admin panel.", "error")
        return RedirectResponse(url="/admin", status_code=303)

    try:
        username = target_user.username
        await db.delete(target_user)
        await db.flush()
        add_flash_message(request, f"User '{username}' and all associated data deleted successfully.", "success")
    except Exception:
        logger.exception("Error deleting user %s", user_id)
        add_flash_message(request, "An error occurred while deleting the user.", "error")

    return RedirectResponse(url="/admin", status_code=303)