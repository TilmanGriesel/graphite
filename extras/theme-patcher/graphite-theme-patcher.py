#!/usr/bin/env python3

"""
Graphite Theme Patcher
-----------------

Updates token values in theme files. Created for the Home Assistant Graphite theme.

"""

import sys
import os
import logging
import tempfile
import re
import argparse
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import fcntl
from typing import Optional, List, Union, Dict, Tuple
from enum import Enum, auto

__version__ = "1.4.0"
__author__ = "Tilman Griesel"
__changelog__ = {
    "1.4.0": "Added support for card-mod tokens",
    "1.3.0": "Enhanced color token handling: RGB tokens use comma format, other tokens use rgb()/rgba() format",
    "1.2.0": "Added support for custom token creation",
    "1.1.0": "Added support for size, opacity, and radius token and multiple themes and configurable paths",
    "1.0.0": "Initial release with RGB token support",
}

script_dir = Path(__file__).parent
log_dir = script_dir / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
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
    """Raised for input validation failures."""

    pass


@contextmanager
def file_lock(lock_file: Path):
    """File access synchronization."""
    lock_path = lock_file.with_suffix(".lock")
    try:
        with open(lock_path, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield
    finally:
        with open(lock_path, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
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


class ThemePatcher:
    def __init__(
        self,
        token: str = "token-rgb-primary",
        token_type: str = "rgb",
        theme: str = "graphite",
        base_path: str = "/config/themes",
    ):
        self.theme = theme
        self.theme_path = Path(base_path) / theme
        self.token = token
        self.token_type = TokenType.from_string(token_type)
        self._validate_paths()
        self._validate_token()

    def _validate_paths(self) -> None:
        """Validate directories exist with correct permissions."""
        # Validate base themes directory
        base_path = self.theme_path.parent
        if not base_path.exists():
            raise ValidationError(f"Themes directory not found: {base_path}")
        if not base_path.is_dir():
            raise ValidationError(f"Not a directory: {base_path}")

        # Validate specific theme directory
        if not self.theme_path.exists():
            raise ValidationError(f"Theme not found: {self.theme_path}")
        if not self.theme_path.is_dir():
            raise ValidationError(f"Theme path is not a directory: {self.theme_path}")
        if not os.access(self.theme_path, os.W_OK):
            raise ValidationError(
                f"Insufficient permissions for theme: {self.theme_path}"
            )

    def _validate_token(self) -> None:
        """Validate token format."""
        if not isinstance(self.token, str) or not self.token.strip():
            raise ValidationError("Token must be a non-empty string")

    def _parse_color_value(self, value: str) -> Tuple[List[int], Optional[float]]:
        """Parse comma-separated color components."""
        try:
            components = [x.strip() for x in value.split(",")]

            if len(components) not in (3, 4):
                raise ValidationError("Color must have 3 or 4 components (RGB or RGBA)")

            rgb = [int(x) for x in components[:3]]
            alpha = float(components[3]) if len(components) == 4 else None

            if not all(0 <= x <= 255 for x in rgb):
                raise ValidationError("RGB values must be between 0 and 255")
            if alpha is not None and not 0 <= alpha <= 1:
                raise ValidationError("Alpha value must be between 0 and 1")

            return rgb, alpha
        except ValueError:
            raise ValidationError("Invalid color component values")

    def _validate_value(self, value: Optional[str]) -> Optional[str]:
        """Validate and format value based on token name and type."""
        if value is None:
            return None

        # Handle raw string prefix
        if value.startswith('r"') or value.startswith("r'"):
            value = value[1:]  # Remove 'r' prefix
            
        # Preserve quotes for generic tokens
        if self.token_type == TokenType.GENERIC:
            stripped_value = value.strip().strip("\"'")
            if any(char in stripped_value for char in " ()/:"):
                # Re-quote the value if it contains spaces or special characters
                return f'"{stripped_value}"'
            return stripped_value
            
        # Strip quotes for "strong typed" tokens
        value = value.strip().strip("\"'")

        try:
            if self.token_type == TokenType.CARD_MOD:
                if not isinstance(value, str):
                    raise ValidationError("Card-mod value must be a string")
                # Always double quote the user value
                return f'"{value}"'

            elif self.token_type == TokenType.SIZE:
                num_value = int(value)
                if num_value < 0:
                    raise ValidationError("Size must be a positive integer")
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
                    raise ValidationError("Radius must be a positive integer")
                return f"{num_value}px"

            elif self.token_type == TokenType.RGB:
                rgb, alpha = self._parse_color_value(value)

                # Use comma format for tokens containing 'rgb'
                if "rgb" in self.token.lower():
                    if alpha is not None:
                        raise ValidationError("RGB tokens cannot include alpha channel")
                    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"

                # Use rgb()/rgba() format for other tokens
                if alpha is not None:
                    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
                return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"

            else:
                return value  # For generic tokens, accept any non-empty value

        except ValidationError as e:
            raise ValidationError(f"Invalid value for token: {str(e)}")

    def _process_yaml_file(
        self, file_path: Path, value: Optional[str], create_token: bool = False
    ) -> bool:
        """Process and update a YAML file."""
        if value is None:
            return True

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if token exists
            token_exists = f"{self.token}:" in content

            if not token_exists and not create_token:
                logger.error(f"Token '{self.token}' not found in {file_path}")
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # For card-mod tokens, ensure they are placed after card-mod-theme
            if self.token_type == TokenType.CARD_MOD:
                if "card-mod-theme:" not in content:
                    logger.error("card-mod-theme key not found in file")
                    return False

                # Find the card-mod-theme section
                lines = content.split("\n")
                card_mod_theme_index = next(
                    (i for i, line in enumerate(lines) if "card-mod-theme:" in line), -1
                )

                if card_mod_theme_index == -1:
                    logger.error("Could not locate card-mod-theme section")
                    return False

                # Determine indentation level (same as card-mod-theme line)
                theme_line = lines[card_mod_theme_index]
                base_indent = len(theme_line) - len(theme_line.lstrip())
                # Match exactly the indentation of the `card-mod-theme:` key
                token_indent = " " * base_indent

            else:
                # Determine the indentation level of the last non-empty line
                lines = content.rstrip().split("\n")
                last_non_empty_line = next(
                    (line for line in reversed(lines) if line.strip()), ""
                )
                base_indent = len(last_non_empty_line) - len(
                    last_non_empty_line.lstrip()
                )
                token_indent = " " * base_indent

            new_value = f"{token_indent}{self.token}: {value}  # Modified via Graphite Theme Patcher v{__version__} - {timestamp}"

            if token_exists:
                # Update existing token
                pattern = f"^[ \t]*{self.token}:.*(?:\r\n|\r|\n|$)"
                updated_content = re.sub(
                    pattern, new_value + "\n", content, flags=re.MULTILINE
                )
            else:
                if self.token_type == TokenType.CARD_MOD:
                    # Insert after card-mod-theme section
                    lines = content.split("\n")
                    lines.insert(card_mod_theme_index + 1, new_value)
                    updated_content = "\n".join(lines)
                else:
                    # Append user-defined entries at the end of the file
                    if "# User defined entries" not in content:
                        custom_section = (
                            f"\n{token_indent}##############################################################################\n"
                            f"{token_indent}# User defined entries added via Graphite Theme Patcher\n"
                        )
                    else:
                        custom_section = "\n"

                    updated_content = (
                        content.rstrip() + custom_section + new_value + "\n"
                    )

            # Atomic write
            with tempfile.NamedTemporaryFile(
                mode="w", dir=file_path.parent, delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(updated_content)
                tmp.flush()
                os.fsync(tmp.fileno())

            os.replace(tmp.name, file_path)
            action = "Created" if not token_exists else "Updated"
            logger.info(f"{action} token in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            if "tmp" in locals():
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
            return False

    def set_token_value(self, value: Optional[str], create_token: bool = False) -> bool:
        """Update token value across theme files."""
        if value is None:
            logger.info("Skipping update: value is None")
            return True

        try:
            validated_value = self._validate_value(value)
            if validated_value is None:
                raise ValidationError(f"Invalid value: {value}")

            yaml_files = [
                path
                for path in self.theme_path.rglob("*")
                if path.suffix in (".yaml")
                and self.theme_path in path.resolve().parents
            ]

            if not yaml_files:
                raise ValidationError(f"No YAML files found in {self.theme_path}")

            success = True
            for yaml_file in yaml_files:
                logger.info(f"Processing: {yaml_file}")
                with file_lock(yaml_file):
                    if not self._process_yaml_file(
                        yaml_file, validated_value, create_token
                    ):
                        success = False

            return success

        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return False


def print_version():
    """Print version information and changelog."""
    print(f"\nGraphite Theme Patcher v{__version__}")
    print(f"Author: {__author__}\n")
    print("Changelog:")
    for version, changes in sorted(__changelog__.items(), reverse=True):
        print(f"v{version}:")
        print(f"  - {changes}")
    print()


def validate_args(args: argparse.Namespace) -> bool:
    """Validate command line arguments and log any errors."""
    # Determine final "value" from either positional or named argument
    final_value = None
    if args.named_value:
        final_value = args.named_value
    elif args.positional_value:
        final_value = args.positional_value

    # If user provided neither, log an error
    if final_value is None:
        error_msg = "Missing token value. Provide as positional argument or via --value"
        logger.error(f"Argument Error: {error_msg}")
        return False

    # Convert 'none' string to None
    if final_value.lower() == "none":
        args.value = None
    else:
        args.value = final_value

    # Validate token
    if not isinstance(args.token, str) or not args.token.strip():
        error_msg = "Token must be a non-empty string"
        logger.error(f"Argument Error: {error_msg}")
        return False

    # Validate token type
    valid_types = ["rgb", "size", "opacity", "radius", "generic", "card-mod"]
    if not hasattr(args, "type") or args.type not in valid_types:
        error_msg = f"Invalid token type. Must be one of: {', '.join(valid_types)}"
        logger.error(f"Argument Error: {error_msg}")
        return False

    # Validate theme
    if (
        not hasattr(args, "theme")
        or not isinstance(args.theme, str)
        or not args.theme.strip()
    ):
        error_msg = "Theme must be a non-empty string"
        logger.error(f"Argument Error: {error_msg}")
        return False

    # Validate path
    if (
        not hasattr(args, "path")
        or not isinstance(args.path, str)
        or not args.path.strip()
    ):
        error_msg = "Path must be a non-empty string"
        logger.error(f"Argument Error: {error_msg}")
        return False

    # Check if path exists
    theme_path = Path(args.path)
    if not theme_path.exists():
        error_msg = f"Theme path does not exist: {args.path}"
        logger.error(f"Argument Error: {error_msg}")
        return False

    if not theme_path.is_dir():
        error_msg = f"Theme path is not a directory: {args.path}"
        logger.error(f"Argument Error: {error_msg}")
        return False

    return True


def main():
    """Main execution."""
    try:

        class ArgumentParserWithLogging(argparse.ArgumentParser):
            def error(self, message):
                """Override error method to log before exiting."""
                logger.error(f"Argument Error: {message}")
                super().error(message)

        parser = ArgumentParserWithLogging(
            description=f"Update token values in theme files. (v{__version__})"
        )
        parser.add_argument(
            "--version", action="store_true", help="Show version information and exit"
        )
        # Value can be positional...
        parser.add_argument(
            "positional_value", nargs="?", help="Token value to set (positional)"
        )
        # ...or named
        parser.add_argument(
            "--value",
            dest="named_value",
            help="Token value to set (named). Takes precedence over the positional value.",
        )
        parser.add_argument(
            "--token",
            default="token-rgb-primary",
            help="Token to update (default: token-rgb-primary)",
        )
        parser.add_argument(
            "--type",
            default="rgb",
            choices=[
                "rgb",
                "size",
                "opacity",
                "radius",
                "generic",
                "card-mod",
            ],
            help="Type of token (default: rgb)",
        )
        parser.add_argument(
            "--theme", default="graphite", help="Theme name (default: graphite)"
        )
        parser.add_argument(
            "--path",
            default="/config/themes",
            help="Base path for themes directory (default: /config/themes)",
        )
        parser.add_argument(
            "--create",
            action="store_true",
            help="Create token if it doesn't exist",
        )

        args = parser.parse_args()

        if args.version:
            print_version()
            sys.exit(0)

        logger.info(f"Arguments received: {args}")
        if not validate_args(args):
            sys.exit(1)

        # Override token name for special cases
        token = args.token
        if args.type == "card-mod":
            token = "card-mod-root"

        # Log user info
        logger.info(
            f"Theme Patcher v{__version__} - "
            f"Updating token: '{token}' "
            f"(type: '{args.type}') in theme: '{args.theme}' "
            f"to value: '{args.value}'"
        )

        # Instantiate patcher
        patcher = ThemePatcher(
            token=token,
            token_type=args.type,
            theme=args.theme,
            base_path=args.path,
        )

        # Override token creation for special cases
        create_token = args.create
        if patcher.token_type == TokenType.CARD_MOD:
            create_token = True

        # Execute patcher
        if not patcher.set_token_value(args.value, create_token):
            logger.error("Update failed")
            sys.exit(1)

        logger.info("Update completed")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
