"""Setup script for ArduFan liquidctl driver."""

from setuptools import setup

setup(
    name='liquidctl-ardufan',
    version='1.0.0',
    description='liquidctl driver for ArduFan Arduino fan controller',
    py_modules=['ardufan'],
    install_requires=[
        'liquidctl>=1.13.0',
        'pyserial',
    ],
    entry_points={
        'liquidctl.driver': [
            'ardufan = ardufan:ArduFan',
        ],
    },
)
