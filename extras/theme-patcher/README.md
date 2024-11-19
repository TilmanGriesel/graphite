## Graphite Theme Patcher

Customize the Graphite theme's primary color and more without needing to fork the project by using the [Graphite Theme Patcher](https://github.com/TilmanGriesel/graphite/blob/main/extras/theme-patcher/README.md). This tool is designed for advanced users with technical expertise and experience in script and config modification.

---

This tool simplifies customizing the Graphite theme with a straightforward patch script. The basic version of the script adjusts the accent or primary color of Graphite to match your taste.

You can customize further by replacing specific tokens to suit your preferences. While this approach isn’t recommended for beginners, tinkerers are very welcome to explore all the possibilities.

**Important:** This patch provides temporary customization. Theme updates will overwrite your changes unless you implement automation.

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/graphite_theme_patcher_demo_accent.gif"/></p>

## Installation

### **Step 1: Get the patcher**

Download the `graphite-theme-patcher.py` script to your `/config/scripts` folder.

- **No folder?** Create one manually first.
- Prefer another location? Don't forget to update references in the following steps.

**Quick Copy-Paste Command (Terminal):**

```bash
wget -P /config/scripts https://raw.githubusercontent.com/TilmanGriesel/graphite/refs/heads/main/extras/theme-patcher/graphite-theme-patcher.py
```

---

### **Step 2: Add a custom shell command**

1. Open your Home Assistant `configuration.yaml` file.
1. Add the following `shell_command` entry:

   ```yaml
   shell_command:
     patch_graphite_theme_primary_color: "python3 /config/scripts/graphite-theme-patcher.py {{ rgb_value }}"
   ```

1. **Save and restart** Home Assistant.

**Important:** Only use this patcher if you understand the script's functionality. It includes safeguards to prevent unintended file changes, but reviewing open-source scripts is always wise.

Need help with shell commands? Check the [official docs](https://www.home-assistant.io/integrations/shell_command/).

---

### **Step 3: Create a script**

Use Home Assistant's [script](https://my.home-assistant.io/redirect/scripts/) interface or paste this YAML into a new script. Update the `device_id` for your Graphite installation.

```yaml
alias: Update & Patch Graphite Theme
icon: mdi:palette-swatch
description: Customize the Graphite theme's primary color. Read more: https://github.com/TilmanGriesel/graphite/tree/main/extras/theme-patcher
fields:
  user_primary_color:
    selector:
      color_rgb: {}
    default:
      - 229
      - 145
      - 9
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
  - action: frontend.reload_themes
    data: {}
```

## **How to use it**

1. Open the new script.
1. Select your desired color using the color picker or input RGB values directly.
1. Run the script on a dashboard or trigger it via automation. It will:
   1. Install graphite updates
   2. Apply your chosen color to the theme
   3. Reload themes for immediate changes

---

## **Expert usage**

You will probably be fine with the basic installation mentioned earlier and don't need to read any further. However, what follows is just a starting point for exploration, see it as your launchpad into the inner workings of the patcher and its possibilities. The documentation is not complete, but it gives you the tools to dive in, study the RGB and size tokens, and tweak them to your heart's content. From here on out, it's uncharted territory.

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/graphite_theme_patcher_demo_advanced.gif"/></p>

### **Expert 1: Add custom advanced shell command**

1. Open your Home Assistant `configuration.yaml` file.
1. Add the following `shell_command` entry:

   ```yaml
   shell_command:
     patch_theme: "python3 /config/dev/graphite/extras/theme-patcher/graphite-theme-patcher.py --theme {{ theme }} --token {{ token }} --type {{ type }} {{ token_value }}"
   ```

1. **Save and restart** Home Assistant.

### **Expert 2: Create a script**

```yaml
alias: Update & Patch Graphite Theme (Advanced)
icon: mdi:dev-to
description: Advanced Graphite theme customization. Read more: https://github.com/TilmanGriesel/graphite/tree/main/extras/theme-patcher
fields:
  user_primary_color:
    selector:
      color_rgb: {}
    default:
      - 229
      - 145
      - 9
    name: Primary Color
    required: true
    description: Choose your custom primary color (RGB format).
  user_radius_large:
    selector:
      number:
        min: 0
        max: 100
        step: 4
    name: "Large Radius "
    description: Choose your custom large radius.
    default: 18
    required: true
sequence:
  - action: update.install
    target:
      device_id: 510699c015423c5fe6211eccfc3fe364
    data: {}
  - action: shell_command.patch_theme
    data:
      theme: graphite
      token: token-rgb-primary
      type: rgb
      token_value: "{{ user_primary_color | join(',') }}"
  - action: shell_command.patch_theme
    data:
      theme: graphite
      token: token-size-radius-large
      type: radius
      token_value: "{{ user_radius_large }}"
  - action: frontend.reload_themes
    data: {}
```

### Command line execution

```bash
usage: graphite-theme-patcher.py [-h] [--version] [--token TOKEN] [--type {rgb,size,opacity,radius,generic}] [--theme THEME]
                                 [--path PATH]
                                 [value]

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
```

**Basic example:**

```bash
python3 graphite-theme-patcher.py "255,158,0"
```

**Advanced examples:**

```bash
# Update a specific token
python3 graphite-theme-patcher.py "255,158,0" --token "token-color-feedback-info"

# Update the default primary token
python3 graphite-theme-patcher.py "0,230,226"
```

**Requirements:**

- Access to `/config/themes/graphite`
- Write permissions for YAML files
- Valid RGB values (three integers between 0–255)
- Valid token names (letters, numbers, and hyphens only)

**Results:** Your modified YAML might look like this:

```yaml
token-rgb-primary: 0,230,226 # Modified via Graphite theme patcher - 2024-11-17 10:59:12
```

**Error handling:**

- Invalid values will raise a validation error
- Invalid token names will raise a validation error
- Missing tokens in YAML files will be logged as errors
- Failed updates are logged to `logs/graphite_theme_patcher.log`

**Notes:**

- The script uses file locking to ensure thread-safe updates
- Updates are performed atomically using temporary files
- All modifications are logged with timestamps
- The script will process all YAML files in the specified directory recursively
