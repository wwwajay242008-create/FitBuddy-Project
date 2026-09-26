from app import routes
from app.schemas import NutritionTip, WorkoutPlan, DayPlan, Exercise


def fake_workout(user):
    return WorkoutPlan(title="Test Plan", safety_note="Move comfortably and stop if pain occurs.", days=[
        DayPlan(day=f"Day {i}", focus="General wellness", warmup="5 minutes easy movement", exercises=[Exercise(name="Bodyweight squat", sets_reps="2 x 8", rest="60 sec")], cooldown="Easy walking and gentle mobility") for i in range(1, 8)
    ])


def fake_tip(user):
    return NutritionTip(tip="Eat regular balanced meals and drink water.", recovery_note="Prioritize sleep and recovery.")


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_generate_and_fetch(client, monkeypatch):
    monkeypatch.setattr(routes, "generate_workout_gemini", fake_workout)
    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", fake_tip)
    response = client.post("/generate-workout", data={"username":"Alex","user_id":"alex1","age":"25","weight":"70","goal":"general wellness","intensity":"medium"})
    assert response.status_code == 200
    assert "Test Plan" in response.text
    api = client.get("/api/users/alex1")
    assert api.status_code == 200
    assert api.json()["user_id"] == "alex1"


def test_feedback(monkeypatch, client):
    monkeypatch.setattr(routes, "generate_workout_gemini", fake_workout)
    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", fake_tip)
    client.post("/generate-workout", data={"username":"Alex","user_id":"alex2","age":"25","weight":"70","goal":"general wellness","intensity":"medium"})
    monkeypatch.setattr(routes, "update_workout_plan", fake_workout)
    response = client.post("/submit-feedback", data={"user_id":"alex2","feedback":"Please add more mobility work."})
    assert response.status_code == 200
    assert "updated" in response.text.lower()
