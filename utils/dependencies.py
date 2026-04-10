import logging
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import SessionLocal
from models.user import User
from utils.security import decode_access_token

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:]

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        return None

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        return user
    except Exception:
        logger.exception("Error fetching current user from database")
        return None


async def require_auth(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Authentication required",
            headers={"Location": "/auth/login"},
        )
    return user


async def require_admin(
    request: Request,
    user: User = Depends(require_auth),
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Admin access required",
            headers={"Location": "/"},
        )
    return user


def add_flash_message(request: Request, message: str, message_type: str = "info") -> None:
    if not hasattr(request.state, "flash_messages"):
        request.state.flash_messages = []
    request.state.flash_messages.append({"text": message, "type": message_type})


def get_flash_messages(request: Request) -> list:
    session_messages = []
    if hasattr(request.state, "_flash_messages_from_session"):
        session_messages = request.state._flash_messages_from_session
    state_messages = []
    if hasattr(request.state, "flash_messages"):
        state_messages = request.state.flash_messages
    return session_messages + state_messages


def build_template_context(
    request: Request,
    user: Optional[User] = None,
    **kwargs,
) -> dict:
    flash_messages = get_flash_messages(request)
    context = {
        "user": user,
        "flash_messages": flash_messages,
    }
    context.update(kwargs)
    return context