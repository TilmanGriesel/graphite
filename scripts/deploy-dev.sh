#!/bin/bash

# Remote Dev Deploy Script for Graphite Theme
# Deploys theme files and patcher to a remote Home Assistant instance
#
# Usage: ./scripts/deploy-dev.sh
# 
# Prerequisites:
# - Remote Home Assistant instance mounted at /Volumes/config
# - Ensure the mount point is accessible before running

set -e

# Configuration
REMOTE_CONFIG_PATH="/Volumes/config"
REMOTE_THEMES_PATH="$REMOTE_CONFIG_PATH/themes/graphite"
REMOTE_SCRIPTS_PATH="$REMOTE_CONFIG_PATH/scripts"
LOCAL_THEMES_PATH="themes"
LOCAL_PATCHER_PATH="extras/theme-patcher/graphite-theme-patcher.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Graphite Theme Remote Dev Deploy${NC}"
echo "================================================"

# Check if remote config path is mounted
if [ ! -d "$REMOTE_CONFIG_PATH" ]; then
    echo -e "${RED}Error: Remote config path not found: $REMOTE_CONFIG_PATH${NC}"
    echo -e "${YELLOW}Please ensure your Home Assistant instance is mounted at $REMOTE_CONFIG_PATH${NC}"
    exit 1
fi

# Check if local theme files exist
if [ ! -d "$LOCAL_THEMES_PATH" ]; then
    echo -e "${RED}Error: Local themes directory not found: $LOCAL_THEMES_PATH${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if patcher exists
if [ ! -f "$LOCAL_PATCHER_PATH" ]; then
    echo -e "${RED}Error: Theme patcher not found: $LOCAL_PATCHER_PATH${NC}"
    exit 1
fi

echo -e "${BLUE}Deployment Configuration:${NC}"
echo "  Remote config: $REMOTE_CONFIG_PATH"
echo "  Remote themes: $REMOTE_THEMES_PATH" 
echo "  Remote scripts: $REMOTE_SCRIPTS_PATH"
echo "  Local themes: $LOCAL_THEMES_PATH"
echo "  Local patcher: $LOCAL_PATCHER_PATH"
echo

# Create remote directories if they don't exist
echo -e "${BLUE}Creating remote directories...${NC}"

if [ ! -d "$REMOTE_THEMES_PATH" ]; then
    echo "  Creating $REMOTE_THEMES_PATH"
    mkdir -p "$REMOTE_THEMES_PATH"
fi

if [ ! -d "$REMOTE_SCRIPTS_PATH" ]; then
    echo "  Creating $REMOTE_SCRIPTS_PATH"
    mkdir -p "$REMOTE_SCRIPTS_PATH"
fi

# Deploy theme files
echo -e "${BLUE}Deploying theme files...${NC}"
THEME_FILES_COPIED=0

for theme_file in "$LOCAL_THEMES_PATH"/*.yaml; do
    if [ -f "$theme_file" ]; then
        filename=$(basename "$theme_file")
        echo "  Copying $filename"
        cp "$theme_file" "$REMOTE_THEMES_PATH/"
        ((THEME_FILES_COPIED++))
    fi
done

echo -e "${GREEN}  Copied $THEME_FILES_COPIED theme files${NC}"

# Deploy theme patcher
echo -e "${BLUE}Deploying theme patcher...${NC}"
echo "  Copying graphite-theme-patcher.py"
cp "$LOCAL_PATCHER_PATH" "$REMOTE_SCRIPTS_PATH/"
echo -e "${GREEN}  Theme patcher deployed${NC}"

# Set executable permissions on the patcher
chmod +x "$REMOTE_SCRIPTS_PATH/graphite-theme-patcher.py"

# Display deployment summary
echo
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "================================================"
echo -e "${BLUE}Deployed Files:${NC}"
echo "  Themes: $REMOTE_THEMES_PATH/"
ls -la "$REMOTE_THEMES_PATH"/*.yaml 2>/dev/null | sed 's/^/    /' || echo "    (No theme files found)"
echo
echo "  Patcher: $REMOTE_SCRIPTS_PATH/graphite-theme-patcher.py"
if [ -f "$REMOTE_SCRIPTS_PATH/graphite-theme-patcher.py" ]; then
    ls -la "$REMOTE_SCRIPTS_PATH/graphite-theme-patcher.py" | sed 's/^/    /'
fi

echo
echo -e "${BLUE}Usage on Remote Home Assistant:${NC}"
echo "  cd /config/scripts"
echo "  python3 graphite-theme-patcher.py --help"
echo "  python3 graphite-theme-patcher.py --recipe /config/themes/graphite/recipes/recipe_hello_world.yaml"
echo
echo -e "${YELLOW}Note: Don't forget to restart Home Assistant to load new theme files!${NC}"