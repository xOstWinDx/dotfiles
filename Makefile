.PHONY: help venv install test clean doctor plan run

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Bootstrap - Modern Dotfiles Installer"
	@echo ""
	@echo "Usage:"
	@echo "  make venv          Create virtual environment"
	@echo "  make install       Install project and dependencies"
	@echo "  make test          Run tests"
	@echo "  make doctor        Check system info"
	@echo "  make plan          Show dry-run installation plan"
	@echo "  make clean         Clean temporary files"

venv:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install: venv
	$(PIP) install -e .
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi

test: install
	$(PYTHON) -m pytest

doctor: install
	$(PYTHON) -m bootstrap doctor

plan: install
	$(PYTHON) -m bootstrap install --dry-run

run: install
	$(PYTHON) -m bootstrap install

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +