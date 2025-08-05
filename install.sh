#!/bin/bash

# ROS2 Bag Info Nautilus Extension Installer
# Installs the extension to the user's Nautilus Python extensions directory

set -e

EXTENSION_NAME="ros2_bag_info.py"
INSTALL_DIR="$HOME/.local/share/nautilus-python/extensions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing ROS2 Bag Info Nautilus Extension..."

# Check if nautilus-python is installed
if ! python3 -c "import gi; gi.require_version('Nautilus', '4.0')" 2>/dev/null; then
    echo "Error: nautilus-python is not installed."
    echo "Please install it first:"
    echo "  sudo apt install nautilus-python"
    exit 1
fi

# Check if PyYAML is available
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Error: PyYAML is not installed."
    echo "Please install it first:"
    echo "  sudo apt install python3-yaml"
    exit 1
fi

# Create the extensions directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy the extension file
if [ -f "$SCRIPT_DIR/$EXTENSION_NAME" ]; then
    cp "$SCRIPT_DIR/$EXTENSION_NAME" "$INSTALL_DIR/"
    echo "Extension copied to $INSTALL_DIR/$EXTENSION_NAME"
else
    echo "Error: $EXTENSION_NAME not found in $SCRIPT_DIR"
    exit 1
fi

# Set executable permissions
chmod +x "$INSTALL_DIR/$EXTENSION_NAME"

echo "Installation complete!"
echo ""
echo "To activate the extension:"
echo "1. Restart Nautilus: killall nautilus && nautilus &"
echo "2. Right-click on any ROS2 bag directory to see the 'ROS2 Bag Info' menu"
echo ""
echo "Note: The extension only works with ROS2 bag directories that contain:"
echo "  - metadata.yaml file"
echo "  - At least one .mcap or .db3 file"
