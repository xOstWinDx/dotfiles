.PHONY: install test clean help

help:
	@echo "Bootstrap - Modern Dotfiles Installer"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Install dependencies"
	@echo "  make test          Run tests"
	@echo "  make clean         Clean temporary files"
	@echo "  make doctor        Check system info"

install:
	python -m venv venv && \
	./venv/bin/pip install click

test:
	./venv/bin/python -m pytest

clean:
	rm -rf venv __pycache__ bootstrap/__pycache__ \
		bootstrap/*/__pycache__ *.egg-info .pytest_cache

doctor:
	./venv/bin/python -m bootstrap doctor

plan:
	./venv/bin/python -m bootstrap install --dry-run
