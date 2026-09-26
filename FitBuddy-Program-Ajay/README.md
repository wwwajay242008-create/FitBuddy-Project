# FitBuddy – AI Fitness Plan Generator

A complete FastAPI + Jinja2 + SQLAlchemy + SQLite application based on the supplied FitBuddy project documentation. It generates a structured 7-day wellness/workout plan, a nutrition/recovery tip, supports feedback-based regeneration, and includes an admin dashboard.

## Architecture

- **Frontend:** Jinja2 templates + responsive CSS/JS
- **Backend:** FastAPI
- **Persistence:** SQLAlchemy + SQLite
- **AI:** Google GenAI Python SDK (`google-genai`)
- **Validation:** Pydantic v2
- **Tests:** pytest + FastAPI TestClient

The original document names Gemini 1.5 Pro and Gemini Flash. Those model names are no longer the recommended production defaults. The implementation uses environment-configurable current model IDs, defaulting to `gemini-2.5-pro` for plan generation and `gemini-2.5-flash` for quick tips. Change them in `.env` if your Google AI account exposes a different model.

## Safety

This app is an informational wellness planner, not medical care. The AI prompt explicitly avoids unsafe exercise, extreme dieting, supplement/drug advice, and aggressive weight-loss instructions. For users under 18, it keeps recommendations age-appropriate and avoids calorie restriction or weight-loss coaching.

## Project tree

```text
fitbuddy/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── gemini_generator.py
│   ├── gemini_flash_generator.py
│   ├── updated_plan.py
│   ├── routes.py
│   └── main.py
├── static/
│   ├── styles.css
│   └── app.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   └── all_users.html
├── tests/
│   ├── conftest.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Quick start – Windows / VS Code

1. Install Python 3.11+.
2. Open this folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate
```

5. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Create `.env` from `.env.example` and put your Gemini API key in it:

```text
GEMINI_API_KEY=your_key_here
```

7. Start the server:

```powershell
uvicorn app.main:app --reload
```

8. Open:

- http://127.0.0.1:8000 — web app
- http://127.0.0.1:8000/docs — interactive API docs
- http://127.0.0.1:8000/health — health check
- http://127.0.0.1:8000/view-all-users — admin/demo dashboard

## Testing

With the virtual environment active:

```powershell
pytest -q
```

The test suite runs without calling Gemini by using a fake AI service.

## API endpoints

- `GET /` — homepage
- `POST /generate-workout` — generate and persist a new plan
- `POST /submit-feedback` — revise an existing plan
- `GET /view-all-users` — dashboard
- `GET /api/users` — JSON user list
- `GET /api/users/{user_id}` — JSON user + plan
- `DELETE /api/users/{user_id}` — delete user
- `GET /health` — service health

## Configuration

`.env.example` documents all supported settings, including model IDs, database URL, and an optional admin token.

For a real deployment, put the application behind HTTPS, use a proper authentication layer for the admin area, and replace SQLite with a managed relational database if traffic grows.
