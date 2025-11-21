# Makefile for the AI-Powered Video Creation Pipeline project

# Define the Python interpreter
PYTHON = python3

# Define the virtual environment directory
VENV = venv

# Default target
all: help

# Help target to display available commands
help:
	@echo "Available commands:"
	@echo "  setup          : Sets up both backend (venv) and frontend (npm)"
	@echo "  run-backend    : Runs the FastAPI backend server"
	@echo "  run-frontend   : Runs the Next.js frontend server"
	@echo "  test           : Runs Python unit tests"
	@echo "  clean          : Removes venv, node_modules, and cache files"

# Setup target
setup: setup-backend setup-frontend
	@echo "Full stack environment set up."

setup-backend: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate; pip install -r requirements.txt
	@touch $(VENV)/bin/activate

setup-frontend:
	cd frontend && npm install

# Run targets
run-backend:
	. $(VENV)/bin/activate; PYTHONPATH=. python src/api/main.py

run-frontend:
	cd frontend && npm run dev

# Test targets
test:
	. $(VENV)/bin/activate; PYTHONPATH=. python -m unittest discover tests

test-integration:
	. $(VENV)/bin/activate; PYTHONPATH=. pytest -s tests/test_integration.py

# Clean target
clean:
	rm -rf $(VENV)
	rm -rf frontend/node_modules
	rm -rf frontend/.next
	rm -rf .ipynb_checkpoints
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleaned up the project."

.PHONY: all help setup setup-backend setup-frontend run-backend run-frontend test clean
