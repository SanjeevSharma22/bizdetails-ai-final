# BizDetails AI

This repository contains a minimal skeleton for the **BizDetails AI** platform.

## Backend

A basic [FastAPI](https://fastapi.tiangolo.com/) app with placeholder endpoints lives in `backend/app/main.py`. The endpoints include authentication, a secure superadmin CSV upload for maintaining the `company_updated` table, file upload, data processing, results retrieval, dashboard stats, and a chat interface.

To install dependencies and run the API locally:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

## Frontend

The frontend is built with React and Vite under `frontend/`. It supports user authentication and, when signed in as a user with the `superadmin` role, provides a secure page to upload a CSV that populates the `company_updated` table.

To run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

## Tests

No automated tests are included. Run `pytest` to execute an empty test suite.
