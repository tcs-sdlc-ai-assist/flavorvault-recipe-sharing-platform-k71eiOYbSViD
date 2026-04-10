import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database import engine, Base
from models.user import User
from seed import run_seed
from utils.dependencies import build_template_context, get_current_user, get_db

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(levelname)-5.5s [%(name)s] %(message)s",
)


class FlashMessageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.flash_messages = []
        request.state._flash_messages_from_session = []
        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FlavorVault application...")
    try:
        await run_seed()
        logger.info("Database seed completed successfully")
    except Exception:
        logger.exception("Error during database seed on startup")
    yield
    logger.info("Shutting down FlavorVault application...")


app = FastAPI(
    title="FlavorVault",
    description="A modern recipe management and sharing platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(FlashMessageMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

from routers.auth import router as auth_router
from routers.recipes import router as recipes_router
from routers.reviews import router as reviews_router
from routers.profile import router as profile_router
from routers.admin import router as admin_router

app.include_router(auth_router)
app.include_router(recipes_router)
app.include_router(reviews_router)
app.include_router(profile_router)
app.include_router(admin_router)


@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy", "version": "1.0.0"})


@app.get("/")
async def homepage(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    from services.recipe_service import search_recipes, get_recipe_rating_info, get_all_tags

    recipes, total_count = await search_recipes(
        db=db,
        query=None,
        tag=None,
        difficulty=None,
        sort="newest",
        page=1,
        per_page=6,
    )

    recipe_list = []
    for recipe in recipes:
        rating_info = await get_recipe_rating_info(db, recipe.id)
        tag_names = [t.name for t in recipe.tags] if recipe.tags else []
        recipe_list.append({
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "prep_time_minutes": recipe.prep_time_minutes,
            "cook_time_minutes": recipe.cook_time_minutes,
            "servings": recipe.servings,
            "difficulty": recipe.difficulty,
            "author_id": recipe.author_id,
            "tags": tag_names,
            "avg_rating": rating_info["avg_rating"],
            "review_count": rating_info["review_count"],
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at,
        })

    all_tags = await get_all_tags(db)

    context = build_template_context(
        request,
        user=user,
        recipes=recipe_list,
        total_count=total_count,
        tags=all_tags,
    )

    home_template = templates_dir / "home.html"
    if home_template.exists():
        return templates.TemplateResponse(request, "home.html", context=context)

    return RedirectResponse(url="/recipes", status_code=303)


@app.get("/about")
async def about_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    context = build_template_context(request, user=user)
    about_template = templates_dir / "about.html"
    if about_template.exists():
        return templates.TemplateResponse(request, "about.html", context=context)
    return HTMLResponse(
        content="<html><head><title>About - FlavorVault</title></head>"
        "<body><h1>About FlavorVault</h1>"
        "<p>A modern recipe management and sharing platform.</p>"
        '<p><a href="/">Back to Home</a></p></body></html>'
    )


@app.get("/privacy")
async def privacy_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    context = build_template_context(request, user=user)
    privacy_template = templates_dir / "privacy.html"
    if privacy_template.exists():
        return templates.TemplateResponse(request, "privacy.html", context=context)
    return HTMLResponse(
        content="<html><head><title>Privacy Policy - FlavorVault</title></head>"
        "<body><h1>Privacy Policy</h1>"
        "<p>Your privacy is important to us.</p>"
        '<p><a href="/">Back to Home</a></p></body></html>'
    )


@app.get("/terms")
async def terms_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    context = build_template_context(request, user=user)
    terms_template = templates_dir / "terms.html"
    if terms_template.exists():
        return templates.TemplateResponse(request, "terms.html", context=context)
    return HTMLResponse(
        content="<html><head><title>Terms of Service - FlavorVault</title></head>"
        "<body><h1>Terms of Service</h1>"
        "<p>By using FlavorVault, you agree to these terms.</p>"
        '<p><a href="/">Back to Home</a></p></body></html>'
    )


@app.get("/collections")
async def collections_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    if user is None:
        return RedirectResponse(url="/auth/login", status_code=303)
    return RedirectResponse(url="/favorites", status_code=303)