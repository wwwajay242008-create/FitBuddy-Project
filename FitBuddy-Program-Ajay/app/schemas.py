from typing import Literal
from pydantic import BaseModel, Field, field_validator


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    user_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=10, le=100)
    weight: float = Field(gt=20, le=400)
    goal: str = Field(min_length=2, max_length=80)
    intensity: Literal["low", "medium", "high"]

    @field_validator("username", "goal")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=80)
    feedback: str = Field(min_length=3, max_length=2000)


class Exercise(BaseModel):
    name: str
    sets_reps: str
    rest: str
    notes: str = ""


class DayPlan(BaseModel):
    day: str
    focus: str
    warmup: str
    exercises: list[Exercise]
    cooldown: str


class WorkoutPlan(BaseModel):
    title: str
    safety_note: str
    days: list[DayPlan] = Field(min_length=7, max_length=7)


class NutritionTip(BaseModel):
    tip: str
    recovery_note: str
