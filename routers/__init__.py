from routers.auth import router as auth_router
from routers.recipes import router as recipes_router
from routers.reviews import router as reviews_router
from routers.profile import router as profile_router
from routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "recipes_router",
    "reviews_router",
    "profile_router",
    "admin_router",
]