<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/logo.png" width="240" alt="Logo Graphite Theme"/></p>
<h3 align="center">Graphite Theme for Home Assistant</h3>
<p align="center">
	<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme"><img src="https://img.shields.io/badge/hacs-default-blue?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/stargazers"><img src="https://img.shields.io/github/stars/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/issues"><img src="https://img.shields.io/github/issues/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
</p>

**Graphite** is a modern theme that offers a soothing dark mode alongside a bright, clean light mode. It uses native device fonts and maintains a unified design language across all Home Assistant interfaces, from the admin panel to code editors.

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/public/assets/screenshot/dark.png"/></p>
<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/public/assets/screenshot/light.png"/></p>

## Installation

Start quickly by following the quickstart guide at https://graphite.tilmangriesel.com

[![Open Graphite in your Home Assistant instance](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite)


<details><summary>Or read the setup instructions here</summary>

#### Step 1: Install HACS
If you haven't already, [install HACS](https://hacs.xyz/docs/use/) by following the official guide.

#### Step 2: Add the Graphite Theme Repository

[Open Graphite in your Home Assistant HACS instance](https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite)

##### Alternatively
1. Open the HACS interface in Home Assistant.
2. Search for **Graphite Theme** or use the direct link below:
3. Click **Install** to add the theme to your setup.

### Step 3: Configure your theme directory

Ensure your `configuration.yaml` is set up to include custom themes:

```yaml
frontend:
  themes: !include_dir_merge_named themes
```

#### Step 4: Restart Home Assistant
Restart your Home Assistant instance to apply changes.

#### Step 5: Select the Graphite Theme

1. Go to your **User Profile** in Home Assistant.
2. Under **Themes**, select `Graphite` (Light or Dark) from the dropdown menu.


### Manual Installation
For manual installation, you can follow these steps:

1. Download and copy the `themes` folder into your Home Assistant configuration directory.
2. Add the following to your `configuration.yaml`:
   ```yaml
   frontend:
     themes: !include_dir_merge_named themes
   ```
3. Restart Home Assistant.
4. Choose the `Graphite` theme from your profile.

</details>

---

### Personalize Graphite
Customize the Graphite theme's primary color and more without needing to fork the project by using the [Graphite Theme Patcher](https://graphite.tilmangriesel.com/features/graphite-theme-patcher.html). This tool is designed for advanced users with technical expertise and experience in script and config modification. For detailed setup instructions, refer to the patcher's README.

---

### Theme Development Kit
I've created token abstraction and a script to help maintain Graphite's consistency across theme variants and simplify updates. This setup can also serve as a great starting point for building your own themes in no time. [Theme Development Kit](https://graphite.tilmangriesel.com/features/graphite-theme-development-kit.html)

---

### Examples
If you're curious about the cards from my screenshot, you can [check out my examples](https://graphite.tilmangriesel.com/guides/card-examples.html).

---

### Personal note
Hi there, I'm Tilman, nice to meet you! I'm a product designer and software engineer with a love for blending technology, art, design, and open-source projects. I live in a cozy 16th-century home that I'm gradually turning into a smarter, more connected space.

I started designing this theme in 2022 to make our smart home more intuitive and visually harmonious for my partner Sophia and me. The goal was to create an experience that's both user-friendly and aesthetically pleasing, without needing extra complexity or plugins.

I hope this theme makes your Home Assistant experience even better! If you love it, [leaving a star](https://github.com/TilmanGriesel/graphite) would mean a lot and help others find it too.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/griesel)

---

<p align="center">
	<a href="https://github.com/TilmanGriesel/graphite/actions/workflows/theme-verification.yaml"><img src="https://img.shields.io/github/actions/workflow/status/tilmangriesel/graphite/theme-verification.yaml?style=for-the-badge&label=Verification"></a>
	<a href="https://github.com/TilmanGriesel/graphite/actions/workflows/HACS_Action.yml"><img src="https://img.shields.io/github/actions/workflow/status/tilmangriesel/graphite/HACS_Action.yml?style=for-the-badge&label=HACS"></a>
</p>

<p align="center">
Inspired by many of the awesome home assistant community themes and contributors.<br>Thank you for your creativity, dedication and inspiration!
</p>
