from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


class IngredientSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    quantity: str
    unit: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ingredient name must not be empty")
        return v.strip()

    @field_validator("quantity")
    @classmethod
    def quantity_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ingredient quantity must not be empty")
        return v.strip()


class StepSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_number: int
    instruction: str

    @field_validator("step_number")
    @classmethod
    def step_number_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Step number must be a positive integer")
        return v

    @field_validator("instruction")
    @classmethod
    def instruction_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Step instruction must not be empty")
        return v.strip()


class RecipeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    cook_time_minutes: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None
    ingredients: list[IngredientSchema] = []
    steps: list[StepSchema] = []

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Recipe title must not be empty")
        return v.strip()

    @field_validator("cook_time_minutes", "prep_time_minutes", "servings")
    @classmethod
    def must_be_positive_if_set(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Value must be a non-negative integer")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"easy", "medium", "hard"}
            if v.lower() not in allowed:
                raise ValueError(f"Difficulty must be one of: {', '.join(allowed)}")
            return v.lower()
        return v


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cook_time_minutes: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None
    ingredients: Optional[list[IngredientSchema]] = None
    steps: Optional[list[StepSchema]] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Recipe title must not be empty")
        return v.strip() if v is not None else v

    @field_validator("cook_time_minutes", "prep_time_minutes", "servings")
    @classmethod
    def must_be_positive_if_set(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Value must be a non-negative integer")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"easy", "medium", "hard"}
            if v.lower() not in allowed:
                raise ValueError(f"Difficulty must be one of: {', '.join(allowed)}")
            return v.lower()
        return v


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    cook_time_minutes: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None
    ingredients: list[IngredientSchema] = []
    steps: list[StepSchema] = []
    author_id: str
    avg_rating: Optional[float] = None
    review_count: int = 0
    created_at: datetime
    updated_at: datetime


class RecipeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    cook_time_minutes: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: Optional[list[str]] = None
    author_id: str
    avg_rating: Optional[float] = None
    review_count: int = 0
    created_at: datetime
    updated_at: datetime