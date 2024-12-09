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
from typing import Optional, List, Union, Dict
from enum import Enum, auto

__version__ = "1.2.0"
__author__ = "Tilman Griesel"
__changelog__ = {
    "1.2.0": "Added support for custom token creation",
    "1.1.0": "Added support for size, opacity, and radius token and multiple themes and configurable paths",
    "1.0.0": "Initial release with RGG token support",
}

script_dir = Path(__file__).parent
log_dir = script_dir / "logs"
log_dir.mkdir(exist_ok=True)

# Configure logging with version information
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


class TokenType(Enum):
    RGB = auto()
    SIZE = auto()
    OPACITY = auto()
    RADIUS = auto()
    GENERIC = auto()

    @classmethod
    def from_string(cls, value: str) -> "TokenType":
        mapping = {
            "rgb": cls.RGB,
            "size": cls.SIZE,
            "opacity": cls.OPACITY,
            "radius": cls.RADIUS,
            "generic": cls.GENERIC,
        }
        return mapping.get(value.lower(), cls.GENERIC)


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

    def _validate_rgb_value(self, value: str) -> str:
        """Validate RGB color value format."""
        try:
            values = [int(x.strip()) for x in value.split(",")]
            if len(values) != 3:
                raise ValidationError("RGB must have 3 components")
            if not all(0 <= val <= 255 for val in values):
                raise ValidationError("RGB values must be 0-255")
            return ", ".join(str(v) for v in values)
        except (ValueError, AttributeError) as e:
            raise ValidationError(f"Invalid RGB format: {str(e)}")

    def _validate_size_value(self, value: str) -> str:
        """Validate size value format (must be a positive integer)."""
        try:
            num_value = int(value)
            if num_value < 0:
                raise ValidationError("Size must be a positive integer")
            return f"{num_value}px"  # Graphite uses the 'px' unit
        except ValueError as e:
            raise ValidationError("Invalid size format. Must be a positive integer")

    def _validate_opacity_value(self, value: str) -> str:
        """Validate opacity value format (0-1 or percentage)."""
        try:
            if value.endswith("%"):
                num_value = float(value.rstrip("%")) / 100
            else:
                num_value = float(value)

            if not 0 <= num_value <= 1:
                raise ValidationError("Opacity must be between 0 and 1 (or 0-100%)")
            return str(num_value)
        except ValueError as e:
            raise ValidationError(f"Invalid opacity format: {str(e)}")

    def _validate_value(self, value: Optional[str]) -> Optional[str]:
        """Validate value based on token type."""
        if value is None:
            return None

        value = value.strip().strip("\"'")

        try:
            if self.token_type == TokenType.RGB:
                return self._validate_rgb_value(value)
            elif self.token_type in (TokenType.SIZE, TokenType.RADIUS):
                return self._validate_size_value(value)
            elif self.token_type == TokenType.OPACITY:
                return self._validate_opacity_value(value)
            else:
                return value  # For generic tokens, accept any non-empty value
        except ValidationError as e:
            raise ValidationError(f"Invalid value for {self.token_type.name}: {str(e)}")

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
            new_value = f"{self.token}: {value}  # Modified via Graphite Theme Patcher v{__version__} - {timestamp}"

            if token_exists:
                # Update existing token
                pattern = f"{self.token}:.*(?:\r\n|\r|\n|$)"
                updated_content = re.sub(pattern, new_value + "\n", content)
            else:
                # Append new token at the end of the file
                custom_token_comment = (
                    "\n# Custom tokens added via Graphite Theme Patcher\n"
                    if not content.find("# Custom tokens") >= 0
                    else "\n"
                )
                updated_content = (
                    content.rstrip() + custom_token_comment + new_value + "\n"
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
            return True

        try:
            validated_value = self._validate_value(value)
            if validated_value is None:
                raise ValidationError(
                    f"Invalid value for {self.token_type.name}: {value}"
                )

            yaml_files = [
                path
                for path in self.theme_path.rglob("*")
                if path.suffix in (".yaml")
                and self.theme_path in path.resolve().parents
            ]

            if not yaml_files:
                raise ValidationError(f"No YAML files found in {self.base_path}")

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


def main():
    """Main execution."""
    try:
        parser = argparse.ArgumentParser(
            description=f"Update token values in theme files. (v{__version__})"
        )
        parser.add_argument(
            "--version", action="store_true", help="Show version information and exit"
        )
        parser.add_argument("value", nargs="?", help="Value to set or 'None' to skip")
        parser.add_argument(
            "--token",
            default="token-rgb-primary",
            help="Token to update (default: token-rgb-primary)",
        )
        parser.add_argument(
            "--type",
            default="rgb",
            choices=["rgb", "size", "opacity", "radius", "generic"],
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

        if args.value is None or args.token is None:
            parser.error("the following arguments are required: value, --token")

        value = None if args.value.lower() == "none" else args.value

        if value is None:
            sys.exit(0)

        action = "Creating/Updating" if args.create else "Updating"
        logger.info(
            f"Theme Patcher v{__version__} - {action} {args.token} ({args.type}) "
            f"in theme '{args.theme}' to: {value}"
        )

        patcher = ThemePatcher(
            token=args.token,
            token_type=args.type,
            theme=args.theme,
            base_path=args.path,
        )
        if not patcher.set_token_value(value, args.create):
            logger.error("Update failed")
            sys.exit(1)

        logger.info("Update completed")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
