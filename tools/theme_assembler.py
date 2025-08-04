#!/usr/bin/env python3

import sys
import logging
import argparse
import shutil
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import List, Generator, Dict, Any, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class YAMLValidationError(Exception):
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
        self.card_mod_theme = self._get_card_mod_theme_name(theme_name)

    @staticmethod
    def _sanitize_theme_name(name: str) -> str:
        special_chars = ":,[]{}#&*!|>'\"%@`"
        if any(c in name for c in special_chars):
            return f'"{name}"'
        return name

    @staticmethod
    def _get_card_mod_theme_name(name: str) -> str:
        return name.strip()


def validate_yaml_content(content: str, filepath: Path) -> None:
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise YAMLValidationError(f"Invalid YAML in {filepath}: {str(e)}")


def read_file(filepath: Path, validate: bool = True) -> List[str]:
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
    return (indent + line if line.strip() else line for line in lines)


def validate_final_yaml(content: str, filepath: Path) -> None:
    try:
        validate_yaml_content(content, filepath)
    except YAMLValidationError as e:
        debug_path = filepath.with_suffix(".debug.yaml")
        with debug_path.open("w") as f:
            f.write(content)
        logging.error(f"{str(e)}\nProblematic content saved to {debug_path}")
        sys.exit(1)


def generate_theme_file(output_path: Path, theme_data: ThemeData) -> None:
    content = []
    content.append(f"{theme_data.theme_name}:\n\n")
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

    timestamp_lines = [
        "#------------------------------------------------------",
        f"# This file was generated at {theme_data.timestamp}",
        "#------------------------------------------------------",
    ]
    content.extend(indent_lines([line + "\n" for line in timestamp_lines]))
    content.append("\n")

    content.append(f"  card-mod-theme: {theme_data.card_mod_theme}\n")
    content.append("\n")

    content.extend(indent_lines(theme_data.tokens_theme_lines))
    content.append("\n")
    content.extend(indent_lines(theme_data.tokens_common_lines))
    content.append("\n")
    content.extend(indent_lines(theme_data.template_lines))

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
    def read_theme_content(theme_path: Path, indent_level: str, is_light: bool = True) -> Tuple[str, Set[str]]:
        with theme_path.open("r") as f:
            lines = f.readlines()[1:]  # Skip the theme name line
            content = []
            seen_anchors = set()
            
            for line in lines:
                # Skip the card-mod-theme line if it exists
                if line.strip().startswith("card-mod-theme:"):
                    continue
                
                # Handle anchors
                anchor_match = re.search(r'&(\w+)', line)
                if anchor_match:
                    anchor_name = anchor_match.group(1)
                    seen_anchors.add(anchor_name)
                
                content.append(f"{indent_level}{line}")
            
            return "".join(content), seen_anchors

    # First pass: collect all anchors from both files
    _, light_anchors = read_theme_content(light_theme_path, "", True)
    _, dark_anchors = read_theme_content(dark_theme_path, "", False)
    
    # Find duplicate anchors
    duplicate_anchors = light_anchors.intersection(dark_anchors)
    
    # Second pass: Process files, renaming anchors in the dark theme
    def process_theme_content(theme_path: Path, indent_level: str, is_light: bool = True) -> str:
        with theme_path.open("r") as f:
            lines = f.readlines()[1:]  # Skip the theme name line
            content = []
            
            for line in lines:
                # Skip the card-mod-theme line if it exists
                if line.strip().startswith("card-mod-theme:"):
                    continue
                
                # In dark theme, rename duplicate anchors and their references
                if not is_light:
                    for anchor in duplicate_anchors:
                        # Replace anchor definitions
                        if f"&{anchor}" in line:
                            line = line.replace(f"&{anchor}", f"&{anchor}_dark")
                        
                        # Replace anchor references
                        if f"*{anchor}" in line:
                            line = line.replace(f"*{anchor}", f"*{anchor}_dark")
                
                # Remove existing indentation and apply the correct indent level
                stripped_line = line.lstrip()
                if stripped_line:  # Don't add extra indentation to empty lines
                    content.append(f"{indent_level}{stripped_line}")
                else:
                    content.append(line)  # Keep empty lines as-is
            
            return "".join(content)
    
    content = []
    sanitized_name = ThemeData._sanitize_theme_name(theme_name)
    card_mod_theme = ThemeData._get_card_mod_theme_name(theme_name)

    content.append(f"{sanitized_name}:\n")
    content.append(f"  card-mod-theme: {card_mod_theme}\n")
    content.append("  modes:\n")
    content.append("    light:\n")
    content.append(process_theme_content(light_theme_path, "      ", True))
    content.append("    dark:\n")
    content.append(process_theme_content(dark_theme_path, "      ", False))

    # Join content and clean up extra whitespace at the end
    final_content = "".join(content).rstrip() + "\n"
    validate_final_yaml(final_content, output_path)

    with output_path.open("w") as f:
        f.write(final_content)
    logging.info(f"Generated auto theme file: {output_path}")


def get_theme_name(base_name: str, variant: str = "", dev_mode: bool = False) -> str:
    parts = [base_name]
    if variant:
        parts.append(variant)
    if dev_mode:
        parts.append("[DEV]")
    return " ".join(parts)


def get_filename(base_name: str, variant: str = "") -> str:
    name_parts = [base_name.lower()]
    if variant:
        name_parts.append(variant.lower())
    return "-".join(name_parts) + ".yaml"


def copy_to_final_destination(source_dir: Path, final_dir: Path) -> None:
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
        tokens_eink_dark_file = src_dir / "tokens_eink_dark.yaml"
        tokens_eink_light_file = src_dir / "tokens_eink_light.yaml"
        template_file = src_dir / "template.yaml"
        template_eink_file = src_dir / "template_eink.yaml"

        tokens_common_lines = read_file(tokens_common_file)
        tokens_dark_lines = read_file(tokens_dark_file)
        tokens_light_lines = read_file(tokens_light_file)
        tokens_eink_dark_lines = read_file(tokens_eink_dark_file)
        tokens_eink_light_lines = read_file(tokens_eink_light_file)
        template_lines = read_file(template_file)
        template_eink_lines = read_file(template_eink_file)

        if themes_dir.exists():
            shutil.rmtree(themes_dir)
        themes_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        themes = [
            {
                "theme_name": get_theme_name(base_name, dev_mode=dev_mode),
                "tokens_theme_lines": tokens_dark_lines,
                "output_filename": get_filename(base_name),
                "template_lines": template_lines,
            },
            {
                "theme_name": get_theme_name(base_name, "Light", dev_mode=dev_mode),
                "tokens_theme_lines": tokens_light_lines,
                "output_filename": get_filename(base_name, "light"),
                "template_lines": template_lines,
            },
            {
                "theme_name": get_theme_name(base_name, "E-ink Dark", dev_mode=dev_mode),
                "tokens_theme_lines": tokens_eink_dark_lines,
                "output_filename": get_filename(base_name, "eink-dark"),
                "template_lines": template_eink_lines,
            },
            {
                "theme_name": get_theme_name(base_name, "E-ink Light", dev_mode=dev_mode),
                "tokens_theme_lines": tokens_eink_light_lines,
                "output_filename": get_filename(base_name, "eink-light"),
                "template_lines": template_eink_lines,
            },
        ]

        for theme in themes:
            theme_data = ThemeData(
                theme_name=theme["theme_name"],
                tokens_common_lines=tokens_common_lines,
                tokens_theme_lines=theme["tokens_theme_lines"],
                template_lines=theme["template_lines"],
                timestamp=timestamp,
            )
            output_path = themes_dir / theme["output_filename"]
            generate_theme_file(output_path=output_path, theme_data=theme_data)

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

        if args.final_dir:
            final_dir = Path(args.final_dir)
            copy_to_final_destination(themes_dir, final_dir)

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
