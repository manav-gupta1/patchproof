up:
	docker compose up -d postgres redis

down:
	docker compose down

ps:
	docker compose ps

test:
	python -m pytest -q tests/test_github_integration.py tests/test_llm_clients.py tests/test_semgrep_matching.py tests/test_vertical_slice.py

semgrep-check:
	docker run --rm semgrep/semgrep:latest semgrep --version

stack-check:
	python scripts/dev-stack-check.py

migrate:
	alembic upgrade head
