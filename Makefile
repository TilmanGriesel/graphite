.PHONY: all rebuild theme clean

all: theme

theme:
	python3 tools/theme_assembler.py

clean:
	@echo "Cleaning theme directory..."
	rm -rf theme/*
	@echo "Theme directory cleaned."

dev:
	chmod +x tools/rebuild_dev.sh
	./tools/rebuild_dev.sh

help:
	@echo "Available targets:"
	@echo "  all    - Run theme assembly (default)"
	@echo "  theme  - Run the theme assembler"
	@echo "  clean  - Remove generated files"
	@echo "  dev    - Run rebuild dev script"
	@echo "  help   - Show this help message"
