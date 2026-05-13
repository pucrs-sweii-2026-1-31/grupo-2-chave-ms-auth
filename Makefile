.PHONY: setup test clean

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

setup-tests:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt pytest

test:
	export PYTHONPATH=$$(PYTHONPATH):. && $(PYTEST) tests/unit/test_auth_service.py

clean-tests:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

rebuild-service:
	make -C ../chave-infra down
	docker images -q 'chave-infra-chave-ms-auth:latest' | xargs -r docker rmi
	make -C ../chave-infra up
