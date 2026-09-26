import json
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from .config import get_settings
from .database import get_db
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .models import Plan, User
from .schemas import FeedbackRequest, UserInput
from .updated_plan import PlanUpdateRequest, update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def plan_to_text(plan) -> str:
    return json.dumps(plan.model_dump(), indent=2, ensure_ascii=False)


def parse_plan(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"title": "Workout Plan", "safety_note": "See plan text below.", "days": []}


def render_result(request: Request, user: User, plan: Plan, message: str | None = None):
    current = plan.updated_plan or plan.original_plan
    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "user": user,
            "plan": plan,
            "workout": parse_plan(current),
            "nutrition": parse_plan(plan.nutrition_tip) if plan.nutrition_tip.startswith("{") else {"tip": plan.nutrition_tip, "recovery_note": ""},
            "message": message,
        },
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        data = UserInput(username=username, user_id=user_id, age=age, weight=weight, goal=goal, intensity=intensity)
        user = db.scalar(select(User).where(User.user_id == data.user_id))
        if user is None:
            user = User(**data.model_dump())
            db.add(user)
            db.flush()
        else:
            for key, value in data.model_dump().items():
                setattr(user, key, value)
        workout = generate_workout_gemini(data)
        nutrition = generate_nutrition_tip_with_flash(data)
        plan = Plan(user_id=user.id, original_plan=plan_to_text(workout), nutrition_tip=nutrition.model_dump_json())
        db.add(plan)
        db.commit()
        db.refresh(user)
        db.refresh(plan)
        return render_result(request, user, plan)
    except Exception as exc:
        db.rollback()
        return templates.TemplateResponse(request=request, name="index.html", context={"error": str(exc)}, status_code=500)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.user_id == user_id).options(selectinload(User.plans)))
    if user is None or not user.plans:
        raise HTTPException(status_code=404, detail="User or workout plan not found")
    plan = sorted(user.plans, key=lambda p: p.created_at)[-1]
    try:
        data = UserInput(username=user.username, user_id=user.user_id, age=user.age, weight=user.weight, goal=user.goal, intensity=user.intensity)
        result = update_workout_plan(PlanUpdateRequest(user=data, original_plan=plan.original_plan, feedback=feedback))
        plan.updated_plan = plan_to_text(result)
        plan.feedback = FeedbackRequest(user_id=user_id, feedback=feedback).feedback
        db.commit()
        db.refresh(plan)
        return render_result(request, user, plan, "Your plan was updated using your feedback.")
    except Exception as exc:
        db.rollback()
        return render_result(request, user, plan, f"Could not update the plan: {exc}")


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    users = db.scalars(select(User).options(selectinload(User.plans)).order_by(User.created_at.desc())).all()
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": users})


@router.get("/api/users")
def api_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).options(selectinload(User.plans)).order_by(User.created_at.desc())).all()
    return [{"user_id": u.user_id, "username": u.username, "age": u.age, "weight": u.weight, "goal": u.goal, "intensity": u.intensity, "plans": len(u.plans)} for u in users]


@router.get("/api/users/{user_id}")
def api_user(user_id: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.user_id == user_id).options(selectinload(User.plans)))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.user_id, "username": user.username, "age": user.age, "weight": user.weight, "goal": user.goal, "intensity": user.intensity, "plans": [{"id": p.id, "original_plan": parse_plan(p.original_plan), "updated_plan": parse_plan(p.updated_plan) if p.updated_plan else None, "feedback": p.feedback, "nutrition_tip": parse_plan(p.nutrition_tip)} for p in user.plans]}


@router.delete("/api/users/{user_id}")
def delete_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    token = request.headers.get("x-admin-token")
    if settings.admin_token and token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Admin token required")
    user = db.scalar(select(User).where(User.user_id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return JSONResponse({"ok": True, "deleted": user_id})


@router.get("/health")
def health():
    return {"status": "ok", "service": "fitbuddy"}
