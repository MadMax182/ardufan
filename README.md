# ArduFan - Arduino Fan Controller for CoolerControl

Turn your Arduino Leonardo into a 6-channel PWM fan controller that works natively with CoolerControl on Linux.

## Features

- 6 fan control channels
- Designed for 2-wire fans (no tachometer feedback)
- liquidctl-compatible protocol (works with CoolerControl automatically)
- No custom drivers or kernel modules needed
- Simple USB serial communication

## Hardware Requirements

- Arduino Leonardo (or any ATmega32U4 board with native USB)
- 2-wire fans (DC fans with just power and ground)
- 12V power supply for fans (DO NOT power fans from Arduino!)
- N-channel MOSFETs (one per fan) - recommended: IRLZ44N, IRL540N, or similar logic-level MOSFETs
- Optional: Flyback diodes (1N4007 or similar) for protection

## Wiring

### Circuit Diagram (per fan)

For 2-wire fans, you need a MOSFET to control the voltage:

```
12V PSU (+) ────────────────┬─── Fan (+) Red Wire
                             │
                             │
Arduino PWM Pin ───────┬─── MOSFET Gate
                       │
                  10kΩ │
                       │
Common GND ────────────┴─── MOSFET Source ─── Fan (-) Black Wire
                       │                   └─── MOSFET Drain
                       │
                  [Optional: 1N4007 Diode across fan terminals, cathode to +12V]
```

### Detailed Wiring (per fan)

1. **MOSFET Gate** → Arduino PWM pin (see table below)
2. **MOSFET Drain** → Fan negative (black wire)
3. **MOSFET Source** → Common Ground (PSU GND + Arduino GND)
4. **10kΩ resistor** between Gate and Source (pulldown resistor)
5. **Fan positive** (red wire) → 12V PSU (+)
6. **Optional diode** across fan terminals (anode to fan-, cathode to fan+) for protection

### Arduino Leonardo PWM Pins

| Channel | Arduino PWM Pin |
|---------|-----------------|
| 0       | 3               |
| 1       | 5               |
| 2       | 6               |
| 3       | 9               |
| 4       | 10              |
| 5       | 11              |

**CRITICAL:**
- All grounds MUST be connected together (PSU GND, Arduino GND, MOSFET Source)
- Use **logic-level MOSFETs** (gate threshold < 5V) like IRLZ44N or IRL540N
- DO NOT connect fans directly to Arduino pins - they will burn out!

## Installation

### 1. Flash the Arduino

```bash
cd ~/Documents/@github/ardufan

# Using Arduino IDE:
# - Open ardufan.ino
# - Select Board: Arduino Leonardo
# - Select Port: /dev/ttyACM0
# - Click Upload

# Using arduino-cli:
arduino-cli compile --fqbn arduino:avr:leonardo .
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo .
```

### 2. Set up udev rules (optional but recommended)

Create a udev rule so the device shows up consistently:

```bash
sudo nano /etc/udev/rules.d/99-ardufan.rules
```

Add:
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="8036", SYMLINK+="ardufan", MODE="0666"
```

Reload:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Now the device will show up as `/dev/ardufan`

### 3. Install CoolerControl

```bash
# Check your distro's instructions at:
# https://gitlab.com/coolercontrol/coolercontrol

# Example for Arch:
yay -S coolercontrol

# Start the daemon
sudo systemctl enable --now coolerd
```

### 4. Configure CoolerControl

CoolerControl should auto-detect the Arduino via liquidctl. If not:

1. Open CoolerControl GUI
2. Go to Settings → Devices
3. Look for "ArduFan" or a Corsair-like device on `/dev/ttyACM0`
4. Enable it

You should now see 6 fan channels you can control!

## Testing

Test the controller manually before connecting to CoolerControl:

```bash
# Install pyserial
pip install pyserial

# Test communication
python3 -c "
import serial
import time

s = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
time.sleep(2)

# Get firmware info
s.write(bytes([0xFF, 0x01]))
print('Firmware:', s.read(32))

# Set fan 0 to 50%
s.write(bytes([0xFF, 0x10, 0x00, 50]))

# Get status
s.write(bytes([0xFF, 0x02]))
status = s.read(128)
print('Status:', status.hex())

s.close()
"
```

## Protocol Documentation

The Arduino uses a simple binary protocol over USB serial (115200 baud):

### Commands

| Command | Bytes | Description |
|---------|-------|-------------|
| Get Info | `FF 01` | Returns firmware version and channel count |
| Get Status | `FF 02` | Returns all channels' duty/RPM/status (RPM always 0) |
| Set Fan | `FF 10 [CH] [DUTY]` | Set channel to duty cycle (0-100%) |
| Get RPM | `FF 11 [CH]` | Get RPM for specific channel (always returns 0) |
| Set All | `FF 20 [DUTY]` | Set all channels to same duty |

### Responses

All responses start with `FF` followed by the command byte. RPM values are always `00 00` for 2-wire fans.

## Troubleshooting

**CoolerControl doesn't detect the device:**
- Check `/dev/ttyACM0` exists: `ls -l /dev/ttyACM0`
- Run `liquidctl list` to see if liquidctl detects it
- Check permissions (should be in dialout group)
- Try unplugging and replugging the Arduino

**Fans don't spin:**
- Verify 12V power supply is connected
- Check all grounds are connected together (PSU GND, Arduino GND, MOSFET Source)
- Verify MOSFET is logic-level (gate threshold < 5V)
- Check MOSFET wiring: Gate→PWM pin, Drain→Fan-, Source→GND
- Some fans need minimum 40-50% duty to start
- Test fan with direct 12V connection first

**Fans spin at 100% all the time:**
- Check 10kΩ pulldown resistor is between MOSFET Gate and Source
- Verify PWM pin connection to MOSFET Gate
- Try swapping MOSFET (might be damaged)
- Check for short circuits in wiring

**CoolerControl shows RPM as 0:**
- This is normal! 2-wire fans have no tachometer
- RPM monitoring not available for 2-wire fans
- If you need RPM, use 4-pin PWM fans instead

**MOSFET gets hot:**
- Use a proper logic-level MOSFET (IRLZ44N, IRL540N)
- Add a heatsink if controlling high-current fans (>1A)
- Check for wiring errors

## Limitations

- No RPM monitoring (2-wire fans don't have tachometers)
- Maximum 6 fans (limited by available PWM pins on Leonardo)
- Requires external MOSFETs (one per fan)
- No RGB control

## Alternative Configurations

### Using a MOSFET driver board

Instead of individual MOSFETs, you can use a pre-made MOSFET board:
- Search for "6-channel MOSFET board" or "Arduino MOSFET shield"
- Connect Arduino PWM pins to board inputs
- Connect fans to board outputs
- Much cleaner wiring!

### Using with 4-pin PWM fans

If you want to use 4-pin fans instead, you can modify the code to remove the MOSFET requirement and add tachometer support. See the git history for the 4-pin version.

## License

MIT License - do whatever you want with this code!
