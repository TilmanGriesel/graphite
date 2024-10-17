#!/usr/bin/env python3

import os

THEMES_DIR = "themes/"
LIGHT_THEME = THEMES_DIR + "graphite-light.yaml"
DARK_THEME = THEMES_DIR + "graphite.yaml"
OUTPUT_THEME = THEMES_DIR + "graphite-auto.yaml"

def read_theme_file(file_path, indent_level):
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # Skip the first line
        return ''.join(f"{indent_level}{line}" for line in lines)

# Create YAML content
output_content = """Graphite Auto:
  modes:
    light:
"""
output_content += read_theme_file(LIGHT_THEME, "      ")
output_content += "    dark:\n"
output_content += read_theme_file(DARK_THEME, "      ")

# Write combined content to output
with open(OUTPUT_THEME, 'w') as output_file:
    output_file.write(output_content)

print(f"Combined theme saved to {OUTPUT_THEME}")
