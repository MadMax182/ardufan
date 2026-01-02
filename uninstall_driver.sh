#!/bin/bash
# Uninstall ArduFan liquidctl driver

echo "Uninstalling ArduFan liquidctl driver..."
echo "This requires sudo to remove the driver from liquidctl's directory."
echo

# Check if driver exists
if [ -f /usr/lib/python3.13/site-packages/liquidctl/driver/ardufan.py ]; then
    sudo rm /usr/lib/python3.13/site-packages/liquidctl/driver/ardufan.py

    if [ $? -eq 0 ]; then
        echo "Driver uninstalled successfully!"

        # Also remove .pyc cache if it exists
        if [ -f /usr/lib/python3.13/site-packages/liquidctl/driver/__pycache__/ardufan*.pyc ]; then
            sudo rm /usr/lib/python3.13/site-packages/liquidctl/driver/__pycache__/ardufan*.pyc 2>/dev/null
            echo "Cache files removed."
        fi

        echo
        echo "Verifying removal..."
        liquidctl list
    else
        echo "Uninstallation failed."
        exit 1
    fi
else
    echo "ArduFan driver not found. Nothing to uninstall."
    exit 0
fi
