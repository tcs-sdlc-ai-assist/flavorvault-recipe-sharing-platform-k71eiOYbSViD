import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.auth_service import update_user
from services.recipe_service import (
    get_recipes_by_author,
    get_user_favorites,
    get_recipe_rating_info,
)
from services.review_service import get_review_count_by_user
from utils.dependencies import (
    get_db,
    get_current_user,
    require_auth,
    add_flash_message,
    build_template_context,
)

logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


def _recipe_to_dict(recipe, rating_info: dict) -> dict:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "author_id": recipe.author_id,
        "tags": [tag.name for tag in recipe.tags] if recipe.tags else [],
        "avg_rating": rating_info.get("avg_rating"),
        "review_count": rating_info.get("review_count", 0),
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
    }


@router.get("/profile")
async def profile_page(
    request: Request,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    recipes_list, recipe_count = await get_recipes_by_author(db, user.id, page=1, per_page=50)

    recipes = []
    for recipe in recipes_list:
        rating_info = await get_recipe_rating_info(db, recipe.id)
        recipes.append(_recipe_to_dict(recipe, rating_info))

    favorites_list, favorite_count = await get_user_favorites(db, user.id, page=1, per_page=50)

    favorites = []
    for recipe in favorites_list:
        rating_info = await get_recipe_rating_info(db, recipe.id)
        favorites.append(_recipe_to_dict(recipe, rating_info))

    review_count = await get_review_count_by_user(db, user.id)

    context = build_template_context(
        request,
        user=user,
        profile_user=user,
        recipes=recipes,
        recipe_count=recipe_count,
        favorites=favorites,
        favorite_count=favorite_count,
        review_count=review_count,
    )

    return templates.TemplateResponse(request, "profile/index.html", context=context)


@router.get("/favorites")
async def favorites_page(
    request: Request,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    favorites_list, total_count = await get_user_favorites(db, user.id, page=1, per_page=50)

    favorites = []
    for recipe in favorites_list:
        rating_info = await get_recipe_rating_info(db, recipe.id)
        favorites.append(_recipe_to_dict(recipe, rating_info))

    context = build_template_context(
        request,
        user=user,
        favorites=favorites,
        total_count=total_count,
    )

    return templates.TemplateResponse(request, "profile/favorites.html", context=context)


@router.post("/profile")
async def update_profile(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    bio: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    confirm_password: Optional[str] = Form(None),
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    username = username.strip()
    email = email.strip()

    if not username:
        add_flash_message(request, "Username must not be empty.", "error")
        return RedirectResponse(url="/profile#settings", status_code=303)

    if len(username) < 3:
        add_flash_message(request, "Username must be at least 3 characters long.", "error")
        return RedirectResponse(url="/profile#settings", status_code=303)

    if len(username) > 50:
        add_flash_message(request, "Username must be at most 50 characters long.", "error")
        return RedirectResponse(url="/profile#settings", status_code=303)

    if not email:
        add_flash_message(request, "Email must not be empty.", "error")
        return RedirectResponse(url="/profile#settings", status_code=303)

    update_password = None
    if password:
        if len(password) < 8:
            add_flash_message(request, "Password must be at least 8 characters long.", "error")
            return RedirectResponse(url="/profile#settings", status_code=303)
        if password != confirm_password:
            add_flash_message(request, "Passwords do not match.", "error")
            return RedirectResponse(url="/profile#settings", status_code=303)
        update_password = password

    try:
        await update_user(
            db=db,
            user=user,
            username=username,
            email=email,
            password=update_password,
            bio=bio if bio is not None else user.bio,
        )
        add_flash_message(request, "Profile updated successfully.", "success")
    except ValueError as e:
        add_flash_message(request, str(e), "error")
        return RedirectResponse(url="/profile#settings", status_code=303)
    except Exception:
        logger.exception("Error updating profile for user %s", user.id)
        add_flash_message(request, "An unexpected error occurred. Please try again.", "error")
        return RedirectResponse(url="/profile#settings", status_code=303)

    return RedirectResponse(url="/profile#settings", status_code=303)