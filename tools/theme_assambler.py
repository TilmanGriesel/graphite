#!/usr/bin/env python3

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Generator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ThemeData:
    def __init__(
        self,
        theme_name: str,
        about_lines: List[str],
        tokens_common_lines: List[str],
        tokens_theme_lines: List[str],
        template_lines: List[str],
        timestamp: str,
    ):
        self.theme_name = theme_name
        self.about_lines = about_lines
        self.tokens_common_lines = tokens_common_lines
        self.tokens_theme_lines = tokens_theme_lines
        self.template_lines = template_lines
        self.timestamp = timestamp


def read_file(filepath: Path) -> List[str]:
    try:
        with filepath.open("r") as f:
            return f.readlines()
    except FileNotFoundError:
        logging.error(f"The file '{filepath}' was not found.")
        sys.exit(1)
    except IOError:
        logging.error(f"The file '{filepath}' could not be read.")
        sys.exit(1)


def indent_lines(lines: List[str], indent: str = "  ") -> Generator[str, None, None]:
    return (indent + line if line.strip() else line for line in lines)


def generate_theme_file(output_path: Path, theme_data: ThemeData) -> None:
    with output_path.open("w") as f:
        f.write(f"{theme_data.theme_name}:\n")
        f.write("\n")
        f.writelines(indent_lines(theme_data.about_lines))
        f.write("\n")
        f.write(f"  # This file was generated at {theme_data.timestamp}\n")
        f.write("\n")
        f.writelines(indent_lines(theme_data.tokens_theme_lines))
        f.write("\n")
        f.writelines(indent_lines(theme_data.tokens_common_lines))
        f.write("\n")
        f.writelines(indent_lines(theme_data.template_lines))
    logging.info(f"Generated theme file: {output_path}")


def generate_auto_theme(
    light_theme_path: Path,
    dark_theme_path: Path,
    output_path: Path,
    about_lines: List[str],
    timestamp: str,
) -> None:
    def read_theme_content(theme_path: Path, indent_level: str) -> str:
        with theme_path.open("r") as f:
            lines = f.readlines()[1:]  # Skip the first line (theme name)
            return "".join(f"{indent_level}{line}" for line in lines)

    auto_theme_name = "Graphite Auto"
    content = [f"{auto_theme_name}:\n"]
    content.append("  modes:\n")
    content.append("    light:")
    content.append(read_theme_content(light_theme_path, "      "))
    content.append("    dark:")
    content.append(read_theme_content(dark_theme_path, "      "))

    with output_path.open("w") as f:
        f.writelines(content)
    logging.info(f"Generated auto theme file: {output_path}")


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
    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    themes_dir = Path(args.themes_dir)

    tokens_common_file = src_dir / "tokens_common.yaml"
    tokens_dark_file = src_dir / "tokens_dark.yaml"
    tokens_light_file = src_dir / "tokens_light.yaml"
    template_file = src_dir / "template.yaml"
    about_file = src_dir / "about.yaml"

    tokens_common_lines = read_file(tokens_common_file)
    tokens_dark_lines = read_file(tokens_dark_file)
    tokens_light_lines = read_file(tokens_light_file)
    template_lines = read_file(template_file)
    about_lines = read_file(about_file)

    themes_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    themes = [
        {
            "theme_name": "Graphite",
            "tokens_theme_lines": tokens_dark_lines,
            "output_filename": "graphite.yaml",
        },
        {
            "theme_name": "Graphite Light",
            "tokens_theme_lines": tokens_light_lines,
            "output_filename": "graphite-light.yaml",
        },
    ]

    # Generate individual themes
    for theme in themes:
        theme_data = ThemeData(
            theme_name=theme["theme_name"],
            about_lines=about_lines,
            tokens_common_lines=tokens_common_lines,
            tokens_theme_lines=theme["tokens_theme_lines"],
            template_lines=template_lines,
            timestamp=timestamp,
        )
        output_path = themes_dir / theme["output_filename"]
        generate_theme_file(output_path=output_path, theme_data=theme_data)

    # Generate auto theme
    light_theme_path = themes_dir / "graphite-light.yaml"
    dark_theme_path = themes_dir / "graphite.yaml"
    auto_theme_path = themes_dir / "graphite-auto.yaml"
    generate_auto_theme(
        light_theme_path=light_theme_path,
        dark_theme_path=dark_theme_path,
        output_path=auto_theme_path,
        about_lines=about_lines,
        timestamp=timestamp,
    )

    logging.info(f"Theme files have been assembled in '{themes_dir}'.")


if __name__ == "__main__":
    main()
