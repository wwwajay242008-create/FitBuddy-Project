from google import genai
from pydantic import ValidationError
from .config import get_settings
from .schemas import UserInput, WorkoutPlan


SYSTEM_PROMPT = """You are FitBuddy, a conservative wellness-planning assistant. Generate safe, realistic, age-appropriate fitness guidance. Do not diagnose medical conditions. Do not prescribe drugs, supplements, extreme diets, fasting, dehydration, dangerous stunts, or maximal/unsafe training. For anyone under 18, do not provide calorie restriction or weight-loss coaching; focus on healthy movement, enjoyment, recovery, sleep, hydration, and general wellness. Encourage a parent/guardian or qualified professional when appropriate. Always include a safety note."""


def _client():
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to your .env file.")
    return genai.Client(api_key=settings.gemini_api_key)


def generate_workout_gemini(user: UserInput) -> WorkoutPlan:
    client = _client()
    settings = get_settings()
    prompt = f"""Create a personalized 7-day wellness/workout plan for:
Name: {user.username}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Preferred intensity: {user.intensity}

Return exactly 7 days. Each day needs a focus, warm-up, 2-5 sensible exercises, rest guidance, and cooldown/recovery guidance. Use bodyweight or common gym exercises, with alternatives where useful. Keep sessions practical and avoid unsafe volume. The user's weight is context only; do not prescribe a target weight or calorie deficit."""
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
    try:
        return WorkoutPlan.model_validate_json(response.text)
    except ValidationError as exc:
        raise RuntimeError(f"Gemini returned an invalid workout plan: {exc}") from exc
