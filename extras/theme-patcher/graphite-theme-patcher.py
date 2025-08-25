#!/usr/bin/env python3

"""
Graphite Theme Patcher

A comprehensive tool for updating token values in Home Assistant Graphite theme files.

Author: Tilman Griesel
License: MIT
"""

import sys
import os
import logging
import tempfile
import re
import argparse
import yaml
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import fcntl
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum, auto
from packaging import version

__version__ = "2.1.0"

MAX_FILES_TO_PROCESS = 50
MAX_FILE_SIZE_MB = 10
MAX_LINES_PER_FILE = 10000
MAX_DOWNLOAD_SIZE_MB = 5
DOWNLOAD_TIMEOUT_SECONDS = 30

__author__ = "Tilman Griesel"
__changelog__ = {
    "2.1.0": "Added recipe system and dry-run functionality",
    "2.0.0": "Complete rewrite with simplified logic",
    "1.6.1": "Fixed indentation and missing comment headers for user defined entries in auto themes",
    "1.6.0": "Major robustness improvements with auto-detection, rollback, and validation",
    "1.5.0": "Fixed comment handling to ignore commented tokens",
    "1.4.2": "Allow none value",
    "1.4.1": "Improved logging and arguments",
    "1.4.0": "Added support for card-mod tokens",
    "1.3.0": "Enhanced color token handling with rgb()/rgba() formats",
    "1.2.0": "Added support for custom token creation",
    "1.1.0": "Added support for multiple themes and configurable paths",
    "1.0.0": "Initial release with RGB token support",
}

script_dir = Path(__file__).parent
log_dir = script_dir / "logs"
log_dir.mkdir(exist_ok=True)


def detect_homeassistant_config_path() -> str:
    """
    Automatically detect the Home Assistant configuration directory.

    Searches common installation locations to find a valid Home Assistant
    configuration directory containing a themes folder.

    Returns:
        str: Path to the themes directory within the HA configuration

    Search order:
        1. /config (Home Assistant OS/Supervised)
        2. /root/.homeassistant (HA Core default)
        3. ~/.homeassistant (HA Core user installation)
        4. Parent directory of script location
        5. Fallback to /config/themes
    """
    candidate_paths = [
        "/config",  # Home Assistant OS/Supervised
        "/root/.homeassistant",  # HA Core default installation
        str(Path.home() / ".homeassistant"),  # HA Core user installation
        str(script_dir.parent),  # Script parent directory
    ]

    for path in candidate_paths:
        config_path = Path(path)
        themes_path = config_path / "themes"

        if (
            config_path.exists()
            and config_path.is_dir()
            and themes_path.exists()
            and themes_path.is_dir()
        ):
            return str(themes_path)

    return "/config/themes"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - [v%(version)s] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "graphite_theme_patcher.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)
logger.version = __version__


class VersionFilter(logging.Filter):
    def filter(self, record):
        record.version = __version__
        return True


logger.addFilter(VersionFilter())


class ValidationError(Exception):
    pass


class RecipeError(Exception):
    pass


@contextmanager
def file_lock(lock_file: Path):
    """Exclusive file lock for atomic operations."""
    lock_path = lock_file.with_suffix(".lock")
    lock_fd = None
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
            except OSError:
                pass
        try:
            lock_path.unlink()
        except OSError:
            pass


class TokenType(Enum):
    RGB = auto()
    SIZE = auto()
    OPACITY = auto()
    RADIUS = auto()
    GENERIC = auto()
    CARD_MOD = auto()

    @classmethod
    def from_string(cls, value: str) -> "TokenType":
        mapping = {
            "rgb": cls.RGB,
            "size": cls.SIZE,
            "opacity": cls.OPACITY,
            "radius": cls.RADIUS,
            "generic": cls.GENERIC,
            "card-mod": cls.CARD_MOD,
        }
        return mapping.get(value.lower(), cls.GENERIC)


class Recipe:

    def __init__(self, recipe_data: Dict[str, Any]):
        self.data = recipe_data
        self.metadata = recipe_data.get("recipe", {})
        self.patches = recipe_data.get("patches", [])

        self._validate_recipe()

    def _validate_recipe(self) -> None:
        required_fields = ["name", "author", "version", "patcher_version"]
        for field in required_fields:
            if field not in self.metadata:
                raise RecipeError(f"Missing required metadata field: {field}")

        try:
            required_version = self.metadata["patcher_version"].replace(">=", "")
            current_version = __version__
            if version.parse(current_version) < version.parse(required_version):
                raise RecipeError(
                    f"Recipe requires patcher version {self.metadata['patcher_version']}, "
                    f"but current version is {current_version}"
                )
        except Exception as e:
            raise RecipeError(f"Invalid patcher version format: {e}")

        if not isinstance(self.patches, list):
            raise RecipeError("Patches must be a list")

        for i, patch in enumerate(self.patches):
            if not isinstance(patch, dict):
                raise RecipeError(f"Patch {i} must be a dictionary")

            required_patch_fields = ["token", "type", "value"]
            for field in required_patch_fields:
                if field not in patch:
                    raise RecipeError(f"Patch {i} missing required field: {field}")

    @classmethod
    def from_file(cls, file_path: str) -> "Recipe":
        try:
            path = Path(file_path)
            if not path.exists():
                raise RecipeError(f"Recipe file not found: {file_path}")

            if path.stat().st_size > MAX_DOWNLOAD_SIZE_MB * 1024 * 1024:
                raise RecipeError(f"Recipe file too large: {file_path}")

            with open(path, "r", encoding="utf-8") as f:
                recipe_data = yaml.safe_load(f)

            if not isinstance(recipe_data, dict):
                raise RecipeError("Recipe must be a YAML dictionary")

            return cls(recipe_data)

        except yaml.YAMLError as e:
            raise RecipeError(f"Invalid YAML in recipe file: {e}")
        except Exception as e:
            raise RecipeError(f"Error loading recipe file: {e}")

    @classmethod
    def from_url(cls, url: str) -> "Recipe":
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise RecipeError("Recipe URL must use HTTP or HTTPS")

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": f"Graphite-Theme-Patcher/{__version__}",
                    "Accept": "text/plain, application/x-yaml, text/yaml",
                },
            )

            with urllib.request.urlopen(
                request, timeout=DOWNLOAD_TIMEOUT_SECONDS
            ) as response:
                content_length = response.headers.get("content-length")
                if (
                    content_length
                    and int(content_length) > MAX_DOWNLOAD_SIZE_MB * 1024 * 1024
                ):
                    raise RecipeError(f"Recipe file too large: {content_length} bytes")

                content = response.read(MAX_DOWNLOAD_SIZE_MB * 1024 * 1024 + 1)
                if len(content) > MAX_DOWNLOAD_SIZE_MB * 1024 * 1024:
                    raise RecipeError(f"Recipe file too large: {len(content)} bytes")

                recipe_data = yaml.safe_load(content.decode("utf-8"))

            if not isinstance(recipe_data, dict):
                raise RecipeError("Recipe must be a YAML dictionary")

            return cls(recipe_data)

        except urllib.error.URLError as e:
            raise RecipeError(f"Failed to download recipe: {e}")
        except yaml.YAMLError as e:
            raise RecipeError(f"Invalid YAML in recipe: {e}")
        except Exception as e:
            raise RecipeError(f"Error loading recipe from URL: {e}")

    def get_variants(self) -> List[str]:
        return self.metadata.get("variants", ["graphite"])

    def get_mode(self) -> str:
        return self.metadata.get("mode", "all")

    def get_patches_for_mode(self, target_mode: str) -> List[Dict[str, Any]]:
        applicable_patches = []

        for patch in self.patches:
            patch_mode = patch.get("mode", "all")

            if target_mode == "all" or patch_mode == "all" or target_mode == patch_mode:
                applicable_patches.append(patch)

        return applicable_patches


class IndentationManager:

    YAML_BASE_INDENT = 2
    YAML_NESTED_INDENT = 2

    def __init__(self, lines: List[str]):
        self.lines = lines
        self._indent_cache = {}

    def detect_base_indentation(self) -> int:
        if hasattr(self, "_base_indent"):
            return self._base_indent

        indent_counts = {}
        for line in self.lines:
            if line.strip() and not line.strip().startswith("#"):
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    indent_counts[indent] = indent_counts.get(indent, 0) + 1

        if indent_counts:
            self._base_indent = min(indent_counts.keys())
        else:
            self._base_indent = self.YAML_BASE_INDENT

        return self._base_indent

    def get_line_indentation(self, line_index: int) -> int:
        if line_index >= len(self.lines):
            return 0
        line = self.lines[line_index]
        return len(line) - len(line.lstrip())

    def get_section_indentation(self, section_info: Dict[str, Any]) -> int:
        return section_info.get("indent", self.YAML_BASE_INDENT)

    def get_content_indentation(self, parent_indent: int) -> int:
        base_indent = self.detect_base_indentation()
        return parent_indent + base_indent

    def get_theme_property_indentation(self) -> int:
        return self.detect_base_indentation()

    def get_mode_content_indentation(self, mode_section_indent: int) -> int:
        return self.get_content_indentation(mode_section_indent)

    def format_indented_line(self, indent_level: int, content: str) -> str:
        return " " * indent_level + content

    def validate_indentation_consistency(
        self, line_index: int, expected_indent: int
    ) -> bool:
        if line_index >= len(self.lines):
            return True
        actual_indent = self.get_line_indentation(line_index)
        return actual_indent == expected_indent

    def find_insertion_point_with_proper_indent(
        self,
        start_line: int,
        end_line: int,
        target_indent: int,
        after_pattern: str = None,
    ) -> Tuple[int, int]:
        best_line = end_line
        best_indent = target_indent

        for i in range(start_line, min(end_line, len(self.lines))):
            line = self.lines[i]
            if line.strip() and not line.strip().startswith("#"):
                line_indent = self.get_line_indentation(i)
                if line_indent == target_indent:
                    best_line = i + 1
                    best_indent = target_indent
                elif after_pattern and after_pattern in line:
                    best_line = i + 1
                    best_indent = target_indent

        return best_line, best_indent


class ThemePatcher:

    def __init__(
        self,
        token: str = "token-rgb-primary",
        token_type: str = "rgb",
        theme: str = "graphite",
        base_path: Optional[str] = None,
        target_mode: str = "all",
        dry_run: bool = False,
    ):
        self.theme = theme
        self.target_mode = target_mode
        self.dry_run = dry_run

        if base_path is None:
            base_path = detect_homeassistant_config_path()
        self.theme_path = Path(base_path) / theme

        self.token = token
        self.token_type = TokenType.from_string(token_type)

        self._validate_paths()
        self._validate_token()

    def _validate_paths(self) -> None:
        base_path = self.theme_path.parent
        if not base_path.exists():
            raise ValidationError(f"Directory not found: {base_path}")
        if not base_path.is_dir():
            raise ValidationError(f"Not a directory: {base_path}")

        theme_yaml_file = base_path / f"{self.theme}.yaml"

        if self.theme_path.exists() and self.theme_path.is_dir():
            if not os.access(self.theme_path, os.W_OK):
                raise ValidationError(f"Cannot write to theme: {self.theme_path}")
        elif theme_yaml_file.exists() and theme_yaml_file.is_file():
            self.theme_path = theme_yaml_file
            if not os.access(self.theme_path, os.W_OK):
                raise ValidationError(f"Cannot write to theme file: {self.theme_path}")
        else:
            raise ValidationError(
                f"Theme not found: neither {self.theme_path} nor {theme_yaml_file} exists"
            )

    def _validate_token(self) -> None:
        if not isinstance(self.token, str) or not self.token.strip():
            raise ValidationError("Token must be a non-empty string")

        token = self.token.strip()

        dangerous_chars = ["\n", "\r", "\t", "#", ":", '"', "'", "\\", "`"]
        if any(char in token for char in dangerous_chars):
            raise ValidationError(f"Token contains invalid characters: {token}")

        if token.startswith(("-", "!", "&", "*", "|", ">", "%", "@")):
            raise ValidationError(
                f"Token cannot start with YAML special character: {token}"
            )

        if len(token) > 100:
            raise ValidationError(f"Token name too long (max 100 chars): {token}")

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", token):
            raise ValidationError(
                f"Token must be alphanumeric with hyphens/underscores: {token}"
            )

    def _parse_color_value(self, value: str) -> Tuple[List[int], Optional[float]]:
        try:
            components = [x.strip() for x in value.split(",")]
            if len(components) not in (3, 4):
                raise ValidationError("Color must have 3 (RGB) or 4 (RGBA) components")
            rgb = [int(x) for x in components[:3]]
            alpha = float(components[3]) if len(components) == 4 else None

            if not all(0 <= x <= 255 for x in rgb):
                raise ValidationError("RGB values must be between 0 and 255")
            if alpha is not None and not 0 <= alpha <= 1:
                raise ValidationError("Alpha must be between 0 and 1")

            return rgb, alpha
        except ValueError:
            raise ValidationError("Invalid color values")

    def _validate_value(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        if self.token_type == TokenType.GENERIC:
            return value

        value = value.strip().strip("\"'")

        try:
            if self.token_type == TokenType.CARD_MOD:
                if (
                    "\n" in value
                    or value.strip().startswith("|")
                    or value.strip().startswith(">")
                ):
                    if not (
                        value.strip().startswith("|") or value.strip().startswith(">")
                    ):
                        value = "|\n" + "\n".join(
                            f"    {line}" for line in value.split("\n")
                        )
                    return value
                else:
                    return f'"{value}"'

            elif self.token_type == TokenType.SIZE:
                num_value = int(value)
                if num_value < 0:
                    raise ValidationError("Size must be positive")
                return f"{num_value}px"

            elif self.token_type == TokenType.OPACITY:
                if value.endswith("%"):
                    num_value = float(value.rstrip("%")) / 100
                else:
                    num_value = float(value)
                if not 0 <= num_value <= 1:
                    raise ValidationError("Opacity must be between 0 and 1")
                return str(num_value)

            elif self.token_type == TokenType.RADIUS:
                num_value = int(value)
                if num_value < 0:
                    raise ValidationError("Radius must be positive")
                return f"{num_value}px"

            elif self.token_type == TokenType.RGB:
                rgb, alpha = self._parse_color_value(value)
                if "rgb" in self.token.lower():
                    if alpha is not None:
                        raise ValidationError("RGB tokens cannot have alpha")
                    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
                if alpha is not None:
                    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
                return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"

            else:
                return value

        except ValidationError as e:
            raise ValidationError(f"Invalid value for token: {str(e)}")

    def _process_yaml_file(
        self, file_path: Path, value: Optional[str], create_token: bool = False
    ) -> bool:
        if value is None:
            return True

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if len(lines) > MAX_LINES_PER_FILE:
                logger.error(
                    f"File has too many lines: {file_path} ({len(lines)} > {MAX_LINES_PER_FILE})"
                )
                return False

            logger.debug(f"Processing file: {file_path} ({len(lines)} lines)")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            indent_manager = IndentationManager(lines)

            file_structure = self._analyze_file_structure(lines)

            existing_tokens = self._find_existing_tokens(lines, file_structure)

            if existing_tokens:
                self._update_existing_tokens(
                    lines, existing_tokens, value, timestamp, indent_manager
                )
                logger.info(
                    f"Updated {len(existing_tokens)} instances of token '{self.token}'"
                )
            elif create_token or self.token_type == TokenType.CARD_MOD:
                self._create_new_tokens(
                    lines, file_structure, value, timestamp, indent_manager
                )
                logger.info(f"Created new token '{self.token}'")
            else:
                logger.error(f"Token '{self.token}' not found in {file_path}")
                return False

            if not self._validate_yaml_structure(lines, indent_manager):
                logger.error(f"YAML structure validation failed for {file_path}")
                return False

            updated_content = "".join(lines)
            if not updated_content.endswith("\n"):
                updated_content += "\n"

            if self.dry_run:
                logger.info(f"[DRY RUN] Would update {file_path}")
                if existing_tokens:
                    for token_info in existing_tokens:
                        line_num = token_info["line_index"] + 1
                        logger.info(f"[DRY RUN] Line {line_num}: {self.token}: {value}")
                else:
                    logger.info(
                        f"[DRY RUN] Would create new token: {self.token}: {value}"
                    )
            else:
                with tempfile.NamedTemporaryFile(
                    mode="w", dir=file_path.parent, delete=False, encoding="utf-8"
                ) as tmp:
                    tmp.write(updated_content)
                    tmp.flush()
                    os.fsync(tmp.fileno())

                os.replace(tmp.name, file_path)
                logger.info(f"Successfully processed {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            if "tmp" in locals():
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
            return False

    def _analyze_file_structure(self, lines):
        structure = {
            "is_auto_theme": False,
            "light_section": None,
            "dark_section": None,
            "base_indent": 2,
        }

        for i, line in enumerate(lines):
            if line.strip().startswith("modes:"):
                structure["is_auto_theme"] = True
                break

        if structure["is_auto_theme"]:
            in_modes = False
            modes_indent = 0

            for i, line in enumerate(lines):
                line_stripped = line.lstrip()
                indent = len(line) - len(line_stripped)

                if line_stripped.startswith("modes:"):
                    in_modes = True
                    modes_indent = indent
                elif in_modes and line_stripped.startswith("light:"):
                    structure["light_section"] = {"start": i, "indent": indent}
                elif in_modes and line_stripped.startswith("dark:"):
                    if (
                        structure["light_section"]
                        and "end" not in structure["light_section"]
                    ):
                        structure["light_section"]["end"] = i
                    structure["dark_section"] = {"start": i, "indent": indent}
                elif in_modes and indent <= modes_indent and line_stripped:
                    if (
                        structure["dark_section"]
                        and "end" not in structure["dark_section"]
                    ):
                        structure["dark_section"]["end"] = i
                    elif (
                        structure["light_section"]
                        and "end" not in structure["light_section"]
                    ):
                        structure["light_section"]["end"] = i
                    break

            if structure["light_section"] and "end" not in structure["light_section"]:
                structure["light_section"]["end"] = len(lines)
            if structure["dark_section"] and "end" not in structure["dark_section"]:
                structure["dark_section"]["end"] = len(lines)

        return structure

    def _find_existing_tokens(self, lines, structure):
        token_instances = []

        for i, line in enumerate(lines):
            line_stripped = line.lstrip()
            if not line_stripped or line_stripped.startswith("#"):
                continue

            if line_stripped.startswith(f"{self.token}:"):
                context = "root"
                if structure["is_auto_theme"]:
                    if (
                        structure["light_section"]
                        and structure["light_section"]["start"]
                        < i
                        < structure["light_section"]["end"]
                    ):
                        context = "light"
                    elif (
                        structure["dark_section"]
                        and structure["dark_section"]["start"]
                        < i
                        < structure["dark_section"]["end"]
                    ):
                        context = "dark"

                include_token = False
                if context == "root":
                    include_token = True
                elif self.target_mode == "all":
                    include_token = True
                elif self.target_mode == context:
                    include_token = True

                if include_token:
                    token_instances.append(
                        {
                            "line_index": i,
                            "context": context,
                            "indent": len(line) - len(line_stripped),
                        }
                    )

        return token_instances

    def _update_existing_tokens(
        self, lines, token_instances, value, timestamp, indent_manager
    ):
        for token_info in token_instances:
            line_index = token_info["line_index"]
            indent = token_info["indent"]

            if not indent_manager.validate_indentation_consistency(line_index, indent):
                logger.warning(
                    f"Inconsistent indentation detected at line {line_index + 1}, correcting..."
                )
                indent = indent_manager.get_line_indentation(line_index)

            new_line = indent_manager.format_indented_line(
                indent,
                f"{self.token}: {value}  # Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n",
            )

            lines[line_index] = new_line

    def _create_new_tokens(self, lines, structure, value, timestamp, indent_manager):
        if self.token_type == TokenType.CARD_MOD:
            self._create_card_mod_token(lines, value, timestamp, indent_manager)
        elif structure["is_auto_theme"]:
            self._create_auto_theme_tokens(
                lines, structure, value, timestamp, indent_manager
            )
        else:
            self._create_standard_theme_token(lines, value, timestamp, indent_manager)

    def _create_card_mod_token(self, lines, value, timestamp, indent_manager):
        card_mod_line = -1
        for i, line in enumerate(lines):
            if line.lstrip().startswith("card-mod-theme:"):
                card_mod_line = i
                break

        if card_mod_line == -1:
            theme_indent = indent_manager.get_theme_property_indentation()
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith("#"):
                    card_mod_line_content = indent_manager.format_indented_line(
                        theme_indent, "card-mod-theme:\n"
                    )
                    lines.insert(i + 1, card_mod_line_content)
                    card_mod_line = i + 1
                    break

        theme_indent = indent_manager.get_theme_property_indentation()
        new_line = indent_manager.format_indented_line(
            theme_indent,
            f"{self.token}: {value}  # Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n",
        )
        lines.insert(card_mod_line + 1, new_line)

    def _create_auto_theme_tokens(
        self, lines, structure, value, timestamp, indent_manager
    ):
        sections_to_update = []

        if self.target_mode == "all":
            if structure["light_section"]:
                sections_to_update.append(("light", structure["light_section"]))
            if structure["dark_section"]:
                sections_to_update.append(("dark", structure["dark_section"]))
        elif self.target_mode == "light" and structure["light_section"]:
            sections_to_update.append(("light", structure["light_section"]))
        elif self.target_mode == "dark" and structure["dark_section"]:
            sections_to_update.append(("dark", structure["dark_section"]))

        for mode, section_info in reversed(sections_to_update):
            self._add_token_to_mode_section(
                lines, section_info, value, timestamp, indent_manager
            )

    def _add_token_to_mode_section(
        self, lines, section_info, value, timestamp, indent_manager
    ):
        """Add token to a specific mode section with professional indentation handling."""
        section_start = section_info["start"]
        section_end = section_info["end"]

        # Look for existing user-defined entries section
        user_section_line = -1
        last_user_token_line = -1

        for i in range(section_start, section_end):
            if i < len(lines) and "# User defined entries" in lines[i]:
                user_section_line = i
                # Find last token in user section
                for j in range(i + 1, section_end):
                    if j < len(lines):
                        line_stripped = lines[j].lstrip()
                        if (
                            line_stripped
                            and not line_stripped.startswith("#")
                            and ":" in line_stripped
                        ):
                            last_user_token_line = j
                        elif (
                            line_stripped.startswith("#")
                            and "User defined entries" not in line_stripped
                        ):
                            break
                break

        # Use professional indentation management
        mode_indent = indent_manager.get_section_indentation(section_info)
        content_indent = indent_manager.get_mode_content_indentation(mode_indent)

        if user_section_line == -1:
            # Create user-defined entries section with proper indentation
            insert_line = section_end
            lines.insert(insert_line, "\n")

            # Add header with consistent indentation
            header_line = indent_manager.format_indented_line(
                content_indent,
                "##############################################################################\n",
            )
            lines.insert(insert_line + 1, header_line)

            # Add comment with consistent indentation
            comment_line = indent_manager.format_indented_line(
                content_indent, "# User defined entries\n"
            )
            lines.insert(insert_line + 2, comment_line)
            insert_line += 3
        else:
            # Append to existing user section
            insert_line = (
                last_user_token_line + 1
                if last_user_token_line != -1
                else user_section_line + 1
            )

        # Insert the new token with professional indentation
        new_line = indent_manager.format_indented_line(
            content_indent,
            f"{self.token}: {value}  # Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n",
        )
        lines.insert(insert_line, new_line)

    def _create_standard_theme_token(self, lines, value, timestamp, indent_manager):
        """Create token in standard theme with professional indentation handling."""
        # Look for existing user-defined entries section
        user_section_line = -1
        last_user_token_line = -1

        for i, line in enumerate(lines):
            if "# User defined entries" in line:
                user_section_line = i
                # Find last token in user section
                for j in range(i + 1, len(lines)):
                    line_stripped = lines[j].lstrip()
                    if (
                        line_stripped
                        and not line_stripped.startswith("#")
                        and ":" in line_stripped
                    ):
                        last_user_token_line = j
                    elif (
                        line_stripped.startswith("#")
                        and "User defined entries" not in line_stripped
                    ):
                        break
                break

        # Use professional indentation management
        theme_indent = indent_manager.get_theme_property_indentation()

        if user_section_line == -1:
            # Create user-defined entries section at end with proper indentation
            lines.append("\n")

            header_line = indent_manager.format_indented_line(
                theme_indent,
                "##############################################################################\n",
            )
            lines.append(header_line)

            comment_line = indent_manager.format_indented_line(
                theme_indent, "# User defined entries\n"
            )
            lines.append(comment_line)

        # Insert the new token with professional indentation
        new_line = indent_manager.format_indented_line(
            theme_indent,
            f"{self.token}: {value}  # Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n",
        )

        if last_user_token_line != -1:
            lines.insert(last_user_token_line + 1, new_line)
        else:
            lines.append(new_line)

    def _validate_yaml_structure(
        self, lines: List[str], indent_manager: IndentationManager
    ) -> bool:
        """
        Validate YAML structure integrity after modifications.

        Args:
            lines: Modified YAML file lines
            indent_manager: Indentation manager for validation

        Returns:
            bool: True if YAML structure is valid, False otherwise
        """
        try:
            # Basic YAML structure validation
            content = "".join(lines)

            # Try to parse as YAML to catch structural issues
            import yaml

            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                logger.error(f"YAML syntax validation failed: {e}")
                return False

            # Validate indentation consistency
            base_indent = indent_manager.detect_base_indentation()
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith("#"):
                    line_indent = indent_manager.get_line_indentation(i)
                    if line_indent % base_indent != 0:
                        logger.warning(
                            f"Inconsistent indentation at line {i + 1}: {line_indent} spaces"
                        )
                        # Don't fail for this, just warn

            # Validate user-defined entries sections have proper structure
            in_user_section = False
            for i, line in enumerate(lines):
                if "# User defined entries" in line:
                    in_user_section = True

                    # Check that the comment line has proper indentation
                    if not line.strip().startswith("#"):
                        logger.error(
                            f"User defined entries comment malformed at line {i + 1}"
                        )
                        return False

                elif (
                    in_user_section
                    and line.strip()
                    and not line.strip().startswith("#")
                ):
                    # This should be a token line in user section
                    if ":" not in line:
                        logger.error(
                            f"Invalid token format in user section at line {i + 1}"
                        )
                        return False
                elif (
                    in_user_section
                    and line.strip().startswith("#")
                    and "User defined entries" not in line
                ):
                    # End of user section
                    in_user_section = False

            logger.debug("YAML structure validation passed")
            return True

        except Exception as e:
            logger.error(f"YAML structure validation error: {e}")
            return False

    def set_token_value(self, value: Optional[str], create_token: bool = False) -> bool:
        """Set token value across all relevant YAML files with mode targeting."""
        if value is None:
            logger.info("Skipping update: value is None")
            return True

        logger.debug(f"Target mode: {self.target_mode}")
        logger.debug(f"Value to apply: '{value}'")

        try:
            logger.debug(f"Validating input value: '{value}'")
            validated_value = self._validate_value(value)
            if validated_value is None:
                raise ValidationError(f"Invalid value: {value}")
            logger.debug(f"Validated value: '{validated_value}'")

            yaml_files = []
            try:
                # Resolve theme path to prevent symlink traversal attacks
                theme_path_resolved = self.theme_path.resolve()

                if self.theme_path.is_file():
                    # Single YAML file theme (e-ink themes)
                    yaml_files.append(self.theme_path)
                else:
                    # Directory-based theme (traditional approach)
                    for path in self.theme_path.rglob("*.yaml"):
                        try:
                            path_resolved = path.resolve()
                            # Ensure the file is within the theme directory
                            if (
                                path_resolved.parent == theme_path_resolved
                                or theme_path_resolved in path_resolved.parents
                            ):
                                # Additional check: ensure no upward traversal in relative path
                                try:
                                    path_resolved.relative_to(theme_path_resolved)
                                    yaml_files.append(path)
                                except ValueError:
                                    # Path is outside theme directory
                                    logger.warning(
                                        f"Skipping file outside theme directory: {path}"
                                    )
                        except (OSError, RuntimeError) as e:
                            # Handle broken symlinks or circular references
                            logger.warning(f"Skipping problematic path {path}: {e}")
            except (OSError, RuntimeError) as e:
                raise ValidationError(f"Error scanning theme directory: {e}")
            if not yaml_files:
                raise ValidationError(f"No YAML files found in {self.theme_path}")

            # Check resource limits
            if len(yaml_files) > MAX_FILES_TO_PROCESS:
                raise ValidationError(
                    f"Too many YAML files ({len(yaml_files)} > {MAX_FILES_TO_PROCESS})"
                )

            # Validate file sizes
            for yaml_file in yaml_files:
                try:
                    file_size = yaml_file.stat().st_size
                    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        raise ValidationError(
                            f"File too large: {yaml_file} ({file_size / 1024 / 1024:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
                        )
                except OSError as e:
                    raise ValidationError(f"Cannot access file {yaml_file}: {e}")

            # Create backups before modifying any files (skip in dry-run mode)
            backups = {}
            if not self.dry_run:
                logger.debug(f"Creating backups for {len(yaml_files)} files")
                try:
                    for yaml_file in yaml_files:
                        backup_path = yaml_file.with_suffix(".yaml.backup")
                        file_size = yaml_file.stat().st_size
                        backup_path.write_bytes(yaml_file.read_bytes())
                        backups[yaml_file] = backup_path
                        logger.debug(
                            f"Created backup: {backup_path} ({file_size} bytes)"
                        )
                except Exception as e:
                    # Clean up any partial backups
                    for backup_path in backups.values():
                        try:
                            backup_path.unlink()
                        except OSError:
                            pass
                    raise ValidationError(f"Failed to create backups: {e}")
            else:
                logger.info(
                    f"[DRY RUN] Would create backups for {len(yaml_files)} files"
                )

            # Process files with rollback capability
            processed_files = []
            success = True

            try:
                for yaml_file in yaml_files:
                    logger.info(f"Processing: {yaml_file}")
                    with file_lock(yaml_file):
                        if self._process_yaml_file(
                            yaml_file, validated_value, create_token
                        ):
                            processed_files.append(yaml_file)
                        else:
                            success = False
                            break

                if success:
                    # All files processed successfully, clean up backups (or log in dry-run)
                    if self.dry_run:
                        logger.info(
                            f"[DRY RUN] All {len(yaml_files)} files would be processed successfully"
                        )
                    else:
                        logger.debug(f"Cleaning up {len(backups)} backup files")
                        for backup_path in backups.values():
                            try:
                                backup_path.unlink()
                                logger.debug(f"Removed backup: {backup_path}")
                            except OSError:
                                logger.warning(
                                    f"Could not remove backup: {backup_path}"
                                )
                else:
                    # Rollback all changes (or log in dry-run)
                    if self.dry_run:
                        logger.error("[DRY RUN] Processing would have failed")
                    else:
                        logger.error("Rolling back changes due to processing failure")
                        logger.debug(f"Rolling back {len(processed_files)} files")
                        for yaml_file in processed_files:
                            try:
                                backup_path = backups[yaml_file]
                                backup_size = backup_path.stat().st_size
                                yaml_file.write_bytes(backup_path.read_bytes())
                                logger.info(f"Restored: {yaml_file}")
                                logger.debug(
                                    f"Restored {backup_size} bytes from {backup_path}"
                                )
                            except Exception as e:
                                logger.error(f"Failed to restore {yaml_file}: {e}")

                        # Clean up backups after rollback
                        logger.debug("Cleaning up backups after rollback")
                        for backup_path in backups.values():
                            try:
                                backup_path.unlink()
                                logger.debug(
                                    f"Removed backup after rollback: {backup_path}"
                                )
                            except OSError:
                                pass

            except Exception as e:
                # Emergency rollback on unexpected errors
                logger.error(f"Emergency rollback due to: {e}")
                for yaml_file, backup_path in backups.items():
                    try:
                        if backup_path.exists():
                            yaml_file.write_bytes(backup_path.read_bytes())
                            backup_path.unlink()
                    except Exception as rollback_error:
                        logger.error(
                            f"Emergency rollback failed for {yaml_file}: {rollback_error}"
                        )
                raise

            return success

        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return False

    def apply_recipe(
        self,
        recipe: Recipe,
        override_theme: Optional[str] = None,
        override_mode: Optional[str] = None,
    ) -> bool:
        """Apply a recipe to themes with optional overrides."""
        try:
            # Determine target variants and mode
            variants = recipe.get_variants()
            if override_theme:
                variants = [override_theme]

            target_mode = override_mode if override_mode else recipe.get_mode()

            logger.info(
                f"Applying recipe '{recipe.metadata['name']}' v{recipe.metadata['version']}"
            )
            logger.info(f"Author: {recipe.metadata['author']}")
            if recipe.metadata.get("description"):
                logger.info(f"Description: {recipe.metadata['description']}")

            success = True

            # Process each variant
            for variant in variants:
                logger.info(f"Processing variant: {variant}")

                # Get patches applicable to the target mode
                patches = recipe.get_patches_for_mode(target_mode)
                logger.info(f"Applying {len(patches)} patches for mode '{target_mode}'")

                # Apply each patch
                for i, patch in enumerate(patches, 1):
                    try:
                        # Create a new patcher instance for this specific patch
                        patcher = ThemePatcher(
                            token=patch["token"],
                            token_type=patch["type"],
                            theme=variant,
                            base_path=self.theme_path.parent,
                            target_mode=patch.get("mode", target_mode),
                            dry_run=self.dry_run,
                        )

                        # Log patch details
                        patch_desc = patch.get("description", "No description")
                        logger.info(
                            f"Patch {i}/{len(patches)}: {patch['token']} = {patch['value']} ({patch_desc})"
                        )

                        # Apply the patch
                        if not patcher.set_token_value(
                            patch["value"], create_token=True
                        ):
                            logger.error(f"Failed to apply patch {i}: {patch['token']}")
                            success = False

                    except Exception as e:
                        logger.error(
                            f"Error applying patch {i} ({patch['token']}): {e}"
                        )
                        success = False

                if success:
                    logger.info(f"Successfully processed variant: {variant}")
                else:
                    logger.error(f"Failed to process variant: {variant}")

            return success

        except Exception as e:
            logger.error(f"Recipe application failed: {str(e)}")
            return False


def print_version():
    """Print version info and changelog."""
    print(f"\nGraphite Theme Patcher v{__version__}")
    print(f"Author: {__author__}\n")
    print("Changelog:")
    for version_key, changes in sorted(__changelog__.items(), reverse=True):
        print(f"v{version_key}:")
        print(f"  - {changes}")
    print()


def validate_args(args: argparse.Namespace) -> bool:
    """Check command-line arguments for validity."""
    # Recipe mode validation
    if args.recipe:
        # Recipe mode - value is not required
        args.value = None
        return True

    # Standard mode validation
    final_value = args.named_value if args.named_value else args.positional_value
    if final_value is None:
        logger.error("Missing token value. Provide as positional argument or --value.")
        return False

    args.value = final_value

    if not args.token or not args.token.strip():
        logger.error("Token must be a non-empty string.")
        return False

    valid_types = ["rgb", "size", "opacity", "radius", "generic", "card-mod"]
    if args.type not in valid_types:
        logger.error(f"Invalid token type. Must be one of: {', '.join(valid_types)}")
        return False

    if not args.theme or not args.theme.strip():
        logger.error("Theme must be a non-empty string.")
        return False

    # Path validation will be handled by ThemePatcher._validate_paths()
    # since we now support auto-detection when args.path is None

    # Mode validation (future-proofed for additional modes)
    if args.mode not in ["light", "dark", "all"]:
        logger.error(f"Invalid mode: {args.mode}")
        return False

    return True


def main():
    """Main entry point."""
    try:

        class ArgumentParserWithLogging(argparse.ArgumentParser):
            def error(self, message):
                logger.error(f"Argument Error: {message}")
                super().error(message)

        parser = ArgumentParserWithLogging(
            description=f"Update token values in theme files (v{__version__})."
        )

        parser.add_argument(
            "-v", "--version", action="store_true", help="Show version info and exit"
        )
        parser.add_argument(
            "positional_value", nargs="?", help="Token value (positional)"
        )
        parser.add_argument(
            "-V",
            "--value",
            dest="named_value",
            help="Token value (named), takes precedence over positional",
        )
        parser.add_argument(
            "-t",
            "-n",
            "--token",
            "--name",
            default="token-rgb-primary",
            help="Token to update (default: token-rgb-primary)",
        )
        parser.add_argument(
            "-T",
            "--type",
            default="rgb",
            choices=["rgb", "size", "opacity", "radius", "generic", "card-mod"],
            help="Token type (default: rgb)",
        )
        parser.add_argument(
            "-m", "--theme", default="graphite", help="Theme name (default: graphite)"
        )
        parser.add_argument(
            "-p",
            "--path",
            default=None,
            help="Base path for themes (default: auto-detect HA config directory)",
        )
        parser.add_argument(
            "-c",
            "--create",
            action="store_true",
            help="Create token if it doesn't exist",
        )
        parser.add_argument(
            "-M",
            "--mode",
            default="all",
            choices=["light", "dark", "all"],
            help="For auto themes: target light mode, dark mode, or all (default: all)",
        )
        parser.add_argument(
            "-r",
            "--recipe",
            help="Apply recipe from file path or URL instead of single token",
        )
        parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="Show what would be changed without modifying files",
        )

        args = parser.parse_args()

        if args.version:
            print_version()
            sys.exit(0)

        logger.info(f"Arguments received: {args}")
        if not validate_args(args):
            sys.exit(1)

        # Determine the actual base path
        actual_base_path = (
            args.path if args.path else detect_homeassistant_config_path()
        )

        # Recipe mode
        if args.recipe:
            logger.info(f"Loading recipe from: {args.recipe}")
            try:
                # Load recipe from file or URL
                if args.recipe.startswith(("http://", "https://")):
                    recipe = Recipe.from_url(args.recipe)
                else:
                    recipe = Recipe.from_file(args.recipe)

                # Create a patcher instance for recipe processing
                patcher = ThemePatcher(
                    token="placeholder",  # Will be overridden by recipe patches
                    token_type="generic",
                    theme=args.theme,
                    base_path=args.path,
                    target_mode=args.mode,
                    dry_run=args.dry_run,
                )

                # Apply the recipe
                if not patcher.apply_recipe(
                    recipe, override_theme=args.theme, override_mode=args.mode
                ):
                    logger.error("Recipe application failed.")
                    sys.exit(1)

                if args.dry_run:
                    logger.info("[DRY RUN] Recipe processing completed successfully")
                else:
                    logger.info("Recipe applied successfully")

            except RecipeError as e:
                logger.error(f"Recipe error: {e}")
                sys.exit(1)

        # Standard token mode
        else:
            # Override token name for card-mod
            token = args.token if args.type != "card-mod" else "card-mod-root"

            # Enhanced logging for mode-specific operations
            mode_info = f"mode: {args.mode}"
            dry_run_info = " [DRY RUN]" if args.dry_run else ""

            logger.info(
                f"Patching '{token}' (type: '{args.type}') in theme '{args.theme}' "
                f"with value: '{args.value}' ({mode_info}) (base path: '{actual_base_path}'){dry_run_info}"
            )

            patcher = ThemePatcher(
                token=token,
                token_type=args.type,
                theme=args.theme,
                base_path=args.path,
                target_mode=args.mode,
                dry_run=args.dry_run,
            )

            # card-mod tokens must be created if missing
            create_token = args.create or (patcher.token_type == TokenType.CARD_MOD)

            if not patcher.set_token_value(args.value, create_token):
                logger.error("Update failed.")
                sys.exit(1)

            if args.dry_run:
                logger.info("[DRY RUN] Update completed successfully")
            else:
                logger.info("Update completed.")

    except (RecipeError, ValidationError) as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
