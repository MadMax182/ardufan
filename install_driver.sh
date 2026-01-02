#!/bin/bash
# Install ArduFan liquidctl driver

echo "Installing ArduFan liquidctl driver..."
echo "This requires sudo to copy the driver to liquidctl's directory."
echo

sudo cp ~/Documents/@github/ardufan/liquidctl_driver/ardufan.py /usr/lib/python3.13/site-packages/liquidctl/driver/

if [ $? -eq 0 ]; then
    echo "Driver installed successfully!"
    echo
    echo "Testing detection..."
    liquidctl list
else
    echo "Installation failed."
    exit 1
fi
