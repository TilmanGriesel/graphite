## Home Dashboard Card Examples
I've been getting a lot of questions about my configurations and card style, so I thought I'd share them here. If you have any questions, don't hesitate to open an issue. Just a heads-up: you might need to tweak the configurations a bit to fit your setup.

---

### Clock Card
It’s a digital-clock and card-mod (you can get both in the HACS) with the following configuration.

Custom Cards:
 - https://github.com/wassy92x/lovelace-digital-clock
 - https://github.com/thomasloven/lovelace-card-mod

```yaml
type: custom:digital-clock
locale: de
dateFormat:
  weekday: long
  day: 2-digit
  month: long
timeFormat:
  hour: 2-digit
  minute: 2-digit
card_mod:
  style: |
    ha-card {
      padding: 16px 0 !important;
    }
    .first-line {
      font-weight: 600 !important;
      font-size: 32px !important;
      color: var(--primary-text-color) !important;
    }
    .second-line {
      font-weight: 500 !important;
      font-size: 16px !important;
      color: var(--secondary-text-color) !important;
    }
```

---

### Temperature Card

It’s a mini-graph-card and card-mod (you can get both in the HACS) with the following configuration. You also need a binary night sensor which is a time of day or TOD sensor.

Custom Cards:
 - https://github.com/kalkih/mini-graph-card
 - https://github.com/thomasloven/lovelace-card-mod

```yaml
type: custom:mini-graph-card
name: Temperatur
line_width: 2
points_per_hour: 0.5
animate: false
entities:
  - entity: sensor.your_sensor_goes_here
    name: Kitchen
  - entity: sensor.aqara_weather_bedroom_temperature
    name: Bedroom
  - entity: sensor.aqara_weather_bathroom_temperature
    name: Bathroom
  - entity: sensor.aqara_weather_wood_storage_temperature
    name: Storage
  - entity: binary_sensor.night
    name: Night
    color: rgba(0, 0, 0, 0.8)
    y_axis: secondary
    aggregate_func: min
    show_state: true
    show_line: false
    show_points: false
state_map:
  - value: 'off'
    label: Day
  - value: 'on'
    label: Night
show:
  labels: true
  labels_secondary: false
card_mod:
  style: |
    .name > span {
      font-size: 14px;
      opacity: 1 !important;
      color: var(--secondary-text-color) !important;
    }
```

---

### Pollenflug Germany (ePIN)
This card utilizes data from the Elektronisches Polleninformationsnetzwerk (ePIN) REST API: https://epin.lgl.bayern.de/pollenflug-aktuell.

To retrieve data from ePIN, you first need to set up a REST sensor in your `/homeassistant/configuration.yaml` file. Adjust the configuration as needed:

```yaml
sensor:
  - platform: rest
    scan_interval: 60
    name: "epin_DEGARM"
    resource: 'https://epin.lgl.bayern.de/api/measurements?from={{now().timestamp()}}&to={{now().timestamp() - 86400}}&pollen=Poaceae&locations=DEGARM'
    value_template: '{{ value_json.measurements[0].data[-1].value }}'
    unit_of_measurement: "Pollen/m³"
    icon: 'mdi:flower-pollen'
  - platform: rest
    scan_interval: 60
    name: "epin_DEMUNC"
    resource: 'https://epin.lgl.bayern.de/api/measurements?from={{now().timestamp()}}&to={{now().timestamp() - 86400}}&pollen=Poaceae&locations=DEMUNC'
    value_template: '{{ value_json.measurements[0].data[-1].value }}'
    unit_of_measurement: "Pollen/m³"
    icon: 'mdi:flower-pollen'
  - platform: statistics
    name: stat_epin_DEGARM
    entity_id: sensor.epin_DEGARM
    state_characteristic: average_linear
    max_age:
      hours: 5
  - platform: statistics
    name: stat_epin_DEMUNC
    entity_id: sensor.epin_DEMUNC
    state_characteristic: average_linear
    max_age:
      hours: 5
```

It’s a mini-graph-card and card-mod (you can get both in the HACS) with the following configuration. You also need a binary night sensor which is a time of day or TOD sensor.


Custom Cards:
 - https://github.com/kalkih/mini-graph-card
 - https://github.com/thomasloven/lovelace-card-mod

```yaml
type: custom:mini-graph-card
name: Pollenflug
line_width: 2
points_per_hour: 2
hour24: true
decimals: 0
lower_bound: 0
animate: false
color_thresholds:
  - value: 0
    color: '#04a777'
  - value: 100
    color: '#fb8b24'
  - value: 400
    color: '#d90368'
  - value: 1000
    color: '#820263'
entities:
  - entity: sensor.epin_degarm
    name: Garmisch
  - entity: sensor.epin_demunc
    name: München
  - entity: binary_sensor.night
    name: Nacht
    color: rgba(0, 0, 0, 1)
    y_axis: secondary
    aggregate_func: min
    show_state: true
    show_line: false
    show_points: false
state_map:
  - value: 'off'
    label: Tag
  - value: 'on'
    label: Nacht
show:
  labels: true
  labels_secondary: false
card_mod:
  style: |
    .name > span {
      font-size: 14px;
      opacity: 1 !important;
      color: var(--secondary-text-color) !important;
    }
````