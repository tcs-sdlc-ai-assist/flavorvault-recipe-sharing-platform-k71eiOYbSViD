import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from utils.security import hash_password, verify_password


async def register_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    display_name: Optional[str] = None,
    role: str = "user",
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    existing_email = result.scalars().first()
    if existing_email:
        raise ValueError("A user with this email already exists")

    result = await db.execute(select(User).where(User.username == username))
    existing_username = result.scalars().first()
    if existing_username:
        raise ValueError("A user with this username already exists")

    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        role=role,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def update_user(
    db: AsyncSession,
    user: User,
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    bio: Optional[str] = None,
    display_name: Optional[str] = None,
) -> User:
    if username is not None and username != user.username:
        result = await db.execute(
            select(User).where(User.username == username, User.id != user.id)
        )
        existing = result.scalars().first()
        if existing:
            raise ValueError("A user with this username already exists")
        user.username = username

    if email is not None and email != user.email:
        result = await db.execute(
            select(User).where(User.email == email, User.id != user.id)
        )
        existing = result.scalars().first()
        if existing:
            raise ValueError("A user with this email already exists")
        user.email = email

    if password is not None:
        user.password_hash = hash_password(password)

    if bio is not None:
        user.bio = bio

    if display_name is not None:
        user.display_name = display_name

    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return user