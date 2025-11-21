# TICKET-001: Setup FastAPI Backend

## Description
Initialize the FastAPI application to serve the LangChain agents.

## Tasks
- [ ] Create `src/api/` directory structure.
- [ ] Create `src/api/main.py` entrypoint.
- [ ] Create `src/api/schemas/` for Pydantic models.
- [ ] Create `src/api/routes/` for endpoints.
- [ ] Implement `/health` endpoint.
- [ ] Add `fastapi` and `uvicorn` to `requirements.txt`.

## Acceptance Criteria
- `uvicorn src.api.main:app --reload` starts the server.
- `/health` returns `{"status": "ok"}`.
