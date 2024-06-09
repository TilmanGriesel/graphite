<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/main/docs/logo_s.svg" width="240" alt="Logo Graphite Theme"/></p>
<h3 align="center">Graphite Theme for Home Assistant</h3>
<p align="center">
	<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme"><img src="https://img.shields.io/badge/hacs-default-blue?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/stargazers"><img src="https://img.shields.io/github/stars/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/issues"><img src="https://img.shields.io/github/issues/tilmangriesel/graphite?colorA=1F2229&colorB=5c5e70&style=for-the-badge"></a>
</p>

<p align="center"><img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/main/docs/screenshots/main.png"/><br/></p>

**Graphite** is a contemporary theme that features both a calming dark color scheme and a bright, clean light theme. It features native device fonts and a cohesive design language across all Home Assistant interfaces, including the administration interface and code editors.
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

## Personal note
Hi, my name is Tilman, nice to meet you! I am a product designer and software engineer by trade and I live in an old 16th century house that I'm trying hard to make smart. 
 
I created this theme to improve my own, and my better halfs quality of life. Currently, it is not possible to customize every aspect of home assistant using a simple theme file. However, my goal is to provide an uncomplicated and convenient way for new or unexperienced users avoiding more advanced and in-depth styling methods.

---

<p align="center">
Inspired by many of the awesome home assistant community themes and contributors.<br>Thank you for your creativity, dedication and inspiration!
</p>
