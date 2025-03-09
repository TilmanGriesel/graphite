.PHONY: all rebuild theme clean format docker-build docker-run docker-clean

all: format theme

theme: clean
	python3 tools/theme_assembler.py

clean:
	@echo "Cleaning theme directory..."
	rm -rf theme/*
	@echo "Theme directory cleaned."

dev:
	chmod +x tools/rebuild_dev.sh
	./tools/rebuild_dev.sh

format:
	@echo "Formatting YAML files..."
	pre-commit run --all-files
	@echo "YAML formatting complete."

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
	@echo "  format       - Format YAML files in src and theme directories"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run the theme assembler in Docker"
	@echo "  docker-clean - Remove the Docker image"
	@echo "  help         - Show this help message"
