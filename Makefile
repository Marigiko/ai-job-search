# CareerOS — Unified Job Search Operating System
# Single command to rule them all.

.PHONY: help dev dev-backend dev-frontend test lint migrate-data setup setup-backend setup-frontend clean

# Default target -------------------------------------------------------------
help: ## Show this help
	@echo "CareerOS — available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
dev: ## Run backend + frontend together (background)
	@echo "Starting CareerOS (backend :8000, frontend :5173)..."
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Run FastAPI backend with auto-reload
	cd careeros-backend && python3 run.py

dev-frontend: ## Run Vite dev server
	cd careeros-frontend && npm run dev

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
test: test-backend ## Run all test suites

test-backend: ## Run backend pytest suite
	cd careeros-backend && python3 -m pytest tests/ -v

test-backend-cov: ## Run backend tests with coverage
	cd careeros-backend && python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------
lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Ruff check for backend
	cd careeros-backend && python3 -m ruff check app/ tests/

lint-backend-fix: ## Ruff check + auto-fix
	cd careeros-backend && python3 -m ruff check --fix app/ tests/

lint-frontend: ## Type-check frontend
	cd careeros-frontend && npm run typecheck

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
migrate: ## Run Alembic migrations (upgrade to head)
	cd careeros-backend && python3 -m alembic upgrade head

migrate-data: ## Migrate legacy JSON data (leads, templates, bounces) → SQLite
	cd careeros-backend && python3 -m app.seed.legacy_data

db-reset: ## Delete local SQLite database (fresh start)
	rm -f careeros.db test_careeros.db
	@echo "Database removed. Run 'make migrate' to recreate."

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
setup: setup-backend setup-frontend ## Full one-time setup

setup-backend: ## Create venv + install backend deps
	cd careeros-backend && python3 -m venv .venv && \
		. .venv/bin/activate && pip install -U pip && \
		pip install -e ".[dev]"
	@echo "Backend ready. Activate with: cd careeros-backend && source .venv/bin/activate"

setup-frontend: ## Install frontend dependencies
	cd careeros-frontend && npm install

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
clean: ## Remove build artefacts and caches
	rm -rf careeros-backend/.venv careeros-backend/.pytest_cache \
		careeros-backend/.ruff_cache careeros-backend/__pycache__ \
		careeros-backend/app/**/__pycache__ careeros-backend/tests/__pycache__ \
		careeros-frontend/dist careeros-frontend/node_modules/.vite \
		careeros.db test_careeros.db
	@echo "Cleaned."
