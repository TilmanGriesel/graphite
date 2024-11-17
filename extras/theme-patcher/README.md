## Graphite Theme Patcher (GTP)

This guide helps you easily customize the primary color in the Graphite theme using a simple patching script. The script modifies the `token-rgb-primary` value in YAML theme files based on your chosen RGB color.

**Note:** This patch is for temporary customization. Any updates to the theme will overwrite your changes unless automated.

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/graphite_theme_patcher_demo.gif"/><br/></p>

---

### **Step 1: Get the patcher**

1. Save the script file `theme-primary-color-patcher.py` in your `/config/scripts` folder.

   - **No folder?** Create one manually first.
   - Prefer another location? Don't forget to update references in the following steps.

   **Quick Copy-Paste Command (Terminal):**

   ```bash
   wget -P /config/scripts https://raw.githubusercontent.com/TilmanGriesel/graphite/refs/heads/main/extras/theme-patcher/graphite-theme-patcher.py
   ```

---

### **Step 2: Add a custom shell command**

**Important:** Only use this patcher if you understand the script's functionality. It includes safeguards to prevent unintended file changes, but reviewing open-source scripts is always wise.

1. Open your Home Assistant `configuration.yaml` file.
1. Add the following `shell_command` entry:
   ```yaml
   shell_command:
     patch_graphite_theme_primary_color: "python3 /config/scripts/graphite-theme-patcher.py {{ rgb_value }}"
   ```
1. Save and restart Home Assistant.

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

---

### **How to use it**

1. Open the new script.
1. Select your desired color using the color picker or input RGB values directly.
1. Run the script on a dashboard or trigger it via automation. It will:
   1. Install graphite updates
   2. Apply your chosen color to the theme
   3. Reload themes for immediate changes

---

### **Advanced usage**

For developers or advanced users:

**Command line execution:**

```bash
python3 graphite-theme-patcher.py <RGB_VALUE> [--token TOKEN_NAME]
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

**Arguments:**

- `RGB_VALUE`: Required. Comma-separated RGB values or 'None' to skip modification
- `--token`: Optional. Token name to update (default: "token-rgb-primary")

**Results:** Your modified YAML might look like this:

```yaml
token-rgb-primary: 0,230,226 # Modified via Graphite theme patcher - 2024-11-17 10:59:12
```

**Error handling:**

- Invalid RGB values will raise a validation error
- Invalid token names will raise a validation error
- Missing tokens in YAML files will be logged as errors
- Failed updates are logged to `logs/graphite_theme_patcher.log`

**Notes:**

- The script uses file locking to ensure thread-safe updates
- Updates are performed atomically using temporary files
- All modifications are logged with timestamps
- The script will process all YAML files in the specified directory recursively
