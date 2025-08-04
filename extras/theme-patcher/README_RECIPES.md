# Theme Patcher Recipes

Theme Patcher Recipes allow community members to share complete theme customizations easily. Instead of manually applying multiple token changes, users can apply a single recipe file or URL to transform their themes.

## Recipe Format

Recipes are YAML files with the following structure:

```yaml
# Recipe metadata
recipe:
  name: "Recipe Name"                    # Required: Display name
  author: "Author Name"                  # Required: Author name  
  author_url: "https://example.com"     # Optional: Author website/profile
  description: "Recipe description"      # Optional: What the recipe does
  version: "1.0.0"                      # Required: Recipe version
  patcher_version: ">=2.0.0"           # Required: Compatible patcher version
  screenshot_url: "https://example.com/preview.png"  # Optional: Theme preview screenshot
  
  # Target theme variants (Optional: defaults to ["graphite"])
  variants:
    - "graphite"         # Dark theme (themes/graphite.yaml)
    - "graphite-light"   # Light theme (themes/graphite-light.yaml)
    - "graphite-auto"    # Auto theme with light/dark modes (themes/graphite-auto.yaml)
    - "graphite-eink-dark"   # E-ink optimized dark theme
    - "graphite-eink-light"  # E-ink optimized light theme
  
  # Target mode for auto themes
  mode: "all"          # Optional: "light", "dark", "all" (default: "all")

# Patch definitions
patches:
  - token: "token-rgb-primary"
    type: "rgb"
    value: "52, 152, 219"
    description: "Ocean blue primary color"
  
  - token: "token-color-accent"
    type: "generic"
    value: "rgb(46, 204, 113)"
    description: "Complementary teal accent"
```

## Token Types

- `rgb`: RGB color values (comma-separated: "255, 128, 0")
- `generic`: Any value, passed through as-is
- `size`: Pixel values (converted to "Npx" format)
- `opacity`: Decimal 0-1 or percentage values
- `radius`: Border radius pixel values
- `card-mod`: Card-mod CSS properties (automatically quoted)

## Usage

### Apply Recipe from File
```bash
# Apply to default theme specified in recipe
python3 graphite-theme-patcher.py --recipe /path/to/recipe.yaml

# Override theme selection
python3 graphite-theme-patcher.py --recipe /path/to/recipe.yaml --theme graphite-light

# Apply to auto theme with specific mode
python3 graphite-theme-patcher.py --recipe /path/to/recipe.yaml --theme graphite-auto --mode dark
```

### Apply Recipe from URL
```bash  
# Apply recipe from URL
python3 graphite-theme-patcher.py --recipe https://example.com/recipe.yaml

# Override theme and mode
python3 graphite-theme-patcher.py --recipe https://example.com/recipe.yaml --theme graphite-auto --mode light

# Specify custom path
python3 graphite-theme-patcher.py --recipe https://example.com/recipe.yaml --path /config/themes
```

### Options
- `--theme`: Target theme name (default: "graphite")
- `--mode`: For auto themes, target "light", "dark", or "all" (default: "all")
- `--path`: Custom themes directory path (auto-detected by default)

## Community Recipes

### Hello World (Beginner-Friendly)
Perfect starter recipe covering the most important tokens:
```bash
python3 graphite-theme-patcher.py --recipe recipes/recipe_hello_world.yaml --theme graphite-light
```

### Retro 70s Theme
Groovy earth tones and warm colors inspired by 1970s design:
```bash
python3 graphite-theme-patcher.py --recipe recipes/recipe_retro_70s.yaml --theme graphite-light
```

### 3D Graphite Cards
Transform your cards with realistic 3D effects using gradients and subtle highlights (inspired by rgnyldz):
```bash
python3 graphite-theme-patcher.py --recipe recipes/recipe_3d_graphite.yaml
```

### Ocean Blue Theme
Transform your theme with calming ocean blues:
```bash
python3 graphite-theme-patcher.py --recipe recipes/recipe_ocean_blue.yaml
```

### Warm Sunset Theme  
Apply warm sunset colors (dark themes only):
```bash
python3 graphite-theme-patcher.py --recipe recipes/recipe_warm_sunset.yaml --theme graphite
```

## Creating Recipes

1. Create a YAML file with the recipe structure
2. Test with your theme: `python3 graphite-theme-patcher.py --recipe your_recipe.yaml`
3. Share via file or host on a public URL
4. Community members can apply with: `python3 graphite-theme-patcher.py --recipe YOUR_URL`

## Recipe Validation

The patcher validates:
- Required metadata fields
- Patcher version compatibility  
- Patch structure and required fields
- Token value formats based on type

## Security

- URLs are downloaded with timeouts and size limits
- File paths are validated to prevent directory traversal
- Recipe content is validated before execution
- All standard patcher security measures apply