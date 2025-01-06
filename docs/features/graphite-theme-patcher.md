# Graphite Theme Patcher

Effortlessly customize Graphite's primary color and more **without forking the project** using the **Graphite Theme Patcher**. Designed for advanced users, this tool simplifies theme adjustments with minimal hassle.

![graphite_theme_patcher_demo_accent](/assets/gif/graphite_theme_patcher_demo_accent.gif)

## Overview

The Graphite Theme Patcher allows you to:

- Adjust the primary accent color.
- Replace specific theme tokens for deeper customization.

This tool is ideal for tinkerers and power users familiar with script and configuration editing.

**🎨 Showcase your Theme Patcher setup** and join the discussion at: https://github.com/TilmanGriesel/graphite/discussions/76

::: info
Changes made with this patcher are **temporary**. Updates to the Graphite theme will overwrite customizations unless automated workflows are in place.
:::

## Installation

### **Step 1: Download the Patcher**

Save the `graphite-theme-patcher.py` script to your `/config/scripts` directory. If the directory doesn't exist, create it.

**Quick Command:**

```bash
wget -O /config/scripts/graphite-theme-patcher.py https://raw.githubusercontent.com/TilmanGriesel/graphite/refs/heads/main/extras/theme-patcher/graphite-theme-patcher.py
```

---

### **Step 2: Add a Shell Command**

1. Open your Home Assistant `configuration.yaml` file.
2. Add the following entry under `shell_command`:

   ```yaml
   shell_command:
     patch_graphite_theme_primary_color: "python3 /config/scripts/graphite-theme-patcher.py --value '{{ rgb_value }}'"
   ```

3. Save and restart Home Assistant.

---

### **Step 3: Create a Home Assistant Script**

Use the Home Assistant UI or add this YAML to a new script for adjusting the theme's primary color:

```yaml
alias: Update & Patch Graphite Theme
icon: mdi:palette-swatch
description: Customize the primary color of the Graphite theme.
fields:
  user_primary_color:
    selector:
      color_rgb: {}
    default:
      - 224
      - 138
      - 0
    name: Primary Color
    required: true
    description: Choose your custom primary color (RGB format).
sequence:
  - action: update.install
    target:
      device_id: 510699c015423c5fe6211eccfc3fe364
    data: {}
  - action: shell_command.patch_graphite_theme_primary_color
    data:
      rgb_value: "{{ user_primary_color | join(',') }}"
    alias: Set Primary Color
  - action: frontend.reload_themes
    data: {}
```

## Usage

1. Open the script in Home Assistant.
2. Choose your desired color using the color picker or input RGB values.
3. Run the script to:
   1. Apply your chosen color.
   2. Reload the Graphite theme for immediate updates.

::: info
**Review the script's functionality to ensure safe usage**. While safeguards are in place, it's good practice to understand any changes being applied.
:::

## Advanced Customization

If your main goal was just to update the primary color, the earlier steps should do the trick. But if you're curious to see what else the patcher can do, this is your chance to experiment and customize to your heart’s content. The documentation isn't super detailed, but it gives you enough to start playing around with RGB and size tokens to see what's possible. From here, it's all about exploring and having fun in uncharted territory.

**🎨 Showcase your Theme Patcher setup** and join the discussion at: https://github.com/TilmanGriesel/graphite/discussions/76

![graphite_theme_patcher_demo_advanced](/assets/gif/graphite_theme_patcher_demo_advanced.gif)

### Advanced Shell Command Example

Add a new shell command to your `configuration.yaml`:

```yaml
shell_command:
  patch_theme: "python3 /config/scripts/graphite-theme-patcher.py --theme '{{ theme }}' --token '{{ token }}' --type '{{ type }}' --create --value '{{ value }}'"
```

Save and restart Home Assistant.

---

### Advanced Script Example

```yaml
alias: Update & Patch Graphite Theme (Advanced)
description: Advanced customization of the Graphite theme.
icon: mdi:dev-to
fields:
  user_primary_color:
    selector:
      color_rgb: {}
    default:
      - 224
      - 138
      - 0
    name: Primary Color
    required: true
    description: Choose your custom primary color (RGB format).
  user_radius_large:
    selector:
      number:
        min: 0
        max: 100
        step: 3
    name: "Large Radius "
    description: Choose your custom large radius.
    default: 18
    required: true
sequence:
  - action: shell_command.patch_theme
    data:
      theme: graphite
      token: token-rgb-primary
      type: rgb
      value: "{{ user_primary_color | join(',') }}"
    alias: Set Primary Color
  - action: shell_command.patch_theme
    data:
      theme: graphite
      token: token-size-radius-large
      type: radius
      value: "{{ user_radius_large }}"
    alias: Set Radius
  - action: shell_command.patch_theme
    data:
      theme: graphite
      type: card-mod
      token: card-mod-root
      value: .header{display:none;}#view{padding:0!important;height:100vh!important;}
    alias: Hide Header
    enabled: false
  - action: shell_command.patch_theme
    data:
      theme: graphite
      type: card-mod
      token: card-mod-root
      value: .header{}
    alias: Show Header
    enabled: false
  - action: shell_command.patch_theme
    data:
      theme: graphite
      type: generic
      token: my-token
      value: url("/local/animated-icons/clear-night.svg")
    alias: Set Custom Generic
    enabled: false
  - action: frontend.reload_themes
    data: {}
```

## Command-Line Usage

Run the patcher directly for quick edits:

```bash
python3 graphite-theme-patcher.py "255,158,0"
```

### Options

```bash
usage: graphite-theme-patcher.py [-h] [--version] [--token TOKEN] [--type {rgb,size,opacity,radius,generic}] [--theme THEME] [--path PATH] [--create] [value]

Update token values in theme files. (v1.2.0)

positional arguments:
  value                 Value to set or 'None' to skip

options:
  -h, --help            show this help message and exit
  --version             Show version information and exit
  --token TOKEN         Token to update (default: token-rgb-primary)
  --type {rgb,size,opacity,radius,generic}
                        Type of token (default: rgb)
  --theme THEME         Theme name (default: graphite)
  --path PATH           Base path for themes directory (default: /config/themes)
  --create              Create token if it doesn't exist
```

---

- **Basic Example**: Update the primary color:
  ```bash
  python3 graphite-theme-patcher.py "0,230,226"
  ```
- **Advanced Example**: Modify specific tokens:
  ```bash
  python3 graphite-theme-patcher.py "255,158,0" --token "token-color-feedback-info"
  ```

## Requirements

- Access to `/config/themes/graphite`.
- Write permissions for YAML files.
- Valid input values (e.g., RGB values between 0–255).

## Error Handling

- **Invalid Inputs**: Triggers validation errors.
- **Missing Tokens**: Logs errors but continues execution.
- **Failed Updates**: Logged in `logs/graphite_theme_patcher.log`.
