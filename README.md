<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/logo.png" width="240" alt="Logo Graphite Theme"/></p>
<h3 align="center">Graphite Theme for Home Assistant</h3>
<p align="center">
	<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme"><img src="https://img.shields.io/badge/hacs-default-blue?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/stargazers"><img src="https://img.shields.io/github/stars/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/issues"><img src="https://img.shields.io/github/issues/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
</p>

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/dark.png"/><br/></p>
<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/HEAD/docs/screenshots/light.png"/><br/></p>

**Graphite** is a modern theme that offers a soothing dark mode alongside a bright, clean light mode. It uses native device fonts and maintains a unified design language across all Home Assistant interfaces, from the admin panel to code editors.

## Installation

<details>
<summary>Home Assistant Community Store Guide</summary>
	
### Installation
The [Home Assistant Community Store](https://hacs.xyz), or HACS, is the most convenient and efficient way to install the Graphite theme. HACS acts as a one-stop shop for community-developed extensions for Home Assistant, similar to the Apple App Store or Google Play Store. With just a few clicks, you can easily find and install the Graphite theme within HACS.

### Guideline

1. Ensure you have [HACS installed](https://hacs.xyz/docs/setup/download).
1. Open the Home Assistant Community Store (HACS) by clicking on the `HACS` tab in the side menu.
1. In the HACS store, click on the `Frontend` tab.
1. On the bottom right, click on `Explore & Download Repositories` and use the search bar to search for `Graphite`.
1. Click on the `Graphite` theme in the search results to open the theme's page.
1. On the theme's page, click on the `Download` button.
1. Wait for the installation to complete. This may take a few seconds.
1. Once the installation is complete, open your profile and select `Graphite` in your `Theme` dropdown menu.

That's it! The Graphite theme has been successfully installed and applied to your Home Assistant instance. You will receive notifications in the Home Assistant Community Store (HACS) whenever an update is available for the theme, so you can keep it up to date with the latest improvements and tweaks.

</details>
	
<details>
<summary>Manual Guide</summary>
	
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

## Custom primary color

Customize the Graphite theme's primary color without needing to fork the project by using the [Graphite Theme Patcher](https://github.com/TilmanGriesel/graphite/blob/main/extras/theme-patcher). This tool is designed for advanced users with technical expertise and experience in script and config modification. For detailed setup instructions, refer to the patcher's README.

## Modifying the theme

I've created a small token abstraction and a script to help maintain Graphite's consistency across theme variants and simplify updates. You'll find the source components in the src folder. After making any changes, use the theme_assembler Python 3 script in the tools directory to regenerate the theme files. Avoid directly modifying the files in the themes directory. This setup can also serve as a great starting point for building your own themes in no time.

## Personal note

Hi there, I'm Tilman, nice to meet you! I'm a product designer and software engineer with a love for blending technology, art, design, and open-source projects. I live in a cozy 16th-century home that I'm gradually turning into a smarter, more connected space.

I started designing this theme in 2022 to make our smart home more intuitive and visually harmonious for my partner Sophia and me. The goal was to create an experience that's both user-friendly and aesthetically pleasing, without needing extra complexity or plugins.

I hope this theme makes your Home Assistant experience even better! If you love it, leaving a star would mean a lot and help others find it too.

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/griesel)

---

<p align="center">
Inspired by many of the awesome home assistant community themes and contributors.<br>Thank you for your creativity, dedication and inspiration!
</p>
