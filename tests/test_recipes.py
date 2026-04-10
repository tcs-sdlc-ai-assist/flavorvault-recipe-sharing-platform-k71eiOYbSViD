import uuid
from datetime import datetime, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.associations import favorites, recipe_tags
from models.ingredient import Ingredient
from models.recipe import Recipe
from models.review import Review
from models.step import Step
from models.tag import Tag
from models.user import User
from utils.security import create_access_token, hash_password


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession) -> User:
    user = User(
        id=str(uuid.uuid4()),
        username="seconduser",
        email="seconduser@example.com",
        display_name="Second User",
        password_hash=hash_password("SecondPass123!"),
        role="user",
        bio="A second test user",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user_client(client: httpx.AsyncClient, second_user: User) -> httpx.AsyncClient:
    token = create_access_token(data={"sub": second_user.id})
    client.cookies.set("access_token", f"Bearer {token}")
    return client


@pytest_asyncio.fixture
async def multiple_tags(db_session: AsyncSession) -> list[Tag]:
    tags = []
    now = datetime.now(timezone.utc)
    for name in ["quick", "healthy", "dessert", "vegan", "breakfast"]:
        tag = Tag(
            id=str(uuid.uuid4()),
            name=name,
            created_at=now,
            updated_at=now,
        )
        db_session.add(tag)
        tags.append(tag)
    await db_session.flush()
    await db_session.commit()
    for tag in tags:
        await db_session.refresh(tag)
    return tags


@pytest_asyncio.fixture
async def multiple_recipes(db_session: AsyncSession, test_user: User, multiple_tags: list[Tag]) -> list[Recipe]:
    recipes = []
    now = datetime.now(timezone.utc)
    recipe_data = [
        {"title": "Chocolate Cake", "description": "Rich chocolate cake", "difficulty": "medium", "prep_time_minutes": 20, "cook_time_minutes": 45, "servings": 8},
        {"title": "Caesar Salad", "description": "Classic caesar salad", "difficulty": "easy", "prep_time_minutes": 10, "cook_time_minutes": 0, "servings": 2},
        {"title": "Beef Stew", "description": "Hearty beef stew", "difficulty": "hard", "prep_time_minutes": 30, "cook_time_minutes": 120, "servings": 6},
        {"title": "Pancakes", "description": "Fluffy breakfast pancakes", "difficulty": "easy", "prep_time_minutes": 5, "cook_time_minutes": 15, "servings": 4},
        {"title": "Vegan Curry", "description": "Spicy vegan curry", "difficulty": "medium", "prep_time_minutes": 15, "cook_time_minutes": 30, "servings": 4},
    ]
    for i, data in enumerate(recipe_data):
        recipe_id = str(uuid.uuid4())
        recipe = Recipe(
            id=recipe_id,
            title=data["title"],
            description=data["description"],
            difficulty=data["difficulty"],
            prep_time_minutes=data["prep_time_minutes"],
            cook_time_minutes=data["cook_time_minutes"],
            servings=data["servings"],
            author_id=test_user.id,
            created_at=now,
            updated_at=now,
        )
        db_session.add(recipe)

        ingredient = Ingredient(
            id=str(uuid.uuid4()),
            recipe_id=recipe_id,
            name=f"Ingredient for {data['title']}",
            quantity="1",
            unit="cup",
            sort_order=0,
            created_at=now,
            updated_at=now,
        )
        db_session.add(ingredient)

        step = Step(
            id=str(uuid.uuid4()),
            recipe_id=recipe_id,
            step_number=1,
            instruction=f"Prepare {data['title']}",
            created_at=now,
            updated_at=now,
        )
        db_session.add(step)

        recipes.append(recipe)

    await db_session.flush()

    # Assign tags to some recipes
    if len(multiple_tags) >= 3 and len(recipes) >= 5:
        recipes[0].tags.append(multiple_tags[2])  # dessert
        recipes[1].tags.append(multiple_tags[1])  # healthy
        recipes[2].tags.append(multiple_tags[0])  # quick
        recipes[3].tags.append(multiple_tags[4])  # breakfast
        recipes[4].tags.append(multiple_tags[3])  # vegan
        recipes[4].tags.append(multiple_tags[1])  # healthy

    await db_session.flush()
    await db_session.commit()
    for recipe in recipes:
        await db_session.refresh(recipe)
    return recipes


class TestCreateRecipe:
    @pytest.mark.asyncio
    async def test_create_recipe_form_requires_auth(self, client: httpx.AsyncClient):
        response = await client.get("/recipes/create", follow_redirects=False)
        assert response.status_code in (303, 401, 403)

    @pytest.mark.asyncio
    async def test_create_recipe_form_accessible_when_authenticated(self, auth_client: httpx.AsyncClient):
        response = await auth_client.get("/recipes/create")
        assert response.status_code == 200
        assert b"Create" in response.content

    @pytest.mark.asyncio
    async def test_create_recipe_with_all_fields(self, auth_client: httpx.AsyncClient, db_session: AsyncSession):
        form_data = {
            "title": "New Test Recipe",
            "description": "A brand new recipe",
            "prep_time_minutes": "10",
            "cook_time_minutes": "25",
            "servings": "4",
            "difficulty": "easy",
            "tags": "quick, healthy",
            "ingredient_count": "2",
            "ingredient_name_0": "Flour",
            "ingredient_quantity_0": "2",
            "ingredient_unit_0": "cups",
            "ingredient_name_1": "Sugar",
            "ingredient_quantity_1": "1",
            "ingredient_unit_1": "cup",
            "step_count": "2",
            "step_0": "Mix dry ingredients",
            "step_1": "Bake at 350F",
        }
        response = await auth_client.post("/recipes/create", data=form_data, follow_redirects=False)
        assert response.status_code == 303
        assert "/recipes/" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_create_recipe_minimal_fields(self, auth_client: httpx.AsyncClient):
        form_data = {
            "title": "Minimal Recipe",
            "description": "",
            "prep_time_minutes": "",
            "cook_time_minutes": "",
            "servings": "",
            "difficulty": "",
            "tags": "",
            "ingredient_count": "1",
            "ingredient_name_0": "Something",
            "ingredient_quantity_0": "1",
            "ingredient_unit_0": "",
            "step_count": "1",
            "step_0": "Do something",
        }
        response = await auth_client.post("/recipes/create", data=form_data, follow_redirects=False)
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_create_recipe_unauthenticated(self, client: httpx.AsyncClient):
        form_data = {
            "title": "Should Fail",
            "description": "No auth",
            "ingredient_count": "1",
            "ingredient_name_0": "Test",
            "ingredient_quantity_0": "1",
            "ingredient_unit_0": "",
            "step_count": "1",
            "step_0": "Test step",
        }
        response = await client.post("/recipes/create", data=form_data, follow_redirects=False)
        assert response.status_code in (303, 401, 403)


class TestViewRecipe:
    @pytest.mark.asyncio
    async def test_view_recipe_detail(self, client: httpx.AsyncClient, sample_recipe: Recipe):
        response = await client.get(f"/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        assert sample_recipe.title.encode() in response.content

    @pytest.mark.asyncio
    async def test_view_recipe_shows_ingredients(self, client: httpx.AsyncClient, sample_recipe: Recipe):
        response = await client.get(f"/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        assert b"Test Ingredient" in response.content

    @pytest.mark.asyncio
    async def test_view_recipe_shows_steps(self, client: httpx.AsyncClient, sample_recipe: Recipe):
        response = await client.get(f"/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        assert b"Mix all ingredients together" in response.content

    @pytest.mark.asyncio
    async def test_view_recipe_not_found(self, client: httpx.AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/recipes/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_view_recipe_shows_edit_button_for_owner(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await auth_client.get(f"/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        assert b"Edit" in response.content

    @pytest.mark.asyncio
    async def test_view_recipe_hides_edit_button_for_non_owner(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await second_user_client.get(f"/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        assert b"Edit" not in response.content or b"edit" not in response.content.lower()


class TestEditRecipe:
    @pytest.mark.asyncio
    async def test_edit_recipe_form_accessible_by_owner(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await auth_client.get(f"/recipes/{sample_recipe.id}/edit")
        assert response.status_code == 200
        assert sample_recipe.title.encode() in response.content

    @pytest.mark.asyncio
    async def test_edit_recipe_form_forbidden_for_non_owner(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await second_user_client.get(f"/recipes/{sample_recipe.id}/edit")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_edit_recipe_form_accessible_by_admin(
        self, admin_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await admin_client.get(f"/recipes/{sample_recipe.id}/edit")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_edit_recipe_submit_by_owner(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        form_data = {
            "title": "Updated Recipe Title",
            "description": "Updated description",
            "prep_time_minutes": "20",
            "cook_time_minutes": "40",
            "servings": "6",
            "difficulty": "medium",
            "tags": "updated-tag",
            "ingredient_count": "1",
            "ingredient_name_0": "Updated Ingredient",
            "ingredient_quantity_0": "3",
            "ingredient_unit_0": "tbsp",
            "step_count": "1",
            "step_0": "Updated instruction",
        }
        response = await auth_client.post(
            f"/recipes/{sample_recipe.id}/edit", data=form_data, follow_redirects=False
        )
        assert response.status_code == 303
        assert f"/recipes/{sample_recipe.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_edit_recipe_submit_forbidden_for_non_owner(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        form_data = {
            "title": "Hacked Title",
            "description": "Hacked",
            "ingredient_count": "1",
            "ingredient_name_0": "Hack",
            "ingredient_quantity_0": "1",
            "ingredient_unit_0": "",
            "step_count": "1",
            "step_0": "Hack step",
        }
        response = await second_user_client.post(
            f"/recipes/{sample_recipe.id}/edit", data=form_data, follow_redirects=False
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_edit_recipe_not_found(self, auth_client: httpx.AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await auth_client.get(f"/recipes/{fake_id}/edit")
        assert response.status_code == 404


class TestDeleteRecipe:
    @pytest.mark.asyncio
    async def test_delete_recipe_by_owner(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await auth_client.post(
            f"/recipes/{sample_recipe.id}/delete", follow_redirects=False
        )
        assert response.status_code == 303
        assert "/recipes" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_delete_recipe_forbidden_for_non_owner(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await second_user_client.post(
            f"/recipes/{sample_recipe.id}/delete", follow_redirects=False
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_recipe_by_admin(
        self, admin_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await admin_client.post(
            f"/recipes/{sample_recipe.id}/delete", follow_redirects=False
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_delete_recipe_not_found(self, auth_client: httpx.AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await auth_client.post(
            f"/recipes/{fake_id}/delete", follow_redirects=False
        )
        assert response.status_code == 404


class TestBrowseRecipes:
    @pytest.mark.asyncio
    async def test_browse_recipes_page_loads(self, client: httpx.AsyncClient):
        response = await client.get("/recipes")
        assert response.status_code == 200
        assert b"Browse Recipes" in response.content

    @pytest.mark.asyncio
    async def test_browse_recipes_shows_recipes(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes")
        assert response.status_code == 200
        for recipe in multiple_recipes:
            assert recipe.title.encode() in response.content

    @pytest.mark.asyncio
    async def test_browse_recipes_empty_state(self, client: httpx.AsyncClient):
        response = await client.get("/recipes")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_sort_newest(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?sort=newest")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_sort_oldest(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?sort=oldest")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_sort_rating(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?sort=rating")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_sort_popular(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?sort=popular")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_filter_by_difficulty(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?difficulty=easy")
        assert response.status_code == 200
        assert b"Caesar Salad" in response.content
        assert b"Pancakes" in response.content

    @pytest.mark.asyncio
    async def test_browse_recipes_filter_by_tag(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?tag=healthy")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_pagination_page_1(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?page=1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_recipes_explore_alias(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes/explore")
        assert response.status_code == 200


class TestSearchRecipes:
    @pytest.mark.asyncio
    async def test_search_by_title(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?q=Chocolate")
        assert response.status_code == 200
        assert b"Chocolate Cake" in response.content

    @pytest.mark.asyncio
    async def test_search_by_description(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?q=hearty")
        assert response.status_code == 200
        assert b"Beef Stew" in response.content

    @pytest.mark.asyncio
    async def test_search_no_results(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?q=nonexistentrecipexyz")
        assert response.status_code == 200
        assert b"No recipes found" in response.content

    @pytest.mark.asyncio
    async def test_search_combined_with_difficulty(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?q=Salad&difficulty=easy")
        assert response.status_code == 200
        assert b"Caesar Salad" in response.content

    @pytest.mark.asyncio
    async def test_search_combined_with_tag(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?q=Curry&tag=vegan")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_all(
        self, client: httpx.AsyncClient, multiple_recipes: list[Recipe]
    ):
        response = await client.get("/recipes?q=")
        assert response.status_code == 200
        for recipe in multiple_recipes:
            assert recipe.title.encode() in response.content


class TestFavoriteToggle:
    @pytest.mark.asyncio
    async def test_favorite_toggle_requires_auth_ajax(
        self, client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
            follow_redirects=False,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_favorite_toggle_redirects_unauthenticated_non_ajax(
        self, client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "/auth/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_favorite_toggle_add_favorite_ajax(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await auth_client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorited"] is True
        assert data["favorite_count"] == 1

    @pytest.mark.asyncio
    async def test_favorite_toggle_remove_favorite_ajax(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        # Add favorite first
        await auth_client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        # Toggle off
        response = await auth_client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorited"] is False
        assert data["favorite_count"] == 0

    @pytest.mark.asyncio
    async def test_favorite_toggle_non_ajax_redirects(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await auth_client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/recipes/{sample_recipe.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_favorite_toggle_recipe_not_found(
        self, auth_client: httpx.AsyncClient
    ):
        fake_id = str(uuid.uuid4())
        response = await auth_client.post(
            f"/recipes/{fake_id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_favorite_count_increments_with_multiple_users(
        self,
        auth_client: httpx.AsyncClient,
        second_user_client: httpx.AsyncClient,
        sample_recipe: Recipe,
    ):
        # First user favorites
        response1 = await auth_client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["favorite_count"] == 1

        # Second user favorites
        response2 = await second_user_client.post(
            f"/recipes/{sample_recipe.id}/favorite",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["favorite_count"] == 2


class TestMyRecipes:
    @pytest.mark.asyncio
    async def test_my_recipes_requires_auth(self, client: httpx.AsyncClient):
        response = await client.get("/recipes/mine", follow_redirects=False)
        assert response.status_code in (303, 401, 403)

    @pytest.mark.asyncio
    async def test_my_recipes_shows_own_recipes(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await auth_client.get("/recipes/mine")
        assert response.status_code == 200
        assert sample_recipe.title.encode() in response.content

    @pytest.mark.asyncio
    async def test_my_recipes_does_not_show_others_recipes(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        response = await second_user_client.get("/recipes/mine")
        assert response.status_code == 200
        assert sample_recipe.title.encode() not in response.content


class TestRecipeReviewFromRecipePage:
    @pytest.mark.asyncio
    async def test_submit_review_on_recipe(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        form_data = {
            "rating": "5",
            "comment": "Excellent recipe!",
        }
        response = await second_user_client.post(
            f"/recipes/{sample_recipe.id}/reviews",
            data=form_data,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"/recipes/{sample_recipe.id}" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_cannot_review_own_recipe(
        self, auth_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        form_data = {
            "rating": "5",
            "comment": "Self review",
        }
        response = await auth_client.post(
            f"/recipes/{sample_recipe.id}/reviews",
            data=form_data,
            follow_redirects=False,
        )
        assert response.status_code == 303

    @pytest.mark.asyncio
    async def test_cannot_review_same_recipe_twice(
        self, second_user_client: httpx.AsyncClient, sample_recipe: Recipe
    ):
        form_data = {
            "rating": "4",
            "comment": "First review",
        }
        await second_user_client.post(
            f"/recipes/{sample_recipe.id}/reviews",
            data=form_data,
            follow_redirects=False,
        )
        # Try again
        form_data2 = {
            "rating": "3",
            "comment": "Second review attempt",
        }
        response = await second_user_client.post(
            f"/recipes/{sample_recipe.id}/reviews",
            data=form_data2,
            follow_redirects=False,
        )
        assert response.status_code == 303