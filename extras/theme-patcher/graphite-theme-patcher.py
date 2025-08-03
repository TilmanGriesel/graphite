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
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import fcntl
from typing import Optional, List, Union, Dict, Tuple
from enum import Enum, auto

__version__ = "1.6.0"

# Security and performance constraints
MAX_FILES_TO_PROCESS = 50       # Maximum number of YAML files to process per operation
MAX_FILE_SIZE_MB = 10          # Maximum file size in megabytes to prevent memory issues
MAX_LINES_PER_FILE = 10000     # Maximum lines per file to prevent DoS attacks

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
        "/config",                              # Home Assistant OS/Supervised
        "/root/.homeassistant",                 # HA Core default installation
        str(Path.home() / ".homeassistant"),   # HA Core user installation
        str(script_dir.parent),                 # Script parent directory
    ]
    
    for path in candidate_paths:
        config_path = Path(path)
        themes_path = config_path / "themes"
        
        # Validate that this appears to be a valid HA configuration directory
        if (config_path.exists() and 
            config_path.is_dir() and 
            themes_path.exists() and 
            themes_path.is_dir()):
            return str(themes_path)
    
    # Fallback to standard HA OS path if no valid directory found
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
    """Custom logging filter to inject version information into log records."""
    
    def filter(self, record):
        """Add version information to log record."""
        record.version = __version__
        return True


logger.addFilter(VersionFilter())


class ValidationError(Exception):
    """Custom exception raised when input validation fails."""
    pass


@contextmanager
def file_lock(lock_file: Path):
    """
    Provide an exclusive file lock for atomic YAML file operations.
    
    Creates a lock file to prevent concurrent modifications of the same
    theme file, ensuring data integrity during updates.
    
    Args:
        lock_file: Path to the file being locked
        
    Yields:
        None: Context manager for use in with statement
        
    Note:
        Uses POSIX file locking (fcntl) which is not available on Windows.
        Lock files are automatically cleaned up on exit.
    """
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
    """Enumeration of supported token types with their validation rules."""
    
    RGB = auto()        # Color tokens expecting RGB/RGBA values
    SIZE = auto()       # Size tokens expecting pixel values
    OPACITY = auto()    # Opacity tokens expecting 0-1 decimal values
    RADIUS = auto()     # Border radius tokens expecting pixel values
    GENERIC = auto()    # Generic tokens with minimal validation
    CARD_MOD = auto()   # Card-mod specific tokens requiring quotes

    @classmethod
    def from_string(cls, value: str) -> "TokenType":
        """
        Convert string token type to enum value.
        
        Args:
            value: String representation of token type
            
        Returns:
            TokenType: Corresponding enum value, defaults to GENERIC
        """
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
    """
    Core class for updating token values in Home Assistant theme files.
    
    Provides comprehensive token management with support for both standard
    themes and auto themes with mode-specific targeting capabilities.
    """
    
    def __init__(
        self,
        token: str = "token-rgb-primary",
        token_type: str = "rgb",
        theme: str = "graphite",
        base_path: Optional[str] = None,
        target_mode: str = "all",
    ):
        """
        Initialize the theme patcher with specified parameters.
        
        Args:
            token: Name of the token to update
            token_type: Type of token (rgb, size, opacity, radius, generic, card-mod)
            theme: Name of the theme directory
            base_path: Base themes directory path (auto-detected if None)
            target_mode: Target mode for auto themes (light, dark, all)
        """
        self.theme = theme
        self.target_mode = target_mode
        
        # Auto-detect base path if not provided
        if base_path is None:
            base_path = detect_homeassistant_config_path()
        self.theme_path = Path(base_path) / theme
        
        self.token = token
        self.token_type = TokenType.from_string(token_type)
        
        # Validate configuration before proceeding
        self._validate_paths()
        self._validate_token()

    def _validate_paths(self) -> None:
        """
        Validate that theme directories exist and are accessible.
        
        Raises:
            ValidationError: If directories are missing, invalid, or not writable
        """
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
        """
        Validate token name for security and YAML compatibility.
        
        Ensures the token name is safe to use in YAML files and prevents
        injection attacks through malicious token names.
        
        Raises:
            ValidationError: If token name is invalid or potentially dangerous
        """
        if not isinstance(self.token, str) or not self.token.strip():
            raise ValidationError("Token must be a non-empty string")
            
        token = self.token.strip()
        
        # Validate against potentially dangerous characters
        dangerous_chars = ['\n', '\r', '\t', '#', ':', '"', "'", '\\', '`']
        if any(char in token for char in dangerous_chars):
            raise ValidationError(f"Token contains invalid characters: {token}")
            
        # Prevent tokens starting with YAML special characters
        if token.startswith(('-', '!', '&', '*', '|', '>', '%', '@')):
            raise ValidationError(f"Token cannot start with YAML special character: {token}")
            
        # Enforce reasonable length constraints
        if len(token) > 100:
            raise ValidationError(f"Token name too long (max 100 chars): {token}")
            
        # Require valid identifier format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', token):
            raise ValidationError(f"Token must be alphanumeric with hyphens/underscores: {token}")

    def _parse_color_value(self, value: str) -> Tuple[List[int], Optional[float]]:
        """
        Parse and validate color values in RGB or RGBA format.
        
        Args:
            value: Comma-separated color values (e.g., "255, 128, 0" or "255, 128, 0, 0.8")
            
        Returns:
            Tuple containing RGB values list and optional alpha value
            
        Raises:
            ValidationError: If color format is invalid or values are out of range
        """
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
        """
        Validate and format token value according to its type.
        
        Args:
            value: Raw token value to validate
            
        Returns:
            Formatted and validated token value, or None if input is None
            
        Raises:
            ValidationError: If value is invalid for the token type
        """
        if value is None:
            return None

        if self.token_type == TokenType.GENERIC:
            return value

        # Remove surrounding quotes for processing
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
                    # RGB tokens use comma-separated format without function wrapper
                    if alpha is not None:
                        raise ValidationError("RGB tokens cannot have alpha")
                    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
                # Use CSS function format for other color tokens
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
        """Update or create the token in a YAML file with mode-specific handling."""
        if value is None:
            return True

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Check line count limit
            if len(lines) > MAX_LINES_PER_FILE:
                logger.error(f"File has too many lines: {file_path} ({len(lines)} > {MAX_LINES_PER_FILE})")
                return False
                
            logger.debug(f"Processing file: {file_path} ({len(lines)} lines)")
            logger.debug(f"Looking for token: '{self.token}' of type: {self.token_type.name}")

            # Analyze file structure to locate tokens in both standard and auto themes
            token_instances = []  # Track found tokens: (line_index, is_in_modes_section, mode_type)
            in_modes_section = False
            in_light_or_dark = False
            current_mode_type = None
            current_indent_level = 0
            
            for i, line in enumerate(lines):
                line_stripped = line.lstrip()
                # Process only non-empty, non-comment lines
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                # Determine current indentation depth for structure tracking
                indent_level = len(line) - len(line_stripped)
                
                # Detect entry into auto theme modes section
                if line_stripped.startswith("modes:"):
                    in_modes_section = True
                    current_indent_level = indent_level
                    logger.debug(f"Line {i+1}: Entering modes section (indent: {indent_level})")
                    continue
                elif in_modes_section and indent_level <= current_indent_level:
                    # Exit modes section when indentation returns to original level
                    in_modes_section = False
                    in_light_or_dark = False
                    logger.debug(f"Line {i+1}: Exiting modes section")
                
                # Detect specific mode subsections (extensible for future theme modes)
                if in_modes_section and (line_stripped.startswith("light:") or line_stripped.startswith("dark:")):
                    current_mode_type = "light" if line_stripped.startswith("light:") else "dark"
                    in_light_or_dark = True
                    logger.debug(f"Line {i+1}: Entering {current_mode_type} mode section")
                    continue
                elif in_modes_section and in_light_or_dark and indent_level <= current_indent_level + 2:
                    # Exit mode subsection when indentation decreases
                    in_light_or_dark = False
                    current_mode_type = None
                    logger.debug(f"Line {i+1}: Exiting light/dark mode section")
                
                # Evaluate token matches against targeting criteria
                if line_stripped.startswith(f"{self.token}:"):
                    if not in_modes_section:
                        # Standard theme: include tokens when targeting all modes
                        if self.target_mode == "all":
                            token_instances.append((i, False, None))
                            logger.debug(f"Line {i+1}: Found token at root level: {line_stripped}")
                    elif in_light_or_dark:
                        # Auto theme: include tokens matching target mode criteria
                        should_include = (
                            self.target_mode == "all" or 
                            self.target_mode == current_mode_type
                        )
                        if should_include:
                            token_instances.append((i, True, current_mode_type))
                            logger.debug(f"Line {i+1}: Found token in {current_mode_type} mode section: {line_stripped}")
                        else:
                            logger.debug(f"Line {i+1}: Skipping token in {current_mode_type} mode (target: {self.target_mode})")
                    else:
                        logger.debug(f"Line {i+1}: Found token but not in valid context: {line_stripped}")
            
            token_exists = len(token_instances) > 0
            
            logger.debug(f"Token detection summary: found {len(token_instances)} instances")
            for idx, (line_num, in_modes, mode_type) in enumerate(token_instances):
                if in_modes:
                    context = f"{mode_type} mode section"
                else:
                    context = "root level"
                logger.debug(f"  Instance {idx+1}: Line {line_num+1} ({context})")

            if not token_exists and not create_token:
                logger.error(f"Token '{self.token}' not found in {file_path}")
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug(f"Using timestamp: {timestamp}")
            logger.debug(f"Target value: '{value}'")

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
                # Update existing token instances
                logger.debug(f"Updating {len(token_instances)} existing token instances")
                for idx, (line_index, is_in_modes, mode_type) in enumerate(reversed(token_instances)):
                    original_line = lines[line_index].rstrip()
                    
                    # Use the same value for all targeted modes
                    target_value = value
                    if is_in_modes:
                        logger.debug(f"Applying value to {mode_type} mode: '{target_value}'")
                    
                    # Use appropriate indentation for each instance
                    if is_in_modes:
                        # For modes section, use the existing line's indentation
                        existing_line = lines[line_index]
                        existing_indent = len(existing_line) - len(existing_line.lstrip())
                        instance_indent = " " * existing_indent
                        context = f"{mode_type} mode section"
                    else:
                        # For root level, use base indentation
                        instance_indent = token_indent
                        context = "root level"
                    
                    instance_line = (
                        f"{instance_indent}{self.token}: {target_value}  "
                        f"# Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n"
                    )
                    
                    logger.debug(f"  Modification {idx+1} at line {line_index+1} ({context}):")
                    logger.debug(f"    Before: {original_line}")
                    logger.debug(f"    After:  {instance_line.rstrip()}")
                    
                    lines[line_index] = instance_line
                    
                logger.info(f"Updated {len(token_instances)} instances of token '{self.token}'")
            else:
                # Create new token - handle modes structure if needed
                logger.debug("Creating new token instance(s)")
                if self.token_type == TokenType.CARD_MOD:
                    logger.debug(f"Inserting card-mod token after line {card_mod_theme_index+1}")
                    logger.debug(f"New line: {new_line.rstrip()}")
                    lines.insert(card_mod_theme_index + 1, new_line)
                else:
                    # Check if this file has a modes structure for auto themes
                    has_modes_structure = any("modes:" in line for line in lines)
                    logger.debug(f"Theme has modes structure: {has_modes_structure}")
                    
                    if has_modes_structure:
                        # Insert token in both light and dark modes if they exist
                        light_section_end = -1
                        dark_section_end = -1
                        in_modes = False
                        in_light = False
                        in_dark = False
                        modes_indent = 0
                        
                        for i, line in enumerate(lines):
                            line_stripped = line.lstrip()
                            if line_stripped.startswith("modes:"):
                                in_modes = True
                                modes_indent = len(line) - len(line_stripped)
                                continue
                            elif in_modes and line_stripped.startswith("light:"):
                                in_light = True
                                in_dark = False
                            elif in_modes and line_stripped.startswith("dark:"):
                                in_dark = True
                                in_light = False
                                if light_section_end > -1:
                                    light_section_end = i - 1
                            elif in_modes and len(line) - len(line_stripped) <= modes_indent and line_stripped:
                                # End of modes section
                                if in_dark:
                                    dark_section_end = i
                                elif in_light:
                                    light_section_end = i
                                break
                        
                        # If we didn't find explicit end, use end of file
                        if in_light and light_section_end == -1:
                            light_section_end = len(lines)
                        if in_dark and dark_section_end == -1:
                            dark_section_end = len(lines)
                        
                        # Insert in both sections with proper indentation
                        mode_token_indent = " " * (modes_indent + 8)  # modes + light/dark + token level
                        mode_new_line = (
                            f"{mode_token_indent}{self.token}: {value}  "
                            f"# Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n"
                        )
                        
                        insertions_made = 0
                        
                        # Insert in dark section if targeted
                        if dark_section_end > -1 and (self.target_mode == "all" or self.target_mode == "dark"):
                            dark_new_line = (
                                f"{mode_token_indent}{self.token}: {value}  "
                                f"# Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n"
                            )
                            logger.debug(f"Inserting token in dark section at line {dark_section_end}")
                            logger.debug(f"Dark section line: {dark_new_line.rstrip()}")
                            lines.insert(dark_section_end, dark_new_line)
                            insertions_made += 1
                            
                        # Insert in light section if targeted  
                        if light_section_end > -1 and (self.target_mode == "all" or self.target_mode == "light"):
                            light_new_line = (
                                f"{mode_token_indent}{self.token}: {value}  "
                                f"# Modified by Graphite Theme Patcher v{__version__} - {timestamp}\n"
                            )
                            # Adjust index if we already inserted in dark section
                            insert_at = light_section_end + insertions_made
                            logger.debug(f"Inserting token in light section at line {insert_at}")
                            logger.debug(f"Light section line: {light_new_line.rstrip()}")
                            lines.insert(insert_at, light_new_line)
                            insertions_made += 1
                            
                        if insertions_made > 0:
                            logger.info(f"Created token '{self.token}' in {insertions_made} mode section(s)")
                        else:
                            logger.warning("Could not find appropriate location in modes structure")
                    else:
                        # Standard theme - add to user section
                        logger.debug("Processing standard theme structure")
                        user_section_exists = False
                        for line in lines:
                            if "# User defined entries" in line:
                                user_section_exists = True
                                break
                        
                        if not user_section_exists:
                            logger.debug("Creating user defined entries section")
                            lines.append(f"\n{token_indent}##############################################################################\n")
                            lines.append(f"{token_indent}# User defined entries\n")
                        else:
                            logger.debug("User defined entries section already exists")
                            
                        logger.debug(f"Appending new token line: {new_line.rstrip()}")
                        lines.append(new_line)

            # Join lines and ensure file ends with newline
            updated_content = ''.join(lines)
            if not updated_content.endswith('\n'):
                updated_content += '\n'
                logger.debug("Added missing newline at end of file")

            logger.debug(f"Writing {len(updated_content)} characters to file")
            
            # Write changes atomically
            with tempfile.NamedTemporaryFile(
                mode="w", dir=file_path.parent, delete=False, encoding="utf-8"
            ) as tmp:
                logger.debug(f"Created temporary file: {tmp.name}")
                tmp.write(updated_content)
                tmp.flush()
                os.fsync(tmp.fileno())
                logger.debug("Flushed and synced temporary file")

            logger.debug(f"Replacing original file with temporary file")
            os.replace(tmp.name, file_path)
            action = "Created" if not token_exists else "Updated"
            logger.info(f"{action} token in {file_path}")
            logger.debug(f"File operation completed successfully")
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
            logger.debug(f"Creating backups for {len(yaml_files)} files")
            try:
                for yaml_file in yaml_files:
                    backup_path = yaml_file.with_suffix(".yaml.backup")
                    file_size = yaml_file.stat().st_size
                    backup_path.write_bytes(yaml_file.read_bytes())
                    backups[yaml_file] = backup_path
                    logger.debug(f"Created backup: {backup_path} ({file_size} bytes)")
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
                    logger.debug(f"Cleaning up {len(backups)} backup files")
                    for backup_path in backups.values():
                        try:
                            backup_path.unlink()
                            logger.debug(f"Removed backup: {backup_path}")
                        except OSError:
                            logger.warning(f"Could not remove backup: {backup_path}")
                else:
                    # Rollback all changes
                    logger.error("Rolling back changes due to processing failure")
                    logger.debug(f"Rolling back {len(processed_files)} files")
                    for yaml_file in processed_files:
                        try:
                            backup_path = backups[yaml_file]
                            backup_size = backup_path.stat().st_size
                            yaml_file.write_bytes(backup_path.read_bytes())
                            logger.info(f"Restored: {yaml_file}")
                            logger.debug(f"Restored {backup_size} bytes from {backup_path}")
                        except Exception as e:
                            logger.error(f"Failed to restore {yaml_file}: {e}")
                    
                    # Clean up backups after rollback
                    logger.debug("Cleaning up backups after rollback")
                    for backup_path in backups.values():
                        try:
                            backup_path.unlink()
                            logger.debug(f"Removed backup after rollback: {backup_path}")
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
        
        # Enhanced logging for mode-specific operations
        mode_info = f"mode: {args.mode}"
            
        logger.info(
            f"Patching '{token}' (type: '{args.type}') in theme '{args.theme}' "
            f"with value: '{args.value}' ({mode_info}) (base path: '{actual_base_path}')"
        )

        patcher = ThemePatcher(
            token=token,
            token_type=args.type,
            theme=args.theme,
            base_path=args.path,
            target_mode=args.mode,
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
