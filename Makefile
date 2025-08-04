.PHONY: all rebuild theme clean format format-python format-yaml lint-python docker-build docker-run docker-clean test-patcher validate-yaml

all: format theme validate-yaml

theme: clean
	python3 tools/theme_assembler.py

clean:
	@echo "Cleaning theme directory..."
	rm -rf theme/*
	@echo "Theme directory cleaned."

dev:
	chmod +x tools/rebuild_dev.sh
	./tools/rebuild_dev.sh

dev-sync: theme
	cp themes/*.yaml /Volumes/config/themes/graphite/

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
	@echo "Running Theme-Patcher v2.0.0 test suite..."
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

help:
	@echo "Available targets:"
	@echo "  all          - Run theme assembly (default)"
	@echo "  theme        - Run the theme assembler"
	@echo "  clean        - Remove generated files"
	@echo "  dev          - Run rebuild dev script"
	@echo "  docs-dev     - Run local VitePress"
	@echo "  format       - Format both YAML and Python files"
	@echo "  format-yaml  - Format YAML files in src and theme directories"
	@echo "  format-python - Format Python files with black"
	@echo "  lint-python  - Lint Python files with flake8"
	@echo "  test-patcher - Run Theme-Patcher v2.0.0 test suite"
	@echo "  validate-yaml - Validate all generated YAML theme files"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run the theme assembler in Docker"
	@echo "  docker-clean - Remove the Docker image"
	@echo "  help         - Show this help message"
