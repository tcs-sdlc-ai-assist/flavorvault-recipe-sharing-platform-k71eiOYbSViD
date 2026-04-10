import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.recipe_service import (
    create_recipe,
    delete_recipe,
    get_favorite_count,
    get_recipe_by_id,
    get_recipe_rating_info,
    get_user_favorited_recipe_ids,
    is_user_favorite,
    search_recipes,
    toggle_favorite,
    update_recipe,
    get_all_tags,
)
from services.review_service import (
    get_reviews_for_recipe,
    get_user_review_for_recipe,
)
from utils.dependencies import (
    add_flash_message,
    build_template_context,
    get_current_user,
    get_db,
    require_auth,
)

logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


@router.get("/recipes")
async def browse_recipes(
    request: Request,
    q: Optional[str] = Query(None),
    tag: Optional[list[str]] = Query(None),
    difficulty: Optional[str] = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    per_page = 12
    recipes, total_count = await search_recipes(
        db=db,
        query=q,
        tag=tag,
        difficulty=difficulty,
        sort=sort,
        page=page,
        per_page=per_page,
    )

    total_pages = max(1, (total_count + per_page - 1) // per_page)

    all_tags = await get_all_tags(db)

    favorited_recipe_ids: set[str] = set()
    if user:
        favorited_recipe_ids = await get_user_favorited_recipe_ids(db, user.id)

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

    selected_tags = tag if tag else []

    context = build_template_context(
        request,
        user=user,
        recipes=recipe_list,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        search_query=q,
        sort=sort,
        tags=all_tags,
        selected_tags=selected_tags,
        selected_difficulty=difficulty,
        favorited_recipe_ids=favorited_recipe_ids,
    )
    return templates.TemplateResponse(request, "recipes/browse.html", context=context)


@router.get("/recipes/explore")
async def explore_recipes(
    request: Request,
    q: Optional[str] = Query(None),
    tag: Optional[list[str]] = Query(None),
    difficulty: Optional[str] = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    return await browse_recipes(
        request=request,
        q=q,
        tag=tag,
        difficulty=difficulty,
        sort=sort,
        page=page,
        db=db,
        user=user,
    )


@router.get("/recipes/mine")
async def my_recipes(
    request: Request,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    from services.recipe_service import get_recipes_by_author

    per_page = 12
    recipes, total_count = await get_recipes_by_author(
        db=db,
        author_id=user.id,
        page=page,
        per_page=per_page,
    )

    total_pages = max(1, (total_count + per_page - 1) // per_page)

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
    favorited_recipe_ids = await get_user_favorited_recipe_ids(db, user.id)

    context = build_template_context(
        request,
        user=user,
        recipes=recipe_list,
        total_count=total_count,
        total_pages=total_pages,
        current_page=page,
        search_query=None,
        sort="newest",
        tags=all_tags,
        selected_tags=[],
        selected_difficulty=None,
        favorited_recipe_ids=favorited_recipe_ids,
    )
    return templates.TemplateResponse(request, "recipes/browse.html", context=context)


@router.get("/recipes/create")
async def create_recipe_form(
    request: Request,
    user: User = Depends(require_auth),
):
    context = build_template_context(
        request,
        user=user,
        recipe=None,
    )
    return templates.TemplateResponse(request, "recipes/form.html", context=context)


@router.post("/recipes/create")
async def create_recipe_submit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
    title: str = Form(...),
    description: str = Form(""),
    prep_time_minutes: Optional[str] = Form(None),
    cook_time_minutes: Optional[str] = Form(None),
    servings: Optional[str] = Form(None),
    difficulty: str = Form(""),
    tags: str = Form(""),
    ingredient_count: int = Form(1),
    step_count: int = Form(1),
):
    form_data = await request.form()

    prep_time = None
    if prep_time_minutes and prep_time_minutes.strip():
        try:
            prep_time = int(prep_time_minutes)
        except ValueError:
            prep_time = None

    cook_time = None
    if cook_time_minutes and cook_time_minutes.strip():
        try:
            cook_time = int(cook_time_minutes)
        except ValueError:
            cook_time = None

    servings_int = None
    if servings and servings.strip():
        try:
            servings_int = int(servings)
        except ValueError:
            servings_int = None

    difficulty_val = difficulty.strip() if difficulty and difficulty.strip() else None

    tag_list = None
    if tags and tags.strip():
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    ingredients = []
    for i in range(ingredient_count):
        name = form_data.get(f"ingredient_name_{i}", "")
        if isinstance(name, str):
            name = name.strip()
        else:
            name = str(name).strip() if name else ""
        if not name:
            continue
        quantity = form_data.get(f"ingredient_quantity_{i}", "")
        if isinstance(quantity, str):
            quantity = quantity.strip()
        else:
            quantity = str(quantity).strip() if quantity else ""
        unit = form_data.get(f"ingredient_unit_{i}", "")
        if isinstance(unit, str):
            unit = unit.strip()
        else:
            unit = str(unit).strip() if unit else ""
        ingredients.append({
            "name": name,
            "quantity": quantity,
            "unit": unit if unit else None,
        })

    steps = []
    for i in range(step_count):
        instruction = form_data.get(f"step_{i}", "")
        if isinstance(instruction, str):
            instruction = instruction.strip()
        else:
            instruction = str(instruction).strip() if instruction else ""
        if not instruction:
            continue
        steps.append({
            "step_number": len(steps) + 1,
            "instruction": instruction,
        })

    try:
        recipe = await create_recipe(
            db=db,
            author_id=user.id,
            title=title.strip(),
            description=description.strip() if description else None,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time,
            servings=servings_int,
            difficulty=difficulty_val,
            tags=tag_list,
            ingredients=ingredients if ingredients else None,
            steps=steps if steps else None,
        )
        add_flash_message(request, "Recipe created successfully!", "success")
        return RedirectResponse(
            url=f"/recipes/{recipe.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logger.exception("Error creating recipe")
        add_flash_message(request, f"Error creating recipe: {str(e)}", "error")
        context = build_template_context(
            request,
            user=user,
            recipe=None,
        )
        return templates.TemplateResponse(
            request, "recipes/form.html", context=context, status_code=400
        )


@router.get("/recipes/{recipe_id}")
async def recipe_detail(
    request: Request,
    recipe_id: str,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    rating_info = await get_recipe_rating_info(db, recipe_id)
    favorite_count = await get_favorite_count(db, recipe_id)

    is_favorited = False
    if user:
        is_favorited = await is_user_favorite(db, user.id, recipe_id)

    reviews_data = await get_reviews_for_recipe(
        db=db,
        recipe_id=recipe_id,
        page=page,
        per_page=10,
    )

    user_has_reviewed = False
    if user:
        user_review = await get_user_review_for_recipe(db, recipe_id, user.id)
        user_has_reviewed = user_review is not None

    tag_names = [t.name for t in recipe.tags] if recipe.tags else []

    ingredient_list = []
    if recipe.ingredients:
        for ing in sorted(recipe.ingredients, key=lambda x: x.sort_order):
            ingredient_list.append({
                "name": ing.name,
                "quantity": ing.quantity,
                "unit": ing.unit,
            })

    step_list = []
    if recipe.steps:
        for s in sorted(recipe.steps, key=lambda x: x.step_number):
            step_list.append({
                "step_number": s.step_number,
                "instruction": s.instruction,
            })

    recipe_data = {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "author_id": recipe.author_id,
        "tags": tag_names,
        "ingredients": ingredient_list,
        "steps": step_list,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
    }

    context = build_template_context(
        request,
        user=user,
        recipe=recipe_data,
        author=recipe.author,
        avg_rating=rating_info["avg_rating"],
        review_count=rating_info["review_count"],
        favorite_count=favorite_count,
        is_favorited=is_favorited,
        reviews=reviews_data["reviews"],
        total_pages=reviews_data["total_pages"],
        current_page=reviews_data["current_page"],
        user_has_reviewed=user_has_reviewed,
    )
    return templates.TemplateResponse(request, "recipes/detail.html", context=context)


@router.get("/recipes/{recipe_id}/edit")
async def edit_recipe_form(
    request: Request,
    recipe_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this recipe")

    tag_names = [t.name for t in recipe.tags] if recipe.tags else []

    ingredient_list = []
    if recipe.ingredients:
        for ing in sorted(recipe.ingredients, key=lambda x: x.sort_order):
            ingredient_list.append({
                "name": ing.name,
                "quantity": ing.quantity,
                "unit": ing.unit,
            })

    step_list = []
    if recipe.steps:
        for s in sorted(recipe.steps, key=lambda x: x.step_number):
            step_list.append({
                "step_number": s.step_number,
                "instruction": s.instruction,
            })

    recipe_data = {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "prep_time_minutes": recipe.prep_time_minutes,
        "cook_time_minutes": recipe.cook_time_minutes,
        "servings": recipe.servings,
        "difficulty": recipe.difficulty,
        "author_id": recipe.author_id,
        "tags": tag_names,
        "ingredients": ingredient_list,
        "steps": step_list,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
    }

    context = build_template_context(
        request,
        user=user,
        recipe=recipe_data,
    )
    return templates.TemplateResponse(request, "recipes/form.html", context=context)


@router.post("/recipes/{recipe_id}/edit")
async def edit_recipe_submit(
    request: Request,
    recipe_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
    title: str = Form(...),
    description: str = Form(""),
    prep_time_minutes: Optional[str] = Form(None),
    cook_time_minutes: Optional[str] = Form(None),
    servings: Optional[str] = Form(None),
    difficulty: str = Form(""),
    tags: str = Form(""),
    ingredient_count: int = Form(1),
    step_count: int = Form(1),
):
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this recipe")

    form_data = await request.form()

    prep_time = None
    if prep_time_minutes and prep_time_minutes.strip():
        try:
            prep_time = int(prep_time_minutes)
        except ValueError:
            prep_time = None

    cook_time = None
    if cook_time_minutes and cook_time_minutes.strip():
        try:
            cook_time = int(cook_time_minutes)
        except ValueError:
            cook_time = None

    servings_int = None
    if servings and servings.strip():
        try:
            servings_int = int(servings)
        except ValueError:
            servings_int = None

    difficulty_val = difficulty.strip() if difficulty and difficulty.strip() else None

    tag_list = None
    if tags is not None:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    ingredients = []
    for i in range(ingredient_count):
        name = form_data.get(f"ingredient_name_{i}", "")
        if isinstance(name, str):
            name = name.strip()
        else:
            name = str(name).strip() if name else ""
        if not name:
            continue
        quantity = form_data.get(f"ingredient_quantity_{i}", "")
        if isinstance(quantity, str):
            quantity = quantity.strip()
        else:
            quantity = str(quantity).strip() if quantity else ""
        unit = form_data.get(f"ingredient_unit_{i}", "")
        if isinstance(unit, str):
            unit = unit.strip()
        else:
            unit = str(unit).strip() if unit else ""
        ingredients.append({
            "name": name,
            "quantity": quantity,
            "unit": unit if unit else None,
        })

    steps = []
    for i in range(step_count):
        instruction = form_data.get(f"step_{i}", "")
        if isinstance(instruction, str):
            instruction = instruction.strip()
        else:
            instruction = str(instruction).strip() if instruction else ""
        if not instruction:
            continue
        steps.append({
            "step_number": len(steps) + 1,
            "instruction": instruction,
        })

    try:
        updated_recipe = await update_recipe(
            db=db,
            recipe_id=recipe_id,
            title=title.strip(),
            description=description.strip() if description else None,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time,
            servings=servings_int,
            difficulty=difficulty_val,
            tags=tag_list,
            ingredients=ingredients,
            steps=steps,
        )
        if not updated_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        add_flash_message(request, "Recipe updated successfully!", "success")
        return RedirectResponse(
            url=f"/recipes/{recipe_id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating recipe")
        add_flash_message(request, f"Error updating recipe: {str(e)}", "error")

        tag_names = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        recipe_data = {
            "id": recipe_id,
            "title": title,
            "description": description,
            "prep_time_minutes": prep_time,
            "cook_time_minutes": cook_time,
            "servings": servings_int,
            "difficulty": difficulty_val,
            "author_id": recipe.author_id,
            "tags": tag_names,
            "ingredients": ingredients,
            "steps": steps,
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at,
        }
        context = build_template_context(
            request,
            user=user,
            recipe=recipe_data,
        )
        return templates.TemplateResponse(
            request, "recipes/form.html", context=context, status_code=400
        )


@router.post("/recipes/{recipe_id}/delete")
async def delete_recipe_handler(
    request: Request,
    recipe_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if recipe.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")

    deleted = await delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recipe not found")

    add_flash_message(request, "Recipe deleted successfully.", "success")
    return RedirectResponse(
        url="/recipes",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/recipes/{recipe_id}/favorite")
async def toggle_favorite_handler(
    request: Request,
    recipe_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    if not user:
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            raise HTTPException(status_code=401, detail="Authentication required")
        return RedirectResponse(
            url="/auth/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    recipe = await get_recipe_by_id(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    result = await toggle_favorite(db, user.id, recipe_id)

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        from fastapi.responses import JSONResponse
        return JSONResponse(content=result)

    return RedirectResponse(
        url=f"/recipes/{recipe_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/recipes/{recipe_id}/reviews")
async def submit_review(
    request: Request,
    recipe_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
    rating: int = Form(...),
    comment: str = Form(""),
):
    from services.review_service import create_review

    try:
        await create_review(
            db=db,
            recipe_id=recipe_id,
            user_id=user.id,
            rating=rating,
            comment=comment.strip() if comment else None,
        )
        add_flash_message(request, "Review submitted successfully!", "success")
    except ValueError as e:
        add_flash_message(request, str(e), "error")
    except Exception as e:
        logger.exception("Error submitting review")
        add_flash_message(request, f"Error submitting review: {str(e)}", "error")

    return RedirectResponse(
        url=f"/recipes/{recipe_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )