## graphite
Calm and clean dark theme for [Home Assistant](https://www.home-assistant.io)

[![hacs](https://img.shields.io/badge/HACS-Default-blue.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TilmanGriesel&repository=graphite&category=theme) ![STARS](https://img.shields.io/github/stars/TilmanGriesel/graphite?color=green&style=flat-square) ![ISSUES](https://img.shields.io/github/issues-raw/TilmanGriesel/graphite?style=flat-square) ![LASTCOMMIT](https://img.shields.io/github/last-commit/TilmanGriesel/graphite?style=flat-square)

![](https://raw.githubusercontent.com/TilmanGriesel/graphite/main/docs/screenshots/tablet.png)

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
