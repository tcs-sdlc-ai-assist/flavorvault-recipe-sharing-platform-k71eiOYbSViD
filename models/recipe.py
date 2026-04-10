import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base
from models.associations import recipe_tags, favorites


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(Integer, nullable=True)
    difficulty = Column(String(20), nullable=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    author = relationship("User", back_populates="recipes", lazy="selectin")
    ingredients = relationship("Ingredient", back_populates="recipe", lazy="selectin", cascade="all, delete-orphan")
    steps = relationship("Step", back_populates="recipe", lazy="selectin", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="recipe", lazy="selectin", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=recipe_tags, back_populates="recipes", lazy="selectin")
    favorited_by = relationship("User", secondary=favorites, back_populates="favorite_recipes", lazy="selectin")