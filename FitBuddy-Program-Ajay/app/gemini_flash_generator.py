from google import genai
from .config import get_settings
from .schemas import NutritionTip, UserInput


SYSTEM_PROMPT = """You provide concise, evidence-aware wellness and recovery tips. Never recommend drugs, unsafe supplements, starvation, dehydration, extreme dieting, or dangerous practices. For users under 18, avoid calorie restriction and weight-loss coaching. Keep advice practical and age-appropriate."""


def generate_nutrition_tip_with_flash(user: UserInput) -> NutritionTip:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to your .env file.")
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"Give one concise nutrition/recovery tip aligned with the goal '{user.goal}' for a {user.age}-year-old. Mention ordinary foods, hydration, sleep, or recovery where relevant. Do not give calorie targets. Return JSON with tip and recovery_note."
    response = client.models.generate_content(
        model=settings.gemini_tip_model,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": NutritionTip,
            "temperature": 0.4,
        },
    )
    if getattr(response, "parsed", None) is not None:
        return response.parsed
    return NutritionTip.model_validate_json(response.text)
