# KLIQ Growth Engine — Makefile
PROJECT_ID  ?= rcwl-development
REGION      ?= europe-west1
REPO        ?= kliq-growth-engine
REGISTRY    ?= $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)
TAG         ?= latest

# --- Local Development ---

.PHONY: dev
dev: ## Run FastAPI with hot-reload
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: dev-all
dev-all: ## Run all services via docker compose
	docker compose up --build

.PHONY: worker
worker: ## Run Celery worker
	celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

.PHONY: beat
beat: ## Run Celery Beat scheduler
	celery -A app.workers.celery_app beat --loglevel=info

.PHONY: dashboard
dashboard: ## Run Streamlit dashboard
	streamlit run dashboard/app.py --server.port 8501

# --- Code Quality ---

.PHONY: lint
lint: ## Run linter checks
	ruff check .
	ruff format --check .

.PHONY: lint-fix
lint-fix: ## Auto-fix lint issues
	ruff check --fix .
	ruff format .

.PHONY: test
test: ## Run test suite
	pytest -v --tb=short

# --- Database ---

.PHONY: migrate
migrate: ## Run database migrations
	alembic upgrade head

# --- Docker Build ---

.PHONY: build-api
build-api: ## Build API image (no Playwright)
	docker build --build-arg INSTALL_PLAYWRIGHT=false -t $(REGISTRY)/api:$(TAG) .

.PHONY: build-worker
build-worker: ## Build Worker image (with Playwright)
	docker build --build-arg INSTALL_PLAYWRIGHT=true -t $(REGISTRY)/worker:$(TAG) .

.PHONY: build
build: build-api build-worker ## Build both images

# --- Docker Push ---

.PHONY: push
push: ## Push both images to Artifact Registry
	docker push $(REGISTRY)/api:$(TAG)
	docker push $(REGISTRY)/worker:$(TAG)

# --- Cloud Run Deploy ---

.PHONY: deploy-api
deploy-api: ## Deploy API to Cloud Run
	gcloud run deploy kliq-growth-api \
		--image $(REGISTRY)/api:$(TAG) \
		--region $(REGION) \
		--platform managed \
		--min-instances=0 --max-instances=5 \
		--memory=512Mi --cpu=1 \
		--port=8000 \
		--allow-unauthenticated

.PHONY: deploy-worker
deploy-worker: ## Deploy Worker to Cloud Run
	gcloud run deploy kliq-growth-worker \
		--image $(REGISTRY)/worker:$(TAG) \
		--region $(REGION) \
		--platform managed \
		--min-instances=1 --max-instances=3 \
		--memory=2Gi --cpu=2 \
		--no-cpu-throttling \
		--command="celery" \
		--args="-A,app.workers.celery_app,worker,--loglevel=info,--concurrency=4"

.PHONY: deploy-dashboard
deploy-dashboard: ## Deploy Dashboard to Cloud Run
	gcloud run deploy kliq-growth-dashboard \
		--image $(REGISTRY)/api:$(TAG) \
		--region $(REGION) \
		--platform managed \
		--min-instances=0 --max-instances=2 \
		--memory=512Mi --cpu=1 \
		--port=8501 \
		--command="streamlit" \
		--args="run,dashboard/app.py,--server.port=8501,--server.address=0.0.0.0"

.PHONY: deploy
deploy: deploy-api deploy-worker deploy-dashboard ## Deploy all services

# --- Logs ---

.PHONY: logs-api
logs-api: ## Tail API logs
	gcloud run services logs tail kliq-growth-api --region $(REGION)

.PHONY: logs-worker
logs-worker: ## Tail Worker logs
	gcloud run services logs tail kliq-growth-worker --region $(REGION)

# --- Help ---

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
