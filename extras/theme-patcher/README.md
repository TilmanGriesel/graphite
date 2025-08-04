# Graphite Theme Patcher

[![Test Theme Patcher](https://github.com/TilmanGriesel/graphite/actions/workflows/test-theme-patcher.yml/badge.svg)](https://github.com/TilmanGriesel/graphite/actions/workflows/test-theme-patcher.yml)

A comprehensive tool for updating token values in Home Assistant Graphite theme files with support for both traditional directory-based themes and e-ink theme variants.

## Features

- **Multi-theme Support**: Works with directory-based themes (`graphite/`) and e-ink themes (`graphite-eink-light.yaml`)
- **Token Type Validation**: RGB, size, opacity, radius, generic, and card-mod token types
- **Auto Theme Mode Targeting**: Target specific modes (light, dark, all) in auto themes
- **Atomic Operations**: Full rollback support with automatic backups
- **Security**: Path validation, file size limits, and input sanitization
- **Auto-detection**: Automatically finds Home Assistant configuration directory

## Installation

No installation required. The script is self-contained and uses only Python standard library modules.

## Usage

### Basic Syntax

```bash
python graphite-theme-patcher.py [OPTIONS] [VALUE]
```

### Quick Examples

```bash
# Update primary color in default theme
python graphite-theme-patcher.py "120, 130, 140"

# Update e-ink light theme
python graphite-theme-patcher.py --theme graphite-eink-light --value "100, 100, 100"

# Update e-ink dark theme
python graphite-theme-patcher.py --theme graphite-eink-dark --value "150, 150, 150"

# Create a new token
python graphite-theme-patcher.py --token my-custom-token --create --value "255, 0, 0"

# Update size token
python graphite-theme-patcher.py --token token-size-radius-large --type size --value "24"

# Update only light mode in auto theme
python graphite-theme-patcher.py --mode light --value "100, 110, 120"
```

## Command Line Options

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `VALUE` | Token value (positional or `--value`) | `"120, 130, 140"` |

### Optional Arguments

| Option | Short | Description | Default | Values |
|--------|-------|-------------|---------|--------|
| `--token` | `-t`, `-n` | Token name to update | `token-rgb-primary` | Any valid token name |
| `--type` | `-T` | Token type for validation | `rgb` | `rgb`, `size`, `opacity`, `radius`, `generic`, `card-mod` |
| `--theme` | `-m` | Theme name | `graphite` | Theme directory or file name |
| `--path` | `-p` | Base themes path | Auto-detected | Any valid directory path |
| `--mode` | `-M` | Target mode (auto themes only) | `all` | `light`, `dark`, `all` |
| `--create` | `-c` | Create token if missing | `false` | Flag |
| `--value` | `-V` | Token value (named parameter) | - | Any valid value |
| `--version` | `-v` | Show version info | - | Flag |
| `--help` | `-h` | Show help message | - | Flag |

## Token Types

### RGB Tokens (`--type rgb`)
Color tokens expecting RGB or RGBA values.

```bash
# RGB format (most common)
python graphite-theme-patcher.py --type rgb --value "120, 130, 140"

# RGBA format
python graphite-theme-patcher.py --type rgb --value "120, 130, 140, 0.8"
```

**Validation:**
- RGB values: 0-255
- Alpha values: 0.0-1.0
- Format: `R, G, B[, A]`

### Size Tokens (`--type size`)
Pixel-based size values.

```bash
python graphite-theme-patcher.py --token token-size-radius-large --type size --value "24"
```

**Output:** `24px`

### Opacity Tokens (`--type opacity`)
Decimal opacity values (0-1).

```bash
python graphite-theme-patcher.py --token token-opacity-overlay --type opacity --value "0.8"
# or percentage
python graphite-theme-patcher.py --token token-opacity-overlay --type opacity --value "80%"
```

**Output:** `0.8`

### Radius Tokens (`--type radius`)
Border radius pixel values.

```bash
python graphite-theme-patcher.py --token token-radius-button --type radius --value "12"
```

**Output:** `12px`


### Card-mod Tokens (`--type card-mod`)
Special tokens that require quotes and theme-level placement.

```bash
python graphite-theme-patcher.py --type card-mod --value "custom CSS value"
```

**Output:** `"custom CSS value"`

### Generic Tokens (`--type generic`)
Pass-through values with minimal validation, perfect for CSS properties and custom values.

```bash
# Custom CSS property
python graphite-theme-patcher.py --token custom-property --type generic --value "center"

# CSS background image
python graphite-theme-patcher.py --token custom-background --type generic --value 'url("https://example.com/image.jpg")'

# CSS gradient
python graphite-theme-patcher.py --token custom-background --type generic --value "linear-gradient(45deg, #ff0000, #0000ff)"

# Complex background with image and properties
python graphite-theme-patcher.py --token custom-background --type generic --value "url('./bg.jpg') center/cover no-repeat"

# Multiple backgrounds (layered)
python graphite-theme-patcher.py --token custom-background --type generic --value "url('./overlay.png'), linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.7))"

# CSS keywords
python graphite-theme-patcher.py --token custom-background --type generic --value "transparent"
```

**Use Cases:**
- CSS background properties (images, gradients, colors)
- Custom CSS values and keywords
- Complex CSS declarations
- Any value that doesn't fit other token types

## Theme Types

### Directory-based Themes (Traditional)
Themes stored in directories with multiple YAML files.

```
themes/
  graphite/
    ├── graphite.yaml
    ├── graphite-light.yaml
    └── graphite-auto.yaml
```

```bash
python graphite-theme-patcher.py --theme graphite --value "120, 130, 140"
```

### E-ink Themes
E-ink theme variants for grayscale displays.

```
themes/
  ├── graphite-eink-light.yaml
  └── graphite-eink-dark.yaml
```

```bash
# Light e-ink theme
python graphite-theme-patcher.py --theme graphite-eink-light --value "100, 100, 100"

# Dark e-ink theme  
python graphite-theme-patcher.py --theme graphite-eink-dark --value "150, 150, 150"
```

### Auto Themes with Mode Targeting
Target specific modes in auto themes.

```bash
# Update only light mode
python graphite-theme-patcher.py --mode light --value "120, 130, 140"

# Update only dark mode
python graphite-theme-patcher.py --mode dark --value "80, 90, 100" 

# Update both modes (default)
python graphite-theme-patcher.py --mode all --value "100, 110, 120"
```

## E-ink Theme Examples

E-ink displays work best with grayscale values. Here are some optimized examples:

### Light E-ink Theme (Black text on white background)
```bash
# Primary color (medium gray)
python graphite-theme-patcher.py --theme graphite-eink-light --value "100, 100, 100"

# Dark text elements
python graphite-theme-patcher.py --theme graphite-eink-light --token token-rgb-grey-1 --value "40, 40, 40"

# Light background elements  
python graphite-theme-patcher.py --theme graphite-eink-light --token token-rgb-grey-4 --value "180, 180, 180"
```

### Dark E-ink Theme (White text on black background)
```bash
# Primary color (medium-light gray)
python graphite-theme-patcher.py --theme graphite-eink-dark --value "150, 150, 150"

# Light text elements
python graphite-theme-patcher.py --theme graphite-eink-dark --token token-rgb-grey-1 --value "220, 220, 220"

# Dark background elements
python graphite-theme-patcher.py --theme graphite-eink-dark --token token-rgb-grey-4 --value "80, 80, 80"
```

## Advanced Usage

### Creating Custom Tokens

```bash
# Create a new color token
python graphite-theme-patcher.py \
  --token my-custom-primary \
  --type rgb \
  --value "64, 128, 255" \
  --create

# Create a new size token
python graphite-theme-patcher.py \
  --token my-button-height \
  --type size \
  --value "48" \
  --create

# Create a custom background image token
python graphite-theme-patcher.py \
  --token custom-sidebar-background \
  --type generic \
  --value 'url("https://example.com/sidebar-bg.jpg")' \
  --create
```

### Custom Background Images and Effects

Replace theme backgrounds with custom images, gradients, and complex CSS properties using the generic type:

```bash
# E-ink theme with custom background image
python graphite-theme-patcher.py \
  --theme graphite-eink-light \
  --token lovelace-background \
  --type generic \
  --value 'url("./local/backgrounds/eink-texture.jpg")'

# Card background with gradient overlay
python graphite-theme-patcher.py \
  --token ha-card-background \
  --type generic \
  --value "linear-gradient(135deg, rgba(255,255,255,0.1), rgba(0,0,0,0.1))" \
  --create

# Complex layered background
python graphite-theme-patcher.py \
  --token sidebar-background-color \
  --type generic \
  --value "url('./pattern.png') repeat, linear-gradient(to right, #f0f0f0, #e0e0e0)"

# Responsive background with size and position
python graphite-theme-patcher.py \
  --token custom-hero-background \
  --type generic \
  --value "url('hero.jpg') center/cover no-repeat fixed" \
  --create
```

### Batch Operations

```bash
# Update multiple tokens (use a script)
#!/bin/bash
THEME="graphite-eink-light"
python graphite-theme-patcher.py --theme $THEME --token token-rgb-primary --value "100, 100, 100"
python graphite-theme-patcher.py --theme $THEME --token token-rgb-grey-1 --value "40, 40, 40" 
python graphite-theme-patcher.py --theme $THEME --token token-rgb-grey-2 --value "80, 80, 80"
```

### Custom Installation Paths

```bash
# Specify custom HA config path
python graphite-theme-patcher.py \
  --path /custom/homeassistant/config/themes \
  --value "120, 130, 140"

# Docker/Add-on paths
python graphite-theme-patcher.py \
  --path /config/themes \
  --value "120, 130, 140"
```

## Path Auto-detection

The patcher automatically searches for Home Assistant configurations in this order:

1. `/config` (Home Assistant OS/Supervised)
2. `/root/.homeassistant` (HA Core default)
3. `~/.homeassistant` (HA Core user installation)  
4. Script parent directory
5. Fallback: `/config/themes`

## Safety Features

### Automatic Backups
Every operation creates backups before making changes:
```
themes/graphite-eink-light.yaml.backup
```
Backups are automatically cleaned up on successful operations or used for rollback on failures.

### Input Validation
- **File paths**: Prevents directory traversal attacks
- **Token names**: Alphanumeric with hyphens/underscores only
- **File sizes**: Limited to 10MB per file
- **File counts**: Maximum 50 YAML files per operation
- **Line counts**: Maximum 10,000 lines per file

### Atomic Operations
All changes are applied atomically - either all files are updated successfully, or all changes are rolled back.

## Troubleshooting

### Common Issues

**Theme not found:**
```bash
ERROR: Theme not found: themes/my-theme
```
- Verify theme name spelling
- Check that theme directory or YAML file exists
- Verify path permissions

**Token not found:**
```bash
ERROR: Token 'my-token' not found in theme files
```
- Use `--create` flag to create new tokens
- Verify token name spelling
- Check if token exists in theme files

**Invalid RGB values:**
```bash
ERROR: RGB values must be between 0 and 255
```
- Ensure RGB values are in range 0-255
- Use comma-separated format: `"R, G, B"`
- Check for typos in values

**Permission denied:**
```bash
ERROR: Cannot write to theme: /config/themes/graphite
```
- Check file/directory permissions
- Ensure Home Assistant is not actively using files
- Run with appropriate user permissions

### Debug Mode

View detailed logging by examining the log file:
```bash
tail -f extras/theme-patcher/logs/graphite_theme_patcher.log
```

## Version Information

```bash
python graphite-theme-patcher.py --version
```

## Security Considerations

- Always backup your themes before running the patcher
- The tool includes built-in security measures for path traversal prevention
- Input validation prevents injection attacks
- File size and count limits prevent DoS attacks
- Atomic operations ensure consistency

## Testing

Run the comprehensive test suite:

```bash
# From theme-patcher directory
python test_theme_patcher.py

# Or from project root
make test-patcher
```

## Development

When modifying the patcher:

1. **Format code**: `make format-python` (from project root)
2. **Run linting**: `make lint-python` (from project root)  
3. **Run tests**: `python test_theme_patcher.py` (from this directory)
4. **Test with real themes**: Verify both directory-based and single-file themes
5. **Verify rollback**: Ensure rollback functionality works correctly
6. **Update documentation**: Update this README for any new features

## Contributing

The theme patcher includes comprehensive CI/CD testing:

- **Formatting**: Black code formatting
- **Linting**: Flake8 code quality checks
- **Testing**: Full test suite across Python 3.9-3.12
- **Integration**: Real theme manipulation testing
- **YAML validation**: Automated theme file validation

## License

MIT License - See project root for full license text.