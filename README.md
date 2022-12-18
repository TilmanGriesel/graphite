## graphite Home Assistant Theme
graphite - A minimalist and clean dark theme for [Home Assistant](https://www.home-assistant.io)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme) ![ISSUES](https://img.shields.io/github/issues-raw/TilmanGriesel/graphite?style=flat-square)

![](https://raw.githubusercontent.com/TilmanGriesel/graphite/main/docs/screenshots/demo.png)

## Installation

#### Installation
1. Copy the `themes` folder into your home-assistant config folder
1. Set the theme folder in you `configuration.yaml`

```yaml
frontend:
  themes: !include_dir_merge_named themes
```

3. Restart Home Assistant
4. Select the `graphite` theme in your profile

## Credits
Inspired by the [noctis theme](https://github.com/aFFekopp/noctis)
