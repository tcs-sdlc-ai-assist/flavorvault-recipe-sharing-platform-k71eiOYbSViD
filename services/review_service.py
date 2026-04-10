import logging
from typing import Optional

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.review import Review
from models.recipe import Recipe

logger = logging.getLogger(__name__)


async def create_review(
    db: AsyncSession,
    recipe_id: str,
    user_id: str,
    rating: int,
    comment: Optional[str] = None,
) -> Review:
    existing = await db.execute(
        select(Review).where(
            Review.recipe_id == recipe_id,
            Review.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("You have already reviewed this recipe")

    recipe_result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    recipe = recipe_result.scalar_one_or_none()
    if recipe is None:
        raise ValueError("Recipe not found")

    if recipe.author_id == user_id:
        raise ValueError("You cannot review your own recipe")

    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")

    review = Review(
        recipe_id=recipe_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)

    logger.info(
        "Review created: user=%s recipe=%s rating=%d",
        user_id,
        recipe_id,
        rating,
    )
    return review


async def update_review(
    db: AsyncSession,
    review_id: str,
    user_id: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    is_admin: bool = False,
) -> Optional[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(selectinload(Review.user), selectinload(Review.recipe))
    )
    review = result.scalar_one_or_none()
    if review is None:
        return None

    if not is_admin and review.user_id != user_id:
        raise PermissionError("You do not have permission to edit this review")

    if rating is not None:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        review.rating = rating

    if comment is not None:
        review.comment = comment

    await db.flush()
    await db.refresh(review)

    logger.info("Review updated: review_id=%s", review_id)
    return review


async def delete_review(
    db: AsyncSession,
    review_id: str,
    user_id: str,
    is_admin: bool = False,
) -> bool:
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        return False

    if not is_admin and review.user_id != user_id:
        raise PermissionError("You do not have permission to delete this review")

    await db.delete(review)
    await db.flush()

    logger.info("Review deleted: review_id=%s by user=%s", review_id, user_id)
    return True


async def get_reviews_for_recipe(
    db: AsyncSession,
    recipe_id: str,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    count_result = await db.execute(
        select(func.count()).select_from(Review).where(Review.recipe_id == recipe_id)
    )
    total_count = count_result.scalar() or 0

    total_pages = max(1, (total_count + per_page - 1) // per_page)

    if page < 1:
        page = 1

    offset = (page - 1) * per_page

    result = await db.execute(
        select(Review)
        .where(Review.recipe_id == recipe_id)
        .options(selectinload(Review.user), selectinload(Review.recipe))
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    reviews = list(result.scalars().all())

    return {
        "reviews": reviews,
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
    }


async def get_review_by_id(
    db: AsyncSession,
    review_id: str,
) -> Optional[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.id == review_id)
        .options(selectinload(Review.user), selectinload(Review.recipe))
    )
    return result.scalar_one_or_none()


async def get_user_review_for_recipe(
    db: AsyncSession,
    recipe_id: str,
    user_id: str,
) -> Optional[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.recipe_id == recipe_id, Review.user_id == user_id)
        .options(selectinload(Review.user), selectinload(Review.recipe))
    )
    return result.scalar_one_or_none()


async def get_review_count_by_user(
    db: AsyncSession,
    user_id: str,
) -> int:
    result = await db.execute(
        select(func.count()).select_from(Review).where(Review.user_id == user_id)
    )
    return result.scalar() or 0


async def get_average_rating(
    db: AsyncSession,
    recipe_id: str,
) -> Optional[float]:
    result = await db.execute(
        select(func.avg(Review.rating)).where(Review.recipe_id == recipe_id)
    )
    avg = result.scalar()
    if avg is not None:
        return round(float(avg), 2)
    return None


async def get_review_count(
    db: AsyncSession,
    recipe_id: str,
) -> int:
    result = await db.execute(
        select(func.count()).select_from(Review).where(Review.recipe_id == recipe_id)
    )
    return result.scalar() or 0


async def get_recipe_rating_info(
    db: AsyncSession,
    recipe_id: str,
) -> dict:
    avg_rating = await get_average_rating(db, recipe_id)
    review_count = await get_review_count(db, recipe_id)
    return {
        "avg_rating": avg_rating,
        "review_count": review_count,
    }


async def get_recent_reviews(
    db: AsyncSession,
    limit: int = 10,
) -> list[Review]:
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.user), selectinload(Review.recipe))
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())