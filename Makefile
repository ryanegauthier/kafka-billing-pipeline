.PHONY: help install install-dev test lint format clean build run-producer run-consumer run-analytics run-dashboard docker-up docker-down

help: ## Show this help message
	@echo "Kafka Billing Pipeline - Development Commands"
	@echo "=============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run tests with coverage
	pytest kafka_billing_pipeline/tests/ -v --cov=kafka_billing_pipeline --cov-report=html --cov-report=term-missing

lint: ## Run linting checks
	flake8 kafka_billing_pipeline/
	mypy kafka_billing_pipeline/

format: ## Format code with black
	black kafka_billing_pipeline/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

build: ## Build the package
	python -m build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

run-producer: ## Run the event producer
	python -m kafka_billing_pipeline.producer

run-consumer: ## Run the billing processor
	python -m kafka_billing_pipeline.billing_processor

run-analytics: ## Run the analytics dashboard
	python -m kafka_billing_pipeline.analytics

run-dashboard: ## Run the monitoring dashboard
	python -m kafka_billing_pipeline.monitoring

run-web-dashboard: ## Run the web dashboard
	python web_dashboard.py

start-pipeline: ## Start the complete pipeline (producer + consumer + analytics)
	python start_pipeline.py start

stop-pipeline: ## Stop all pipeline components
	python start_pipeline.py stop

pipeline-status: ## Show status of pipeline components
	python start_pipeline.py status

shutdown: ## Complete shutdown - stop pipeline and containers
	@echo "🛑 Complete shutdown of Kafka Billing Pipeline..."
	@echo "1. Stopping pipeline components..."
	$(MAKE) stop-pipeline
	@echo "2. Stopping Docker containers..."
	$(MAKE) docker-down
	@echo "3. Cleaning up..."
	$(MAKE) clean-pids
	@echo "✅ Complete shutdown finished!"

clean-pids: ## Clean up any leftover PID files
	@rm -f .producer.pid .consumer.pid .analytics.pid

test-connections: ## Test all connections (Kafka, PostgreSQL)
	python test_connections.py

check-status: ## Check status of all components
	@echo "=== Docker Containers ==="
	docker ps
	@echo ""
	@echo "=== Kafka Topics ==="
	docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
	@echo ""
	@echo "=== Database Connection ==="
	python -c "import psycopg2; conn = psycopg2.connect(host='localhost', database='billing', user='admin', password='password'); print('✅ Database connected'); conn.close()"

setup: ## Complete setup of the project
	@echo "Setting up Kafka Billing Pipeline..."
	@echo "1. Installing dependencies..."
	$(MAKE) install-dev
	@echo "2. Starting Docker containers..."
	$(MAKE) docker-up
	@echo "3. Waiting for services to be ready..."
	sleep 10
	@echo "4. Testing connections..."
	$(MAKE) test-connections
	@echo "✅ Setup complete! Run 'make start-pipeline' to start the system."

dev-setup: ## Development environment setup
	@echo "Setting up development environment..."
	@echo "1. Creating virtual environment..."
	python -m venv kafka-env
	@echo "2. Activating virtual environment..."
	@echo "   On Windows: kafka-env\\Scripts\\activate"
	@echo "   On Unix/MacOS: source kafka-env/bin/activate"
	@echo "3. Installing dependencies..."
	$(MAKE) install-dev
	@echo "4. Starting infrastructure..."
	$(MAKE) docker-up
	@echo "✅ Development environment ready!"

all: clean install-dev test lint format ## Run all checks (clean, install, test, lint, format)
	@echo "✅ All checks passed!" 