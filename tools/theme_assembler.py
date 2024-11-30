#!/usr/bin/env python3

import sys
import logging
import argparse
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Generator, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class YAMLValidationError(Exception):
    """Custom exception for YAML validation errors."""

    pass


class ThemeData:
    def __init__(
        self,
        theme_name: str,
        tokens_common_lines: List[str],
        tokens_theme_lines: List[str],
        template_lines: List[str],
        timestamp: str,
    ):
        self.theme_name = self._sanitize_theme_name(theme_name)
        self.tokens_common_lines = tokens_common_lines
        self.tokens_theme_lines = tokens_theme_lines
        self.template_lines = template_lines
        self.timestamp = timestamp

    @staticmethod
    def _sanitize_theme_name(name: str) -> str:
        """Sanitize theme name to ensure it's YAML-safe."""
        # If name contains special characters, wrap it in quotes
        special_chars = ":,[]{}#&*!|>'\"%@`"
        if any(c in name for c in special_chars):
            return f'"{name}"'
        return name


def validate_yaml_content(content: str, filepath: Path) -> None:
    """Validate that content is proper YAML."""
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise YAMLValidationError(f"Invalid YAML in {filepath}: {str(e)}")


def read_file(filepath: Path, validate: bool = True) -> List[str]:
    """Read file contents and optionally validate as YAML."""
    try:
        with filepath.open("r") as f:
            lines = f.readlines()
            if validate:
                validate_yaml_content("".join(lines), filepath)
            return lines
    except FileNotFoundError:
        logging.error(f"The file '{filepath}' was not found.")
        sys.exit(1)
    except IOError:
        logging.error(f"The file '{filepath}' could not be read.")
        sys.exit(1)
    except YAMLValidationError as e:
        logging.error(str(e))
        sys.exit(1)


def indent_lines(lines: List[str], indent: str = "  ") -> Generator[str, None, None]:
    """Indent lines while preserving empty lines and existing indentation."""
    return (indent + line if line.strip() else line for line in lines)


def validate_final_yaml(content: str, filepath: Path) -> None:
    """Validate the final generated YAML content."""
    try:
        validate_yaml_content(content, filepath)
    except YAMLValidationError as e:
        # If validation fails, save the problematic content for debugging
        debug_path = filepath.with_suffix(".debug.yaml")
        with debug_path.open("w") as f:
            f.write(content)
        logging.error(f"{str(e)}\nProblematic content saved to {debug_path}")
        sys.exit(1)


def generate_theme_file(output_path: Path, theme_data: ThemeData) -> None:
    """Generate a theme file with YAML validation."""
    content = []
    content.append(f"{theme_data.theme_name}:\n")
    content.append("\n")

    # Add description comments with proper indentation
    description_lines = [
        "# Graphite is a contemporary theme that offers both a calm dark color scheme and a",
        "# clean light theme, featuring native device fonts and a cohesive design",
        "# language. Carefully crafted to be visually appealing and easy on the eyes,",
        "# Graphite ensures a consistent user experience throughout the entire Home",
        "# Assistant interface, including the administration panel and code editors.",
        "# https://github.com/TilmanGriesel/graphite",
    ]
    content.extend(indent_lines([line + "\n" for line in description_lines]))
    content.append("\n")

    # Add timestamp comments with proper indentation
    timestamp_lines = [
        "#------------------------------------------------------",
        f"# This file was generated at {theme_data.timestamp}",
        "#------------------------------------------------------",
    ]
    content.extend(indent_lines([line + "\n" for line in timestamp_lines]))
    content.append("\n")

    content.extend(indent_lines(theme_data.tokens_theme_lines))
    content.append("\n")
    content.extend(indent_lines(theme_data.tokens_common_lines))
    content.append("\n")
    content.extend(indent_lines(theme_data.template_lines))

    # Join all content and validate
    final_content = "".join(content)
    validate_final_yaml(final_content, output_path)

    # Write to file
    with output_path.open("w") as f:
        f.write(final_content)
    logging.info(f"Generated theme file: {output_path}")


def generate_auto_theme(
    light_theme_path: Path,
    dark_theme_path: Path,
    output_path: Path,
    theme_name: str,
    timestamp: str,
) -> None:
    """Generate auto theme with YAML validation."""

    def read_theme_content(theme_path: Path, indent_level: str) -> str:
        with theme_path.open("r") as f:
            lines = f.readlines()[1:]  # Skip the first line (theme name)
            return "".join(f"{indent_level}{line}" for line in lines)

    content = []
    content.append(f"{ThemeData._sanitize_theme_name(theme_name)}:\n")
    content.append("  modes:\n")
    content.append("    light:")
    content.append(read_theme_content(light_theme_path, "      "))
    content.append("    dark:")
    content.append(read_theme_content(dark_theme_path, "      "))

    # Join all content and validate
    final_content = "".join(content)
    validate_final_yaml(final_content, output_path)

    # Write to file
    with output_path.open("w") as f:
        f.write(final_content)
    logging.info(f"Generated auto theme file: {output_path}")


def get_theme_name(base_name: str, variant: str = "", dev_mode: bool = False) -> str:
    """Generate theme name with proper YAML escaping."""
    parts = [base_name]
    if variant:
        parts.append(variant)
    if dev_mode:
        parts.append("[DEV]")
    return " ".join(parts)


def get_filename(base_name: str, variant: str = "") -> str:
    """Generate safe filename for theme."""
    name_parts = [base_name.lower()]
    if variant:
        name_parts.append(variant.lower())
    return "-".join(name_parts) + ".yaml"


def copy_to_final_destination(source_dir: Path, final_dir: Path) -> None:
    """Copy generated themes to the final destination directory."""
    try:
        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.copytree(source_dir, final_dir)
        logging.info(f"Copied themes to final destination: {final_dir}")
    except Exception as e:
        logging.error(f"Error copying to final destination: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Assemble theme files from YAML fragments."
    )
    parser.add_argument(
        "--src-dir", default="src", help="Source directory containing YAML fragments."
    )
    parser.add_argument(
        "--themes-dir",
        default="themes",
        help="Output directory for assembled theme files.",
    )
    parser.add_argument(
        "--name",
        default="Graphite",
        help="Base name for the theme (default: Graphite)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable dev mode (adds DEV suffix to theme names)",
    )
    parser.add_argument(
        "--final-dir",
        help="Final destination directory for the themes (e.g., ../../themes/graphite-dev)",
    )
    args = parser.parse_args()

    try:
        src_dir = Path(args.src_dir)
        themes_dir = Path(args.themes_dir)
        base_name = args.name
        dev_mode = args.dev

        tokens_common_file = src_dir / "tokens_common.yaml"
        tokens_dark_file = src_dir / "tokens_dark.yaml"
        tokens_light_file = src_dir / "tokens_light.yaml"
        template_file = src_dir / "template.yaml"

        # Read and validate all input files
        tokens_common_lines = read_file(tokens_common_file)
        tokens_dark_lines = read_file(tokens_dark_file)
        tokens_light_lines = read_file(tokens_light_file)
        template_lines = read_file(template_file)

        # Ensure themes directory exists and is empty
        if themes_dir.exists():
            shutil.rmtree(themes_dir)
        themes_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Define theme variants
        themes = [
            {
                "theme_name": get_theme_name(base_name, dev_mode=dev_mode),
                "tokens_theme_lines": tokens_dark_lines,
                "output_filename": get_filename(base_name),
            },
            {
                "theme_name": get_theme_name(base_name, "Light", dev_mode=dev_mode),
                "tokens_theme_lines": tokens_light_lines,
                "output_filename": get_filename(base_name, "light"),
            },
        ]

        # Generate individual themes
        for theme in themes:
            theme_data = ThemeData(
                theme_name=theme["theme_name"],
                tokens_common_lines=tokens_common_lines,
                tokens_theme_lines=theme["tokens_theme_lines"],
                template_lines=template_lines,
                timestamp=timestamp,
            )
            output_path = themes_dir / theme["output_filename"]
            generate_theme_file(output_path=output_path, theme_data=theme_data)

        # Generate auto theme
        light_theme_path = themes_dir / get_filename(base_name, "light")
        dark_theme_path = themes_dir / get_filename(base_name)
        auto_theme_path = themes_dir / get_filename(base_name, "auto")

        auto_theme_name = get_theme_name(base_name, "Auto", dev_mode=dev_mode)
        generate_auto_theme(
            light_theme_path=light_theme_path,
            dark_theme_path=dark_theme_path,
            output_path=auto_theme_path,
            theme_name=auto_theme_name,
            timestamp=timestamp,
        )

        logging.info(f"Theme files have been assembled in '{themes_dir}'.")

        # Copy to final destination if specified
        if args.final_dir:
            final_dir = Path(args.final_dir)
            copy_to_final_destination(themes_dir, final_dir)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
