import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from database import Base
from models.associations import favorites


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    recipes = relationship("Recipe", back_populates="author", lazy="selectin")
    reviews = relationship("Review", back_populates="user", lazy="selectin")
    favorite_recipes = relationship(
        "Recipe",
        secondary=favorites,
        back_populates="favorited_by",
        lazy="selectin",
    )