from dataclasses import dataclass

from google import genai
from .config import get_settings
from .schemas import UserInput, WorkoutPlan
from .gemini_generator import SYSTEM_PROMPT


@dataclass
class PlanUpdateRequest:
    user: UserInput
    original_plan: str
    feedback: str


def update_workout_plan(request_or_original_plan, feedback: str | None = None, user: UserInput | None = None) -> WorkoutPlan:
    if isinstance(request_or_original_plan, PlanUpdateRequest):
        original_plan = request_or_original_plan.original_plan
        user = request_or_original_plan.user
        feedback = request_or_original_plan.feedback
    elif isinstance(request_or_original_plan, str):
        original_plan = request_or_original_plan
        if feedback is None or user is None:
            raise TypeError("update_workout_plan requires feedback and user when given an original plan string")
    elif isinstance(request_or_original_plan, UserInput):
        user = request_or_original_plan
        if feedback is None or not isinstance(feedback, str):
            raise TypeError("update_workout_plan requires feedback when given a user payload")
        raise TypeError("The update request requires an original plan and feedback payload when called in the single-user form")
    else:
        raise TypeError("Unsupported update_workout_plan payload")

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to your .env file.")
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"""Revise the existing 7-day FitBuddy plan below based on the user's feedback.
User: {user.username}, age {user.age}, goal {user.goal}, intensity {user.intensity}
Feedback: {feedback}

Existing plan:
{original_plan}

Preserve sensible structure and safety. Apply the feedback where it is reasonable. If feedback asks for unsafe or inappropriate activity, replace it with a safer alternative. Keep exactly 7 days and return the same JSON schema."""
    response = client.models.generate_content(
        model=settings.gemini_workout_model,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": WorkoutPlan,
            "temperature": 0.6,
        },
    )
    if getattr(response, "parsed", None) is not None:
        return response.parsed
    return WorkoutPlan.model_validate_json(response.text)
