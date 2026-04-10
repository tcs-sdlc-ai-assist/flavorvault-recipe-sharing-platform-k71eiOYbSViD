import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.tag import Tag
from models.recipe import Recipe
from models.associations import recipe_tags


async def create_tag(db: AsyncSession, name: str) -> Tag:
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("Tag name cannot be empty or whitespace")

    result = await db.execute(
        select(Tag).where(func.lower(Tag.name) == normalized)
    )
    existing = result.scalars().first()
    if existing:
        return existing

    tag = Tag(
        id=str(uuid.uuid4()),
        name=normalized,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(tag)
    await db.flush()
    return tag


async def edit_tag(db: AsyncSession, tag_id: str, new_name: str) -> Optional[Tag]:
    normalized = new_name.strip().lower()
    if not normalized:
        raise ValueError("Tag name cannot be empty or whitespace")

    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalars().first()
    if not tag:
        return None

    duplicate_result = await db.execute(
        select(Tag).where(func.lower(Tag.name) == normalized, Tag.id != tag_id)
    )
    duplicate = duplicate_result.scalars().first()
    if duplicate:
        raise ValueError(f"A tag with the name '{normalized}' already exists")

    tag.name = normalized
    tag.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return tag


async def delete_tag(db: AsyncSession, tag_id: str) -> bool:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalars().first()
    if not tag:
        return False

    await db.execute(
        delete(recipe_tags).where(recipe_tags.c.tag_id == tag_id)
    )

    await db.delete(tag)
    await db.flush()
    return True


async def get_all_tags(db: AsyncSession) -> list[Tag]:
    result = await db.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


async def get_tag_by_id(db: AsyncSession, tag_id: str) -> Optional[Tag]:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalars().first()


async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    normalized = name.strip().lower()
    result = await db.execute(
        select(Tag).where(func.lower(Tag.name) == normalized)
    )
    return result.scalars().first()


async def assign_tags_to_recipe(
    db: AsyncSession, recipe: Recipe, tags_input: Optional[str | list[str]]
) -> list[Tag]:
    if tags_input is None:
        return []

    if isinstance(tags_input, str):
        tag_names = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
    else:
        tag_names = [t.strip().lower() for t in tags_input if t.strip()]

    tag_names = list(dict.fromkeys(tag_names))

    if not tag_names:
        recipe.tags = []
        await db.flush()
        return []

    tags: list[Tag] = []
    for name in tag_names:
        result = await db.execute(
            select(Tag).where(func.lower(Tag.name) == name)
        )
        existing = result.scalars().first()
        if existing:
            tags.append(existing)
        else:
            new_tag = Tag(
                id=str(uuid.uuid4()),
                name=name,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_tag)
            await db.flush()
            tags.append(new_tag)

    recipe.tags = tags
    await db.flush()
    return tags