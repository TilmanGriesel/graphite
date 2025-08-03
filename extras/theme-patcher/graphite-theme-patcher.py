#!/usr/bin/env python3

"""
Graphite Theme Patcher

Updates token values in theme files for the Home Assistant Graphite theme.
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

__version__ = "1.6.0"

MAX_FILES_TO_PROCESS = 50
MAX_FILE_SIZE_MB = 10
MAX_LINES_PER_FILE = 10000

__author__ = "Tilman Griesel"
__changelog__ = {
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
    Detect Home Assistant configuration directory.
    
    Returns the path to the HA config directory containing themes and scripts folders.
    Checks for common HA installation patterns.
    """
    # Common HA paths to check
    candidate_paths = [
        "/config",  # Home Assistant OS/Supervised
        "/root/.homeassistant",  # HA Core default
        str(Path.home() / ".homeassistant"),  # HA Core user install
        str(script_dir.parent),  # Directory above script location
    ]
    
    for path in candidate_paths:
        config_path = Path(path)
        themes_path = config_path / "themes"
        
        # Check if this looks like a HA config directory
        if (config_path.exists() and 
            config_path.is_dir() and 
            themes_path.exists() and 
            themes_path.is_dir()):
            return str(themes_path)
    
    # Fallback to original default
    return "/config/themes"

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
    """Raised when input is invalid."""
    pass


@contextmanager
def file_lock(lock_file: Path):
    """Provide an exclusive file lock for atomic operations."""
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


class ThemePatcher:
    def __init__(
        self,
        token: str = "token-rgb-primary",
        token_type: str = "rgb",
        theme: str = "graphite",
        base_path: Optional[str] = None,
    ):
        self.theme = theme
        # Use dynamic detection if no base_path provided
        if base_path is None:
            base_path = detect_homeassistant_config_path()
        self.theme_path = Path(base_path) / theme
        self.token = token
        self.token_type = TokenType.from_string(token_type)
        self._validate_paths()
        self._validate_token()

    def _validate_paths(self) -> None:
        """Check directories exist and are writable."""
        base_path = self.theme_path.parent
        if not base_path.exists():
            raise ValidationError(f"Directory not found: {base_path}")
        if not base_path.is_dir():
            raise ValidationError(f"Not a directory: {base_path}")

        if not self.theme_path.exists():
            raise ValidationError(f"Theme not found: {self.theme_path}")
        if not self.theme_path.is_dir():
            raise ValidationError(f"Not a directory: {self.theme_path}")
        if not os.access(self.theme_path, os.W_OK):
            raise ValidationError(f"Cannot write to theme: {self.theme_path}")

    def _validate_token(self) -> None:
        """Ensure token is a valid YAML key and safe to use."""
        if not isinstance(self.token, str) or not self.token.strip():
            raise ValidationError("Token must be a non-empty string")
            
        token = self.token.strip()
        
        # Check for potentially dangerous characters
        dangerous_chars = ['\n', '\r', '\t', '#', ':', '"', "'", '\\', '`']
        if any(char in token for char in dangerous_chars):
            raise ValidationError(f"Token contains invalid characters: {token}")
            
        # Ensure token doesn't start with special YAML characters
        if token.startswith(('-', '!', '&', '*', '|', '>', '%', '@')):
            raise ValidationError(f"Token cannot start with YAML special character: {token}")
            
        # Check reasonable length limits
        if len(token) > 100:
            raise ValidationError(f"Token name too long (max 100 chars): {token}")
            
        # Ensure it's a valid identifier-like string
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', token):
            raise ValidationError(f"Token must be alphanumeric with hyphens/underscores: {token}")

    def _parse_color_value(self, value: str) -> Tuple[List[int], Optional[float]]:
        """Parse comma-separated RGB or RGBA values."""
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
        """Validate and format the value based on the token type."""
        if value is None:
            return None

        if self.token_type == TokenType.GENERIC:
            return value

        # Strip quotes for other types
        value = value.strip().strip("\"'")

        try:
            if self.token_type == TokenType.CARD_MOD:
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
                    # Token name includes 'rgb', so just commas
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
        """Update or create the token in a YAML file."""
        if value is None:
            return True

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Check line count limit
            if len(lines) > MAX_LINES_PER_FILE:
                logger.error(f"File has too many lines: {file_path} ({len(lines)} > {MAX_LINES_PER_FILE})")
                return False

            # Check if token exists as an actual property (not in a comment)
            token_exists = False
            token_line_index = -1
            
            # Process line by line
            for i, line in enumerate(lines):
                line_stripped = line.lstrip()
                # Skip empty lines and comments
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                # Check if this non-comment line contains our token
                if line_stripped.startswith(f"{self.token}:"):
                    token_exists = True
                    token_line_index = i
                    break

            if not token_exists and not create_token:
                logger.error(f"Token '{self.token}' not found in {file_path}")
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Determine indentation
            if self.token_type == TokenType.CARD_MOD:
                card_mod_theme_index = -1
                for i, line in enumerate(lines):
                    line_stripped = line.lstrip()
                    if line_stripped.startswith("card-mod-theme:") and not line_stripped.startswith('#'):
                        card_mod_theme_index = i
                        break
                        
                if card_mod_theme_index == -1:
                    if create_token:
                        # Create card-mod-theme section if it doesn't exist
                        logger.info("Creating card-mod-theme section")
                        # Find a good place to insert it (after existing sections)
                        insert_index = len(lines)
                        for i, line in enumerate(lines):
                            line_stripped = line.lstrip()
                            if line_stripped and not line_stripped.startswith('#'):
                                # Found first non-comment line, use its indentation
                                base_indent = len(line) - len(line_stripped)
                                break
                        else:
                            base_indent = 0
                            
                        # Insert card-mod-theme section
                        indent_str = " " * base_indent
                        lines.append(f"\n{indent_str}card-mod-theme:\n")
                        card_mod_theme_index = len(lines) - 1
                    else:
                        logger.error("No card-mod-theme key found and create_token=False")
                        return False
                    
                base_indent = len(lines[card_mod_theme_index]) - len(
                    lines[card_mod_theme_index].lstrip()
                )
            else:
                # Find indentation from last non-comment line
                base_indent = 0
                for line in reversed(lines):
                    line_stripped = line.lstrip()
                    if line_stripped and not line_stripped.startswith('#'):
                        base_indent = len(line) - len(line_stripped)
                        break

            token_indent = " " * base_indent
            # newline character \n added at the end after timestamp on 2025-05-01
            new_line = (
                f"{token_indent}{self.token}: {value}  "
                f"# Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n"
            )

            if token_exists:
                # Update existing token
                lines[token_line_index] = new_line
            else:
                if self.token_type == TokenType.CARD_MOD:
                    lines.insert(card_mod_theme_index + 1, new_line)
                else:
                    # Check for user section
                    user_section_exists = False
                    for line in lines:
                        if "# User defined entries" in line:
                            user_section_exists = True
                            break
                    
                    if not user_section_exists:
                        lines.append(f"\n{token_indent}##############################################################################\n")
                        lines.append(f"{token_indent}# User defined entries\n")
                        
                    lines.append(new_line)

            # Join lines and ensure file ends with newline
            updated_content = ''.join(lines)
            if not updated_content.endswith('\n'):
                updated_content += '\n'

            # Write changes atomically
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
        """Set token value across all relevant YAML files."""
        if value is None:
            logger.info("Skipping update: value is None")
            return True

        try:
            validated_value = self._validate_value(value)
            if validated_value is None:
                raise ValidationError(f"Invalid value: {value}")

            yaml_files = []
            try:
                # Resolve theme path to prevent symlink traversal attacks
                theme_path_resolved = self.theme_path.resolve()
                for path in self.theme_path.rglob("*.yaml"):
                    try:
                        path_resolved = path.resolve()
                        # Ensure the file is within the theme directory
                        if (path_resolved.parent == theme_path_resolved or 
                            theme_path_resolved in path_resolved.parents):
                            # Additional check: ensure no upward traversal in relative path
                            try:
                                path_resolved.relative_to(theme_path_resolved)
                                yaml_files.append(path)
                            except ValueError:
                                # Path is outside theme directory
                                logger.warning(f"Skipping file outside theme directory: {path}")
                    except (OSError, RuntimeError) as e:
                        # Handle broken symlinks or circular references
                        logger.warning(f"Skipping problematic path {path}: {e}")
            except (OSError, RuntimeError) as e:
                raise ValidationError(f"Error scanning theme directory: {e}")
            if not yaml_files:
                raise ValidationError(f"No YAML files found in {self.theme_path}")
                
            # Check resource limits
            if len(yaml_files) > MAX_FILES_TO_PROCESS:
                raise ValidationError(f"Too many YAML files ({len(yaml_files)} > {MAX_FILES_TO_PROCESS})")
                
            # Validate file sizes
            for yaml_file in yaml_files:
                try:
                    file_size = yaml_file.stat().st_size
                    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        raise ValidationError(f"File too large: {yaml_file} ({file_size / 1024 / 1024:.1f}MB > {MAX_FILE_SIZE_MB}MB)")
                except OSError as e:
                    raise ValidationError(f"Cannot access file {yaml_file}: {e}")

            # Create backups before modifying any files
            backups = {}
            try:
                for yaml_file in yaml_files:
                    backup_path = yaml_file.with_suffix(".yaml.backup")
                    backup_path.write_bytes(yaml_file.read_bytes())
                    backups[yaml_file] = backup_path
                    logger.debug(f"Created backup: {backup_path}")
            except Exception as e:
                # Clean up any partial backups
                for backup_path in backups.values():
                    try:
                        backup_path.unlink()
                    except OSError:
                        pass
                raise ValidationError(f"Failed to create backups: {e}")

            # Process files with rollback capability
            processed_files = []
            success = True
            
            try:
                for yaml_file in yaml_files:
                    logger.info(f"Processing: {yaml_file}")
                    with file_lock(yaml_file):
                        if self._process_yaml_file(yaml_file, validated_value, create_token):
                            processed_files.append(yaml_file)
                        else:
                            success = False
                            break
                            
                if success:
                    # All files processed successfully, clean up backups
                    for backup_path in backups.values():
                        try:
                            backup_path.unlink()
                        except OSError:
                            logger.warning(f"Could not remove backup: {backup_path}")
                else:
                    # Rollback all changes
                    logger.error("Rolling back changes due to processing failure")
                    for yaml_file in processed_files:
                        try:
                            backup_path = backups[yaml_file]
                            yaml_file.write_bytes(backup_path.read_bytes())
                            logger.info(f"Restored: {yaml_file}")
                        except Exception as e:
                            logger.error(f"Failed to restore {yaml_file}: {e}")
                    
                    # Clean up backups after rollback
                    for backup_path in backups.values():
                        try:
                            backup_path.unlink()
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
                        logger.error(f"Emergency rollback failed for {yaml_file}: {rollback_error}")
                raise
                
            return success

        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return False

def print_version():
    """Print version info and changelog."""
    print(f"\nGraphite Theme Patcher v{__version__}")
    print(f"Author: {__author__}\n")
    print("Changelog:")
    for version, changes in sorted(__changelog__.items(), reverse=True):
        print(f"v{version}:")
        print(f"  - {changes}")
    print()


def validate_args(args: argparse.Namespace) -> bool:
    """Check command-line arguments for validity."""
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

        args = parser.parse_args()

        if args.version:
            print_version()
            sys.exit(0)

        logger.info(f"Arguments received: {args}")
        if not validate_args(args):
            sys.exit(1)

        # Override token name for card-mod
        token = args.token if args.type != "card-mod" else "card-mod-root"

        # Determine the actual base path for logging
        actual_base_path = args.path if args.path else detect_homeassistant_config_path()
        
        logger.info(
            f"Patching '{token}' (type: '{args.type}') in theme '{args.theme}' "
            f"with value: '{args.value}' (base path: '{actual_base_path}')"
        )

        patcher = ThemePatcher(
            token=token,
            token_type=args.type,
            theme=args.theme,
            base_path=args.path,
        )

        # card-mod tokens must be created if missing
        create_token = args.create or (patcher.token_type == TokenType.CARD_MOD)

        if not patcher.set_token_value(args.value, create_token):
            logger.error("Update failed.")
            sys.exit(1)

        logger.info("Update completed.")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
