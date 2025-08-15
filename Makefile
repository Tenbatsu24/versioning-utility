#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME := version-util
PYTHON_INTERPRETER := python3

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## This target checks the current version of the project using version-manager.
.PHONY: check
check:
	@version-manager check

## This target bumps the version of the project using version-manager.
.PHONY: bump
bump:
	@version-manager bump

## This target generates a changelog based on the version history.
.PHONY: changelog
changelog:
	@version-manager changelog

## This target generates a graph of the version history.
.PHONY: graph
graph:
	@version-manager graph

## Example: CI job on main that bumps, changelog, and graph non-interactively
.PHONY: release
release:
	@version-manager bump -y
	version=$$(grep -E '^version\s*=' pyproject.toml | head -1 | cut -d '"' -f2); \
	if git rev-parse "v$$version" >/dev/null 2>&1; then \
		echo "Tag v$$version already exists! Aborting."; \
		exit 1; \
	fi; \
	git tag "v$$version" && git push --tags


## Install Python Dependencies
.PHONY: requirements
requirements:
	@echo "Installing Python dependencies..."
	@if [ ! -d "venv" ]; then \
  		$(PYTHON_INTERPRETER) -m venv venv; \
	else \
		echo "Virtual environment already exists."; \
	fi
	@echo "Upgrading pip and installing requirements..."
	venv/bin/python3 -m pip install -U pip
	venv/bin/python3 -m pip install -r requirements.txt


## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete


## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 versioning_tool
	black --check --config pyproject.toml versioning_tool


## Format source code with black
.PHONY: format
format:
	black --config pyproject.toml versioning_tool


.PHONY: dependencies
dependencies:
	@echo "Installing dependencies for the container..."
	$(PYTHON_INTERPRETER) -m pip install -U pip
	apt install -y python3-venv


## Set up python interpreter environment
.PHONY: create_environment
create_environment:
	@if command -v $(PYTHON_INTERPRETER) > /dev/null; then \
		if [ ! -d "venv" ]; then \
			$(PYTHON_INTERPRETER) -m venv venv; \
			echo "Virtual environment created."; \
		else \
			echo "Virtual environment already exists."; \
		fi; \
		$(MAKE) requirements; \
	else \
		echo "$(PYTHON_INTERPRETER) is not installed. Please install it first."; \
	fi


## Activate python environment
.PHONY: activate_environment
activate_environment:
	@if [ -d "venv" ]; then \
		echo "Run 'source venv/bin/activate' to activate the virtual environment."; \
	else \
		echo "Virtual environment does not exist. Please run 'make create_environment' first."; \
	fi

# This target sets up pre-commit hooks for the project.
# It checks if the current directory is a Git repository and installs the hooks.
# If the repository is not initialized, it will skip the setup.
.PHONY: setup_hooks
setup_hooks:
	@if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then \
		echo "Setting up pre-commit hooks..."; \
		venv/bin/pre-commit install; \
		venv/bin/pre-commit autoupdate --repo https://github.com/pre-commit/pre-commit-hooks; \
		venv/bin/pre-commit install --hook-type pre-push; \
		venv/bin/pre-commit install --hook-type pre-commit; \
		venv/bin/pre-commit install --install-hooks; \
		echo "Pre-commit hooks set up successfully."; \
	else \
		echo "Not inside a Git repository. Skipping pre-commit setup."; \
	fi


## This target creates the virtual environment, activates it, installs requirements, and sets up pre-commit hooks.
.PHONY: env
env: create_environment activate_environment setup_hooks

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
