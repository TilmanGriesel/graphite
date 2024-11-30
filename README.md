<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/logo.png" width="240" alt="Logo Graphite Theme"/></p>
<h3 align="center">Graphite Theme for Home Assistant</h3>
<p align="center">
	<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme"><img src="https://img.shields.io/badge/hacs-default-blue?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/stargazers"><img src="https://img.shields.io/github/stars/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/issues"><img src="https://img.shields.io/github/issues/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
</p>

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/dark.png"/></p>
<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/light.png"/></p>

**Graphite** is a modern theme that offers a soothing dark mode alongside a bright, clean light mode. It uses native device fonts and maintains a unified design language across all Home Assistant interfaces, from the admin panel to code editors.

## Installation
Easily install Graphite via [HACS](https://hacs.xyz), the Home Assistant Community Store.

[![Open Graphite in your Home Assistant instance](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite)

<details>
<summary>Prefer manual installation? Read manual installation instructions</summary>
	
### Manual Guide
	
1. Copy the `themes` folder into your home-assistant config folder
1. Set the theme folder in you `configuration.yaml`

```yaml
frontend:
  themes: !include_dir_merge_named themes
```

3. Restart Home Assistant
4. Select the `Graphite` theme in your profile
</details>

## Examples

If you're curious about the cards from my screenshot, you can [check out my examples](https://github.com/TilmanGriesel/graphite/blob/main/examples/README.md).

## Custom primary color & more

Customize the Graphite theme's primary color and more without needing to fork the project by using the [Graphite Theme Patcher](https://github.com/TilmanGriesel/graphite/blob/main/extras/theme-patcher/README.md). This tool is designed for advanced users with technical expertise and experience in script and config modification. For detailed setup instructions, refer to the patcher's README.

## Modifying the theme

I've created a small token abstraction and a script to help maintain Graphite's consistency across theme variants and simplify updates. You'll find the source components in the src folder. After making any changes, use the theme_assembler Python 3 script in the tools directory to regenerate the theme files. Avoid directly modifying the files in the themes directory. This setup can also serve as a great starting point for building your own themes in no time.

## Personal note

Hi there, I'm Tilman, nice to meet you! I'm a product designer and software engineer with a love for blending technology, art, design, and open-source projects. I live in a cozy 16th-century home that I'm gradually turning into a smarter, more connected space.

I started designing this theme in 2022 to make our smart home more intuitive and visually harmonious for my partner Sophia and me. The goal was to create an experience that's both user-friendly and aesthetically pleasing, without needing extra complexity or plugins.

I hope this theme makes your Home Assistant experience even better! If you love it, leaving a star would mean a lot and help others find it too.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/griesel)

---

<p align="center">
	<a href="https://github.com/TilmanGriesel/graphite/actions/workflows/theme-verification.yaml"><img src="https://img.shields.io/github/actions/workflow/status/tilmangriesel/graphite/theme-verification.yaml?style=for-the-badge&label=Verification"></a>
	<a href="https://github.com/TilmanGriesel/graphite/actions/workflows/HACS_Action.yml"><img src="https://img.shields.io/github/actions/workflow/status/tilmangriesel/graphite/HACS_Action.yml?style=for-the-badge&label=HACS"></a>
</p>

<p align="center">
Inspired by many of the awesome home assistant community themes and contributors.<br>Thank you for your creativity, dedication and inspiration!
</p>
