import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.associations import favorites, recipe_tags
from models.ingredient import Ingredient
from models.recipe import Recipe
from models.review import Review
from models.step import Step
from models.tag import Tag
from models.user import User


async def create_recipe(
    db: AsyncSession,
    author_id: str,
    title: str,
    description: Optional[str] = None,
    prep_time_minutes: Optional[int] = None,
    cook_time_minutes: Optional[int] = None,
    servings: Optional[int] = None,
    difficulty: Optional[str] = None,
    tags: Optional[list[str]] = None,
    ingredients: Optional[list[dict]] = None,
    steps: Optional[list[dict]] = None,
) -> Recipe:
    recipe_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    recipe = Recipe(
        id=recipe_id,
        title=title,
        description=description,
        prep_time_minutes=prep_time_minutes,
        cook_time_minutes=cook_time_minutes,
        servings=servings,
        difficulty=difficulty,
        author_id=author_id,
        created_at=now,
        updated_at=now,
    )
    db.add(recipe)

    if ingredients:
        for idx, ing in enumerate(ingredients):
            ingredient = Ingredient(
                id=str(uuid.uuid4()),
                recipe_id=recipe_id,
                name=ing["name"],
                quantity=ing.get("quantity", ""),
                unit=ing.get("unit"),
                sort_order=idx,
                created_at=now,
                updated_at=now,
            )
            db.add(ingredient)

    if steps:
        for step_data in steps:
            step = Step(
                id=str(uuid.uuid4()),
                recipe_id=recipe_id,
                step_number=step_data["step_number"],
                instruction=step_data["instruction"],
                created_at=now,
                updated_at=now,
            )
            db.add(step)

    if tags:
        for tag_name in tags:
            tag_name_stripped = tag_name.strip()
            if not tag_name_stripped:
                continue
            result = await db.execute(
                select(Tag).where(func.lower(Tag.name) == tag_name_stripped.lower())
            )
            tag = result.scalars().first()
            if not tag:
                tag = Tag(
                    id=str(uuid.uuid4()),
                    name=tag_name_stripped,
                    created_at=now,
                    updated_at=now,
                )
                db.add(tag)
                await db.flush()
            recipe.tags.append(tag)

    await db.flush()

    return await get_recipe_by_id(db, recipe_id)


async def update_recipe(
    db: AsyncSession,
    recipe_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    prep_time_minutes: Optional[int] = None,
    cook_time_minutes: Optional[int] = None,
    servings: Optional[int] = None,
    difficulty: Optional[str] = None,
    tags: Optional[list[str]] = None,
    ingredients: Optional[list[dict]] = None,
    steps: Optional[list[dict]] = None,
) -> Optional[Recipe]:
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return None

    now = datetime.now(timezone.utc)

    if title is not None:
        recipe.title = title
    if description is not None:
        recipe.description = description
    if prep_time_minutes is not None:
        recipe.prep_time_minutes = prep_time_minutes
    if cook_time_minutes is not None:
        recipe.cook_time_minutes = cook_time_minutes
    if servings is not None:
        recipe.servings = servings
    if difficulty is not None:
        recipe.difficulty = difficulty

    recipe.updated_at = now

    if ingredients is not None:
        await db.execute(
            delete(Ingredient).where(Ingredient.recipe_id == recipe_id)
        )
        for idx, ing in enumerate(ingredients):
            ingredient = Ingredient(
                id=str(uuid.uuid4()),
                recipe_id=recipe_id,
                name=ing["name"],
                quantity=ing.get("quantity", ""),
                unit=ing.get("unit"),
                sort_order=idx,
                created_at=now,
                updated_at=now,
            )
            db.add(ingredient)

    if steps is not None:
        await db.execute(
            delete(Step).where(Step.recipe_id == recipe_id)
        )
        for step_data in steps:
            step = Step(
                id=str(uuid.uuid4()),
                recipe_id=recipe_id,
                step_number=step_data["step_number"],
                instruction=step_data["instruction"],
                created_at=now,
                updated_at=now,
            )
            db.add(step)

    if tags is not None:
        recipe.tags.clear()
        for tag_name in tags:
            tag_name_stripped = tag_name.strip()
            if not tag_name_stripped:
                continue
            result = await db.execute(
                select(Tag).where(func.lower(Tag.name) == tag_name_stripped.lower())
            )
            tag = result.scalars().first()
            if not tag:
                tag = Tag(
                    id=str(uuid.uuid4()),
                    name=tag_name_stripped,
                    created_at=now,
                    updated_at=now,
                )
                db.add(tag)
                await db.flush()
            recipe.tags.append(tag)

    await db.flush()

    return await get_recipe_by_id(db, recipe_id)


async def delete_recipe(db: AsyncSession, recipe_id: str) -> bool:
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        return False

    await db.delete(recipe)
    await db.flush()
    return True


async def get_recipe_by_id(db: AsyncSession, recipe_id: str) -> Optional[Recipe]:
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.author),
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
            selectinload(Recipe.tags),
            selectinload(Recipe.reviews).selectinload(Review.user),
            selectinload(Recipe.favorited_by),
        )
    )
    return result.scalars().first()


async def search_recipes(
    db: AsyncSession,
    query: Optional[str] = None,
    tag: Optional[list[str]] = None,
    difficulty: Optional[str] = None,
    sort: str = "newest",
    page: int = 1,
    per_page: int = 12,
) -> tuple[list[Recipe], int]:
    stmt = select(Recipe).options(
        selectinload(Recipe.author),
        selectinload(Recipe.ingredients),
        selectinload(Recipe.steps),
        selectinload(Recipe.tags),
        selectinload(Recipe.reviews),
        selectinload(Recipe.favorited_by),
    )

    count_stmt = select(func.count(Recipe.id))

    if query:
        search_filter = (
            Recipe.title.ilike(f"%{query}%") | Recipe.description.ilike(f"%{query}%")
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if difficulty:
        stmt = stmt.where(func.lower(Recipe.difficulty) == difficulty.lower())
        count_stmt = count_stmt.where(func.lower(Recipe.difficulty) == difficulty.lower())

    if tag:
        for tag_name in tag:
            tag_subquery = (
                select(recipe_tags.c.recipe_id)
                .join(Tag, Tag.id == recipe_tags.c.tag_id)
                .where(func.lower(Tag.name) == tag_name.strip().lower())
            )
            stmt = stmt.where(Recipe.id.in_(tag_subquery))
            count_stmt = count_stmt.where(Recipe.id.in_(tag_subquery))

    if sort == "oldest":
        stmt = stmt.order_by(Recipe.created_at.asc())
    elif sort == "rating":
        avg_rating_subq = (
            select(
                Review.recipe_id,
                func.avg(Review.rating).label("avg_rating"),
            )
            .group_by(Review.recipe_id)
            .subquery()
        )
        stmt = (
            stmt.outerjoin(avg_rating_subq, Recipe.id == avg_rating_subq.c.recipe_id)
            .order_by(avg_rating_subq.c.avg_rating.desc().nullslast(), Recipe.created_at.desc())
        )
    elif sort == "popular":
        fav_count_subq = (
            select(
                favorites.c.recipe_id,
                func.count(favorites.c.user_id).label("fav_count"),
            )
            .group_by(favorites.c.recipe_id)
            .subquery()
        )
        stmt = (
            stmt.outerjoin(fav_count_subq, Recipe.id == fav_count_subq.c.recipe_id)
            .order_by(fav_count_subq.c.fav_count.desc().nullslast(), Recipe.created_at.desc())
        )
    else:
        stmt = stmt.order_by(Recipe.created_at.desc())

    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar() or 0

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    recipes = list(result.scalars().unique().all())

    return recipes, total_count


async def get_recipes_by_author(
    db: AsyncSession,
    author_id: str,
    page: int = 1,
    per_page: int = 12,
) -> tuple[list[Recipe], int]:
    stmt = (
        select(Recipe)
        .where(Recipe.author_id == author_id)
        .options(
            selectinload(Recipe.author),
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
            selectinload(Recipe.tags),
            selectinload(Recipe.reviews),
            selectinload(Recipe.favorited_by),
        )
        .order_by(Recipe.created_at.desc())
    )

    count_result = await db.execute(
        select(func.count(Recipe.id)).where(Recipe.author_id == author_id)
    )
    total_count = count_result.scalar() or 0

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    recipes = list(result.scalars().unique().all())

    return recipes, total_count


async def toggle_favorite(
    db: AsyncSession,
    user_id: str,
    recipe_id: str,
) -> dict:
    check_result = await db.execute(
        select(favorites).where(
            (favorites.c.user_id == user_id) & (favorites.c.recipe_id == recipe_id)
        )
    )
    existing = check_result.first()

    if existing:
        await db.execute(
            delete(favorites).where(
                (favorites.c.user_id == user_id) & (favorites.c.recipe_id == recipe_id)
            )
        )
        is_favorited = False
    else:
        await db.execute(
            favorites.insert().values(
                user_id=user_id,
                recipe_id=recipe_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        is_favorited = True

    await db.flush()

    count_result = await db.execute(
        select(func.count(favorites.c.user_id)).where(
            favorites.c.recipe_id == recipe_id
        )
    )
    favorite_count = count_result.scalar() or 0

    return {
        "is_favorited": is_favorited,
        "favorite_count": favorite_count,
    }


async def get_user_favorites(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    per_page: int = 12,
) -> tuple[list[Recipe], int]:
    fav_recipe_ids_stmt = select(favorites.c.recipe_id).where(
        favorites.c.user_id == user_id
    )

    count_result = await db.execute(
        select(func.count()).select_from(
            select(favorites.c.recipe_id).where(favorites.c.user_id == user_id).subquery()
        )
    )
    total_count = count_result.scalar() or 0

    stmt = (
        select(Recipe)
        .where(Recipe.id.in_(fav_recipe_ids_stmt))
        .options(
            selectinload(Recipe.author),
            selectinload(Recipe.ingredients),
            selectinload(Recipe.steps),
            selectinload(Recipe.tags),
            selectinload(Recipe.reviews),
            selectinload(Recipe.favorited_by),
        )
        .order_by(Recipe.created_at.desc())
    )

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    recipes = list(result.scalars().unique().all())

    return recipes, total_count


async def get_recipe_rating_info(
    db: AsyncSession,
    recipe_id: str,
) -> dict:
    result = await db.execute(
        select(
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        ).where(Review.recipe_id == recipe_id)
    )
    row = result.first()
    avg_rating = float(row.avg_rating) if row and row.avg_rating else None
    review_count = row.review_count if row else 0

    return {
        "avg_rating": avg_rating,
        "review_count": review_count,
    }


async def get_favorite_count(db: AsyncSession, recipe_id: str) -> int:
    result = await db.execute(
        select(func.count(favorites.c.user_id)).where(
            favorites.c.recipe_id == recipe_id
        )
    )
    return result.scalar() or 0


async def is_user_favorite(
    db: AsyncSession,
    user_id: str,
    recipe_id: str,
) -> bool:
    result = await db.execute(
        select(favorites).where(
            (favorites.c.user_id == user_id) & (favorites.c.recipe_id == recipe_id)
        )
    )
    return result.first() is not None


async def get_user_favorited_recipe_ids(
    db: AsyncSession,
    user_id: str,
) -> set[str]:
    result = await db.execute(
        select(favorites.c.recipe_id).where(favorites.c.user_id == user_id)
    )
    return {row[0] for row in result.fetchall()}


async def get_all_tags(db: AsyncSession) -> list[Tag]:
    result = await db.execute(
        select(Tag).order_by(Tag.name.asc())
    )
    return list(result.scalars().all())