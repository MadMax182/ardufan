"""liquidctl driver for ArduFan Arduino-based fan controller."""

import logging
import usb
import serial
import time
from liquidctl.driver.usb import UsbDriver

LOGGER = logging.getLogger(__name__)

# Arduino Leonardo USB IDs
ARDUINO_VENDOR_ID = 0x2341
LEONARDO_PRODUCT_ID = 0x8036

# Protocol commands
CMD_GET_INFO = 0x01
CMD_GET_STATUS = 0x02
CMD_SET_FAN = 0x10
CMD_GET_RPM = 0x11
CMD_SET_ALL = 0x20


class ArduFan(UsbDriver):
    """liquidctl driver for ArduFan controller."""

    SUPPORTED_DEVICES = [
        (ARDUINO_VENDOR_ID, LEONARDO_PRODUCT_ID, None, 'ArduFan Controller', {}),
    ]

    def __init__(self, device, description, **kwargs):
        """Instantiate an ArduFan device."""
        super().__init__(device, description, **kwargs)
        self._num_fans = 6
        self._serial = None
        self._port = None

    def connect(self, **kwargs):
        """Connect to the device."""
        # Find the serial port for this USB device
        # Arduino Leonardo shows up as /dev/ttyACM*
        import os
        import glob

        # Get bus and address from USB device
        try:
            bus = self.device.bus
            address = self.device.address

            # Find corresponding ttyACM device
            for port in glob.glob('/dev/ttyACM*'):
                # Check if this port corresponds to our USB device
                try:
                    device_path = os.path.realpath(f'/sys/class/tty/{os.path.basename(port)}')
                    if f'{bus}-{address}' in device_path or str(address) in device_path:
                        self._port = port
                        break
                except Exception:
                    pass

            if not self._port:
                # Fallback: try the first available ttyACM
                ports = sorted(glob.glob('/dev/ttyACM*'))
                if ports:
                    self._port = ports[0]
                    LOGGER.warning('Could not determine exact port, using %s', self._port)

            if self._port:
                self._serial = serial.Serial(self._port, 115200, timeout=1)
                time.sleep(2)  # Wait for Arduino to reset
                LOGGER.info('Connected to ArduFan on %s', self._port)
                return super().connect(**kwargs)
            else:
                raise RuntimeError('Could not find serial port for ArduFan device')

        except Exception as e:
            LOGGER.error('Failed to connect: %s', e)
            raise

    def initialize(self, **kwargs):
        """Initialize the device."""
        if not self._serial or not self._serial.is_open:
            self.connect()

        msg = bytes([0xFF, CMD_GET_INFO])
        self._serial.write(msg)
        time.sleep(0.1)

        # Read response
        response = self._serial.read(32)

        if response and len(response) > 2 and response[0] == 0xFF and response[1] == CMD_GET_INFO:
            # Parse firmware info
            try:
                null_idx = response.index(0x00, 2)
                firmware = response[2:null_idx].decode('ascii', errors='ignore')
                self._num_fans = response[null_idx + 1] if null_idx + 1 < len(response) else 6
                LOGGER.info('Initialized ArduFan: %s, %d channels', firmware, self._num_fans)
                return [(firmware, str(self._num_fans) + ' channels', '')]
            except (ValueError, IndexError, UnicodeDecodeError):
                LOGGER.warning('Failed to parse firmware info')
                return [('ArduFan', '6 channels', '')]

        return [('ArduFan', '6 channels', '')]

    def get_status(self, **kwargs):
        """Get device status."""
        if not self._serial or not self._serial.is_open:
            self.connect()

        msg = bytes([0xFF, CMD_GET_STATUS])
        self._serial.write(msg)
        time.sleep(0.1)

        # Read response
        response = self._serial.read(128)

        status = []

        if response and len(response) > 2 and response[0] == 0xFF and response[1] == CMD_GET_STATUS:
            # Parse status
            offset = 2
            for i in range(self._num_fans):
                if offset + 4 <= len(response):
                    duty = response[offset]
                    rpm_high = response[offset + 1]
                    rpm_low = response[offset + 2]

                    rpm = (rpm_high << 8) | rpm_low

                    status.append((f'Fan {i + 1} duty', duty, '%'))
                    status.append((f'Fan {i + 1} speed', rpm, 'rpm'))

                    offset += 4

        return sorted(status)

    def set_color(self, channel, mode, colors, **kwargs):
        """Not supported."""
        raise NotImplementedError()

    def set_speed_profile(self, channel, profile, **kwargs):
        """Not supported."""
        raise NotImplementedError()

    def set_fixed_speed(self, channel, duty, **kwargs):
        """Set fan to a fixed speed duty."""
        if not self._serial or not self._serial.is_open:
            self.connect()

        if channel == 'sync':
            # Set all fans
            duty_val = int(duty)
            if duty_val < 0 or duty_val > 100:
                raise ValueError('Duty must be between 0 and 100')

            msg = bytes([0xFF, CMD_SET_ALL, duty_val])
            self._serial.write(msg)
        else:
            # Set specific fan
            if not channel.startswith('fan'):
                raise ValueError(f'Unknown channel: {channel}')

            try:
                fan_num = int(channel[3:]) - 1
            except (ValueError, IndexError):
                raise ValueError(f'Invalid channel: {channel}')

            if fan_num < 0 or fan_num >= self._num_fans:
                raise ValueError(f'Invalid fan number: {fan_num + 1}')

            duty_val = int(duty)
            if duty_val < 0 or duty_val > 100:
                raise ValueError('Duty must be between 0 and 100')

            msg = bytes([0xFF, CMD_SET_FAN, fan_num, duty_val])
            self._serial.write(msg)

    def disconnect(self, **kwargs):
        """Disconnect from the device."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        return super().disconnect(**kwargs)
