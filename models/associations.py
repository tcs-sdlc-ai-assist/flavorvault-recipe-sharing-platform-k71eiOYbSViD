from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from datetime import datetime, timezone

from database import Base

recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", String(36), ForeignKey("recipes.id"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id"), primary_key=True),
)

favorites = Table(
    "favorites",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("recipe_id", String(36), ForeignKey("recipes.id"), primary_key=True),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc), nullable=False),
)