<h3 align="center" style="margin-bottom: 32px">
	<img src="https://raw.githubusercontent.com/TilmanGriesel/graphite/2.0-rework/docs/logo_s.svg" width="270" height="220" alt="Logo Graphite Theme"/><br/>
	Graphite Theme for Home Assistant
</h3>

<p align="center">
  	<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme"><img src="https://img.shields.io/badge/hacs-default-blue?colorA=16181d&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/stargazers"><img src="https://img.shields.io/github/stars/tilmangriesel/graphite?colorA=16181d&colorB=5c5e70&style=for-the-badge"></a>
	<a href="https://github.com/tilmangriesel/graphite/issues"><img src="https://img.shields.io/github/issues/tilmangriesel/graphite?colorA=16181d&colorB=5c5e70&style=for-the-badge"></a>
</p>

## Installation

#### Via HACS (Home Assistant Community Store)
1. Go to the Community Store.
2. Search for `graphite`.
3. Navigate to `graphite`.
4. Press Install.

#### Manual
1. Copy the `themes` folder into your home-assistant config folder
1. Set the theme folder in you `configuration.yaml`

```yaml
frontend:
  themes: !include_dir_merge_named themes
```

3. Restart Home Assistant
4. Select the `graphite` theme in your profile

## Credits
Inspired by the awesome [noctis theme](https://github.com/aFFekopp/noctis)
