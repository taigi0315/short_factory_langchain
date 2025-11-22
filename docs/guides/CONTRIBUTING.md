# Contributing to ShortFactoryLangChain

## Development Workflow

We follow a strict ticket-based development workflow to ensure quality and traceability.

### 1. Ticket System
- All work must start with a ticket in `tickets/todo/`.
- Ticket format: `TICKET-[ID]_[description].md`.
- Move ticket to `tickets/in_progress/` (create if needed) when starting.
- Move to `tickets/done/` when completed.

### 2. Branching Strategy
- **Main Branch**: `main` (Protected, production-ready code).
- **Feature Branches**: Create a new branch for each ticket.
    - Format: `feature/[ticket-id]-[short-description]` or `fix/[ticket-id]-[short-description]`.
    - Example: `feature/001-story-finder-agent`.
- **No direct commits to main**.

### 3. Code Quality
- **Comments**: Write clear docstrings for all modules, classes, and functions.
- **Tests**: Every feature must have accompanying tests in `tests/`.
- **Mocking**: Use mocks for external APIs (LLMs, Video generation) to save costs during testing.

### 4. Architecture
- **Backend**: FastAPI (Python) for agent orchestration.
- **Frontend**: Next.js (React) for the User Interface.
- **Infrastructure**: Dockerized services deployable to Google Cloud Run.

### 5. LangChain Usage
- Use `LangGraph` for complex agent workflows.
- Maintain modular agents in `src/agents/`.
