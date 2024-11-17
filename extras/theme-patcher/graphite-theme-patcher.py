#!/usr/bin/env python3

"""
Graphite Theme Token Patcher
---------------------------

Updates a token value in Graphite theme files.

Usage:
    python3 graphite-theme-patcher.py <RGB_VALUE> [--token TOKEN_NAME]
    python3 graphite-theme-patcher.py "255, 158, 0"
    python3 graphite-theme-patcher.py "255, 158, 0" --token "token-rgb-secondary"
    
    Pass no arguments or 'None' for RGB_VALUE to skip modification.
    The --token argument is optional and defaults to "token-rgb-primary".
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
from typing import Optional, List

script_dir = Path(__file__).parent
log_dir = script_dir / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "graphite_theme_patcher.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


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
        base_path: str = "/config/themes/graphite",
        token: str = "token-rgb-primary",
    ):
        self.base_path = Path(base_path).resolve()
        self.token = token
        self._validate_base_path()
        self._validate_token()

    def _validate_base_path(self) -> None:
        """Validate directory exists with correct permissions."""
        if not self.base_path.exists():
            raise ValidationError(f"Directory not found: {self.base_path}")
        if not self.base_path.is_dir():
            raise ValidationError(f"Not a directory: {self.base_path}")
        if not os.access(self.base_path, os.W_OK):
            raise ValidationError(f"Insufficient permissions: {self.base_path}")

    def _validate_token(self) -> None:
        """Validate token format."""
        if not isinstance(self.token, str) or not self.token.strip():
            raise ValidationError("Token must be a non-empty string")
        if not re.match(r"^[a-zA-Z0-9-]+$", self.token):
            raise ValidationError(
                "Token must contain only letters, numbers, and hyphens"
            )

    def _validate_rgb_value(self, rgb_value: Optional[str]) -> Optional[List[int]]:
        """Validate RGB color value format."""
        if rgb_value is None:
            return None

        rgb_value = rgb_value.strip().strip("\"'")

        try:
            values = [int(x.strip()) for x in rgb_value.split(",")]
            if len(values) != 3:
                raise ValidationError("RGB must have 3 components")
            if not all(0 <= val <= 255 for val in values):
                raise ValidationError("RGB values must be 0-255")
            return values
        except (ValueError, AttributeError) as e:
            raise ValidationError(f"Invalid RGB format: {str(e)}")

    def _process_yaml_file(self, file_path: Path, rgb_value: Optional[str]) -> bool:
        """Process and update a YAML file."""
        if rgb_value is None:
            return True

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify required token exists
            if f"{self.token}:" not in content:
                logger.error(f"Token '{self.token}' not found in {file_path}")
                return False

            # Prepare update
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_value = f"{self.token}: {rgb_value}  # Modified via Graphite theme patcher - {timestamp}"
            pattern = f"{self.token}:.*(?:\r\n|\r|\n|$)"
            updated_content = re.sub(pattern, new_value + "\n", content)

            # Atomic write
            with tempfile.NamedTemporaryFile(
                mode="w", dir=file_path.parent, delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(updated_content)
                tmp.flush()
                os.fsync(tmp.fileno())

            os.replace(tmp.name, file_path)
            logger.info(f"Updated {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            if "tmp" in locals():
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
            return False

    def set_token_value(self, rgb_value: Optional[str]) -> bool:
        """Update token value across theme files."""
        if rgb_value is None:
            return True

        try:
            rgb_tuple = self._validate_rgb_value(rgb_value)
            if not rgb_tuple:
                raise ValidationError(f"Invalid RGB value: {rgb_value}")

            yaml_files = [
                path
                for path in self.base_path.rglob("*")
                if path.suffix in (".yaml") and self.base_path in path.resolve().parents
            ]

            if not yaml_files:
                raise ValidationError(f"No YAML files found in {self.base_path}")

            success = True
            for yaml_file in yaml_files:
                logger.info(f"Processing: {yaml_file}")
                with file_lock(yaml_file):
                    if not self._process_yaml_file(yaml_file, rgb_value):
                        success = False

            return success

        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return False


def main():
    """Main execution."""
    try:
        parser = argparse.ArgumentParser(
            description="Update token values in Graphite theme files."
        )
        parser.add_argument(
            "rgb_value", help="RGB value to set (comma-separated) or 'None' to skip"
        )
        parser.add_argument(
            "--token",
            default="token-rgb-primary",
            help="Token to update (default: token-rgb-primary)",
        )

        args = parser.parse_args()

        primary_color = None if args.rgb_value.lower() == "none" else args.rgb_value

        if primary_color is None:
            sys.exit(0)

        logger.info(f"Updating {args.token} to: {primary_color}")

        patcher = ThemePatcher(token=args.token)
        if not patcher.set_token_value(primary_color):
            logger.error("Update failed")
            sys.exit(1)

        logger.info("Update completed")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
