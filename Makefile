.PHONY: all rebuild theme clean format

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
	pre-commit install
	pre-commit run --all-files
	@echo "YAML formatting complete."

help:
	@echo "Available targets:"
	@echo "  all    - Run theme assembly (default)"
	@echo "  theme  - Run the theme assembler"
	@echo "  clean  - Remove generated files"
	@echo "  dev    - Run rebuild dev script"
	@echo "  format - Format YAML files in src and theme directories"
	@echo "  help   - Show this help message"
