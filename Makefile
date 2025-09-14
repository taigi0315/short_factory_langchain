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
	@echo "  setup          : Creates a virtual environment and installs dependencies"
	@echo "  install        : Installs dependencies from requirements.txt"
	@echo "  clean          : Removes the virtual environment and other generated files"

# Setup target
setup: $(VENV)/bin/activate
	@echo "Virtual environment is set up."

$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created."
	. $(VENV)/bin/activate; pip install -r requirements.txt
	@echo "Dependencies installed."
	@touch $(VENV)/bin/activate

# Install target
install:
	. $(VENV)/bin/activate; pip install -r requirements.txt
	@echo "Dependencies installed."

# Clean target
clean:
	rm -rf $(VENV)
	rm -rf .ipynb_checkpoints
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleaned up the project."

.PHONY: all help setup install clean
