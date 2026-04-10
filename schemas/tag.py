import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class TagCreate(TagBase):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Tag name cannot be empty or whitespace")
        return stripped


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tag name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Tag name cannot be empty or whitespace")
            return stripped
        return v


class TagResponse(TagBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)