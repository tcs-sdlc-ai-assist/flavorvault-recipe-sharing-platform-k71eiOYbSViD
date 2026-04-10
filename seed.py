import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import Base, SessionLocal, engine
from models.user import User
from models.recipe import Recipe
from models.ingredient import Ingredient
from models.step import Step
from models.tag import Tag
from models.review import Review
from models.associations import recipe_tags, favorites
from utils.security import hash_password

logger = logging.getLogger(__name__)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def seed_admin_user(db: AsyncSession) -> None:
    result = await db.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    existing_admin = result.scalars().first()

    if existing_admin:
        logger.info("Admin user already exists: %s", settings.ADMIN_EMAIL)
        return

    admin_user = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        display_name=getattr(settings, "ADMIN_DISPLAY_NAME", "Administrator"),
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role="admin",
        bio="FlavorVault platform administrator",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(admin_user)
    await db.flush()
    logger.info("Admin user created: %s (%s)", settings.ADMIN_USERNAME, settings.ADMIN_EMAIL)


async def seed_default_tags(db: AsyncSession) -> None:
    default_tags = [
        "vegetarian",
        "vegan",
        "gluten-free",
        "dairy-free",
        "quick",
        "easy",
        "healthy",
        "comfort food",
        "dessert",
        "breakfast",
        "lunch",
        "dinner",
        "snack",
        "appetizer",
        "soup",
        "salad",
        "pasta",
        "seafood",
        "chicken",
        "beef",
        "pork",
        "baking",
        "grilling",
        "slow cooker",
        "one-pot",
        "meal prep",
        "low-carb",
        "high-protein",
        "kid-friendly",
        "holiday",
    ]

    now = datetime.now(timezone.utc)
    created_count = 0

    for tag_name in default_tags:
        result = await db.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        existing = result.scalars().first()
        if not existing:
            tag = Tag(
                name=tag_name,
                created_at=now,
                updated_at=now,
            )
            db.add(tag)
            created_count += 1

    if created_count > 0:
        await db.flush()
        logger.info("Created %d default tags", created_count)
    else:
        logger.info("All default tags already exist")


async def run_seed() -> None:
    logger.info("Starting database seed...")

    await create_tables()

    async with SessionLocal() as session:
        try:
            await seed_admin_user(session)
            await seed_default_tags(session)
            await session.commit()
            logger.info("Database seeding completed successfully")
        except Exception:
            await session.rollback()
            logger.exception("Error during database seeding")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-5.5s [%(name)s] %(message)s",
    )
    asyncio.run(run_seed())