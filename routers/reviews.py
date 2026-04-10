import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.review_service import (
    create_review,
    delete_review,
    get_review_by_id,
    update_review,
)
from utils.dependencies import (
    add_flash_message,
    build_template_context,
    get_db,
    require_auth,
)

logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


@router.post("/recipes/{recipe_id}/reviews")
async def submit_review(
    request: Request,
    recipe_id: str,
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if rating < 1 or rating > 5:
        add_flash_message(request, "Rating must be between 1 and 5.", "error")
        return RedirectResponse(
            url=f"/recipes/{recipe_id}",
            status_code=303,
        )

    try:
        await create_review(
            db=db,
            recipe_id=recipe_id,
            user_id=user.id,
            rating=rating,
            comment=comment if comment and comment.strip() else None,
        )
        add_flash_message(request, "Your review has been submitted.", "success")
    except ValueError as e:
        add_flash_message(request, str(e), "error")
    except Exception:
        logger.exception("Error creating review for recipe %s", recipe_id)
        add_flash_message(request, "An error occurred while submitting your review.", "error")

    return RedirectResponse(
        url=f"/recipes/{recipe_id}",
        status_code=303,
    )


@router.get("/reviews/{review_id}/edit")
async def edit_review_form(
    request: Request,
    review_id: str,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Response:
    review = await get_review_by_id(db, review_id)
    if review is None:
        add_flash_message(request, "Review not found.", "error")
        return RedirectResponse(url="/recipes", status_code=303)

    is_admin = user.role == "admin"
    if review.user_id != user.id and not is_admin:
        add_flash_message(request, "You do not have permission to edit this review.", "error")
        return RedirectResponse(
            url=f"/recipes/{review.recipe_id}",
            status_code=303,
        )

    context = build_template_context(
        request,
        user=user,
        review=review,
        recipe=review.recipe,
    )
    return templates.TemplateResponse(
        request,
        "reviews/edit.html",
        context=context,
    )


@router.post("/reviews/{review_id}/edit")
async def edit_review_submit(
    request: Request,
    review_id: str,
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Response:
    review = await get_review_by_id(db, review_id)
    if review is None:
        add_flash_message(request, "Review not found.", "error")
        return RedirectResponse(url="/recipes", status_code=303)

    is_admin = user.role == "admin"

    try:
        updated = await update_review(
            db=db,
            review_id=review_id,
            user_id=user.id,
            rating=rating,
            comment=comment if comment and comment.strip() else None,
            is_admin=is_admin,
        )
        if updated is None:
            add_flash_message(request, "Review not found.", "error")
            return RedirectResponse(url="/recipes", status_code=303)

        add_flash_message(request, "Your review has been updated.", "success")
    except PermissionError:
        add_flash_message(request, "You do not have permission to edit this review.", "error")
    except ValueError as e:
        add_flash_message(request, str(e), "error")
        return RedirectResponse(
            url=f"/reviews/{review_id}/edit",
            status_code=303,
        )
    except Exception:
        logger.exception("Error updating review %s", review_id)
        add_flash_message(request, "An error occurred while updating your review.", "error")
        return RedirectResponse(
            url=f"/reviews/{review_id}/edit",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/recipes/{review.recipe_id}",
        status_code=303,
    )


@router.post("/reviews/{review_id}/delete")
async def delete_review_handler(
    request: Request,
    review_id: str,
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> Response:
    review = await get_review_by_id(db, review_id)
    if review is None:
        add_flash_message(request, "Review not found.", "error")
        return RedirectResponse(url="/recipes", status_code=303)

    recipe_id = review.recipe_id
    is_admin = user.role == "admin"

    try:
        deleted = await delete_review(
            db=db,
            review_id=review_id,
            user_id=user.id,
            is_admin=is_admin,
        )
        if deleted:
            add_flash_message(request, "Review has been deleted.", "success")
        else:
            add_flash_message(request, "Review not found.", "error")
    except PermissionError:
        add_flash_message(request, "You do not have permission to delete this review.", "error")
    except Exception:
        logger.exception("Error deleting review %s", review_id)
        add_flash_message(request, "An error occurred while deleting the review.", "error")

    return RedirectResponse(
        url=f"/recipes/{recipe_id}",
        status_code=303,
    )