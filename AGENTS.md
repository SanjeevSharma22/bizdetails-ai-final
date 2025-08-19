# Agent Guidelines

## Repository Overview
- This project is a skeleton for the **BizDetails AI** platform.
- The backend is a FastAPI application with endpoints for authentication, file upload, data processing, results retrieval, dashboard stats, and a chat interface.
- Frontend implementation is not yet provided.

## Development Setup
1. Use Python 3.10+.
2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run the API locally if needed:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

## Testing
- Run all tests with `pytest` before committing any changes.

## Coding Standards
- Follow PEP8 style guidelines and include type hints where practical.
- Use 4 spaces for indentation.
- Maintain consistency with existing FastAPI patterns and SQLAlchemy models.

## File Structure
- `backend/` – FastAPI app and database models.
- `frontend/` – placeholder for future React/Tailwind implementation.
- `tests/` – pytest suite exercising backend behavior.

## Contribution Workflow
1. Create or update code within appropriate directories.
2. Run tests and ensure they pass.
3. Commit changes to the main branch with clear messages.

