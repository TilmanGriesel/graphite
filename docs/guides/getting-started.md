# Graphite Theme Quickstart

Graphite is a sleek and modern Home Assistant theme with both a soothing dark mode and a clean, bright light mode. It's easy to install and customize via HACS, the Home Assistant Community Store.

![graphite_theme_patcher_demo_accent](/assets/screenshot/dark.png)
![graphite_theme_patcher_demo_accent](/assets/screenshot/light.png)

## Installation via HACS

Follow these steps to install the Graphite theme using HACS:

### Step 1: Install HACS

If you haven't already, [install HACS](https://hacs.xyz/docs/use/) by following the official guide.

### Step 2: Add the Graphite Theme Repository

[![Open Graphite in your Home Assistant instance](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite)

#### Alternatively
1. Open the HACS interface in Home Assistant.
2. Search for **Graphite Theme** or use the direct link below:
3. Click **Install** to add the theme to your setup.

### Step 3: Configure Your Theme Directory

Ensure your `configuration.yaml` is set up to include custom themes:

```yaml
frontend:
  themes: !include_dir_merge_named themes
```

### Step 4: Restart Home Assistant

Restart your Home Assistant instance to apply changes.

### Step 5: Select the Graphite Theme

1. Go to your **User Profile** in Home Assistant.
2. Under **Themes**, select `Graphite` (Light or Dark) from the dropdown menu.


## Manual Installation

For manual installation, you can follow these steps:

1. Download and copy the `themes` folder into your Home Assistant configuration directory.
2. Add the following to your `configuration.yaml`:
   ```yaml
   frontend:
     themes: !include_dir_merge_named themes
   ```
3. Restart Home Assistant.
4. Choose the `Graphite` theme from your profile.

---

Enjoy the Graphite theme? 🌟 Consider [leaving a star](https://github.com/TilmanGriesel/graphite/stargazers) on GitHub to support its development! 
