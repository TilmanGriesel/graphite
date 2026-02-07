.PHONY: all rebuild theme clean format format-python format-yaml lint-python docker-build docker-run docker-clean test-patcher validate-yaml dev-build dev-deploy dev-deploy-full ha-start ha-stop ha-restart ha-logs ha-clean

all: format theme validate-yaml

theme: clean
	python3 tools/theme_assembler.py

clean:
	@echo "Cleaning theme directory..."
	rm -rf theme/*
	@echo "Theme directory cleaned."

dev:
	chmod +x scripts/ha-rebuild-local.sh
	./scripts/ha-rebuild-local.sh

dev-build: clean
	@echo "Building themes for development..."
	python3 tools/theme_assembler.py --dev
	@echo "Development themes built."

dev-deploy:
	@echo "Deploying to remote development environment..."
	./scripts/deploy-dev.sh
	@echo "Remote dev deployment complete."

dev-deploy-full: theme dev-deploy
	@echo "Building and deploying to remote development environment..."
	@echo "Full dev deployment complete."

format: format-yaml format-python

format-yaml:
	@echo "Formatting YAML files..."
	pre-commit run --all-files
	@echo "YAML formatting complete."

format-python:
	@echo "Formatting Python files..."
	@command -v black >/dev/null 2>&1 || { echo "Installing black..."; pip install black; }
	black extras/theme-patcher/graphite-theme-patcher.py extras/theme-patcher/test_theme_patcher.py
	@echo "Python formatting complete."

lint-python:
	@echo "Linting Python files..."
	@command -v flake8 >/dev/null 2>&1 || { echo "Installing flake8..."; pip install flake8; }
	flake8 extras/theme-patcher/graphite-theme-patcher.py extras/theme-patcher/test_theme_patcher.py --max-line-length=120 --ignore=E501,W503,E203 --show-source --statistics
	@echo "Python linting complete."

test-patcher:
	@echo "Running test suite..."
	python3 extras/theme-patcher/test_theme_patcher.py
	@echo "Theme-Patcher tests complete."

validate-yaml:
	@echo "Validating generated YAML files..."
	@yamllint -d '{extends: relaxed, rules: {line-length: {max: 200}, trailing-spaces: disable, indentation: disable, empty-lines: {max-end: 2}}}' themes/*.yaml
	@echo "✓ All YAML files are valid."

docs-dev:
	@echo "Starting vitepress..."
	yarn add -D vitepress
	yarn docs:dev

docker-build:
	@echo "Building Docker image..."
	docker build -t theme-assembler .

docker-run: docker-build
	@echo "Running theme assembler in Docker..."
	docker run --rm -v $(CURDIR):/app theme-assembler

docker-clean:
	@echo "Removing Docker image..."
	docker rmi theme-assembler 2>/dev/null || true

ha-start: theme
	@echo "Starting Home Assistant test environment..."
	docker compose -f docker-compose.ha.yml up -d
	@echo "Home Assistant is starting at http://localhost:8123"

ha-stop:
	@echo "Stopping Home Assistant test environment..."
	docker compose -f docker-compose.ha.yml down
	@echo "Home Assistant stopped."

ha-restart: theme
	@echo "Restarting Home Assistant test environment..."
	docker compose -f docker-compose.ha.yml restart
	@echo "Home Assistant restarted."

ha-logs:
	docker compose -f docker-compose.ha.yml logs -f

ha-clean: ha-stop
	@echo "Removing Home Assistant runtime data..."
	find .ha/config -mindepth 1 ! -name 'configuration.yaml' -exec rm -rf {} + 2>/dev/null || true
	@echo "Home Assistant runtime data cleaned."

help:
	@echo "Available targets:"
	@echo "  all          - Run theme assembly (default)"
	@echo "  theme        - Run the theme assembler"
	@echo "  clean        - Remove generated files"
	@echo "  dev          - Run local HA rebuild script"
	@echo "  dev-deploy   - Deploy themes and patcher to remote HA (/Volumes/config)"
	@echo "  dev-deploy-full - Build themes and deploy to remote HA"
	@echo "  dev-build    - Build themes with dev suffix"
	@echo "  docs-dev     - Run local VitePress"
	@echo "  format       - Format both YAML and Python files"
	@echo "  format-yaml  - Format YAML files in src and theme directories"
	@echo "  format-python - Format Python files with black"
	@echo "  lint-python  - Lint Python files with flake8"
	@echo "  test-patcher - Run test suite"
	@echo "  validate-yaml - Validate all generated YAML theme files"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run the theme assembler in Docker"
	@echo "  docker-clean - Remove the Docker image"
	@echo "  ha-start     - Build themes and start HA test environment"
	@echo "  ha-stop      - Stop HA test environment"
	@echo "  ha-restart   - Rebuild themes and restart HA"
	@echo "  ha-logs      - Tail HA container logs"
	@echo "  ha-clean     - Stop HA and remove runtime data"
	@echo "  help         - Show this help message"
