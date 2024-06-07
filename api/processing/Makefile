ENV := .venv
PIP := ${ENV}/bin/pip3
PY := ${ENV}/bin/python
PY_TEST := $(ENV)/bin/pytest
FLAKE8 := $(ENV)/bin/flake8
BLACK := $(ENV)/bin/black
ISORT := $(ENV)/bin/isort
MYPY := $(ENV)/bin/mypy
PRECOMMIT_HOOK := $(ENV)/bin/pre-commit
DIST_DIR := ./dist


.PHONY: clean lint setup test build check-whl install build-and-install mypy-check

clean: clean-py clean-env clean-dist
	@echo "Cleaning finished :)"

clean-py:
	@find ./ -name "*.pyc"  | xargs rm -f
	@find ./ -name "__pycache__" | xargs rm -rf
	@find ./ -name "*.egg-info" | xargs rm -rf

clean-env:
	rm -rf ./$(ENV)

clean-dist:
	rm -rf ./dist

test-coverage:
	@${PY_TEST} --cov deep_mmnl --cov-config deep_mmnl/.coveragerc --benchmark-skip --without-integration --cov-report term-missing

init-virtualenv:
	test -d $(ENV) || python3.12 -m venv $(ENV)
	@${PIP} install -U pip

dev-setup: init-virtualenv
	@${PIP} install -e .[dev]
	${PIP} freeze

notebook-setup:
	${PIP} install jupyterlab
	@${PY} -m ipykernel install --user --name=labellm

setup: clean dev-setup
	@${PRECOMMIT_HOOK} install

build:
	@${PIP} install build==1.0.3
	@${PY} -m build

check-whl:
	@if [ $(shell find $(DIST_DIR) -name "*.whl" | wc -l) -ne 1 ]; then \
		echo "Error: There should be exactly one .whl file in $(DIST_DIR)"; \
		exit 1; \
	fi

install: check-whl
	@WHL_FILE=$$(ls $(DIST_DIR)/*.whl | head -n 1); \
	${PIP} install "$${WHL_FILE}[dev]"

build-and-install: clean init-virtualenv build install

test:
	@${PY_TEST} --benchmark-skip --without-integration

test-integration:
	@${PY_TEST} integration

benchmark:
	@${PY_TEST} --benchmark-only

lint: flake8-check black-check issort-check mypy-check

flake8-check:
	@echo "=====FLAKE8====="
	@${FLAKE8} --ignore W503,E203

black-check:
	@echo "=====BLACK====="
	@${BLACK}

issort-check:
	@echo "=====ISORT====="
	@${ISORT} --profile black

mypy-check:
	@echo "=====MYPY====="
	@${MYPY} --ignore-missing-imports --install-types --non-interactive
