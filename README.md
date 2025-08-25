# BizDetails AI

This repository contains a minimal skeleton for the **BizDetails AI** platform.

## Backend

A basic [FastAPI](https://fastapi.tiangolo.com/) app with placeholder endpoints lives in `backend/app/main.py`. The endpoints include authentication, file upload, data processing, results retrieval, dashboard stats, and a chat interface.

Each user record stores the user's full name, role (e.g., Sales, Marketing, Data Analyst), enrichment count, last login timestamp, and account status.

To install dependencies and run the API locally:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

The application expects a `.env` file in the working directory containing
configuration values such as:

```
DEEPSEEK_API_KEY=your_api_key_here
```

If the file lives elsewhere, pass its path to `load_dotenv()` when starting
the app.

## Frontend

Frontend implementation is not yet provided. A future iteration would use React and Tailwind CSS to implement the upload flow, results view, dashboard, and chat panel described in the project plan.

## Tests

No automated tests are included. Run `pytest` to execute an empty test suite.
