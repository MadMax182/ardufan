/*
 * Arduino Fan Controller - liquidctl compatible
 * Emulates a Corsair Commander-style device for CoolerControl/liquidctl
 *
 * Designed for 2-wire fans (no tachometer feedback)
 * Uses PWM to drive MOSFETs that control fan voltage
 *
 * CoolerControl will detect this via liquidctl automatically
 */

#define NUM_FANS 6  // Most Corsair controllers support 6 fans
#define FIRMWARE_VERSION "1.0.0"
#define TWO_WIRE_FANS  // No tachometer support

// PWM output pins (Leonardo has PWM on 3,5,6,9,10,11,13)
const int pwmPins[NUM_FANS] = {3, 5, 6, 9, 10, 11};

// Fan state
uint8_t fanDuty[NUM_FANS] = {0};  // 0-100%
bool fanConnected[NUM_FANS] = {true};  // Assume all connected

// Command buffer
#define CMD_BUFFER_SIZE 64
uint8_t cmdBuffer[CMD_BUFFER_SIZE];
int cmdIndex = 0;

void setup() {
  Serial.begin(115200);

  // Initialize PWM pins for controlling MOSFETs
  for (int i = 0; i < NUM_FANS; i++) {
    pinMode(pwmPins[i], OUTPUT);
    analogWrite(pwmPins[i], 0);  // Start with fans off
  }
}

void loop() {
  // Process serial commands from CoolerControl/liquidctl
  while (Serial.available() > 0) {
    uint8_t byte = Serial.read();

    if (byte == 0xFF) {
      // Start of command marker - reset buffer
      cmdIndex = 0;
      cmdBuffer[cmdIndex++] = byte;
    } else if (cmdIndex > 0 && cmdIndex < CMD_BUFFER_SIZE) {
      cmdBuffer[cmdIndex++] = byte;

      // Check if we have a complete command
      if (cmdIndex >= 2) {
        processCommand();
      }
    }
  }
}

void processCommand() {
  // Simple command protocol compatible with liquidctl expectations
  // Commands are in format: [0xFF] [CMD] [DATA...]

  if (cmdBuffer[0] != 0xFF || cmdIndex < 2) {
    return;
  }

  uint8_t cmd = cmdBuffer[1];

  switch (cmd) {
    case 0x01:  // Get firmware info
      sendFirmwareInfo();
      cmdIndex = 0;
      break;

    case 0x02:  // Get status (all fans)
      sendStatus();
      cmdIndex = 0;
      break;

    case 0x10:  // Set fan speed
      if (cmdIndex >= 4) {
        uint8_t channel = cmdBuffer[2];
        uint8_t duty = cmdBuffer[3];
        setFanSpeed(channel, duty);
        cmdIndex = 0;
      }
      break;

    case 0x11:  // Get fan RPM
      if (cmdIndex >= 3) {
        uint8_t channel = cmdBuffer[2];
        sendFanRPM(channel);
        cmdIndex = 0;
      }
      break;

    case 0x20:  // Set all fans
      if (cmdIndex >= 3) {
        uint8_t duty = cmdBuffer[2];
        for (int i = 0; i < NUM_FANS; i++) {
          setFanSpeed(i, duty);
        }
        sendAck();
        cmdIndex = 0;
      }
      break;

    default:
      // Unknown command - reset
      if (cmdIndex >= 3) {
        cmdIndex = 0;
      }
      break;
  }
}

void setFanSpeed(uint8_t channel, uint8_t duty) {
  if (channel >= NUM_FANS) return;

  fanDuty[channel] = constrain(duty, 0, 100);

  // Convert 0-100% to 0-255 PWM value
  uint8_t pwmValue = map(fanDuty[channel], 0, 100, 0, 255);
  analogWrite(pwmPins[channel], pwmValue);
}

void sendFirmwareInfo() {
  // Response: [0xFF] [0x01] [VERSION] [NUM_FANS]
  Serial.write((uint8_t)0xFF);
  Serial.write((uint8_t)0x01);
  Serial.print("ArduFan ");
  Serial.print(FIRMWARE_VERSION);
  Serial.write((uint8_t)0x00);  // Null terminator
  Serial.write((uint8_t)NUM_FANS);
  Serial.flush();
}

void sendStatus() {
  // Response: [0xFF] [0x02] [FAN0_DUTY] [FAN0_RPM_HIGH] [FAN0_RPM_LOW] ... [FAN5]
  // RPM is always 0 for 2-wire fans (no tachometer)
  Serial.write((uint8_t)0xFF);
  Serial.write((uint8_t)0x02);

  for (int i = 0; i < NUM_FANS; i++) {
    Serial.write(fanDuty[i]);
    Serial.write((uint8_t)0x00);  // RPM high byte = 0
    Serial.write((uint8_t)0x00);  // RPM low byte = 0
    Serial.write((uint8_t)(fanConnected[i] ? 0x01 : 0x00));
  }

  Serial.flush();
}

void sendFanRPM(uint8_t channel) {
  if (channel >= NUM_FANS) {
    sendError();
    return;
  }

  // Response: [0xFF] [0x11] [CHANNEL] [RPM_HIGH] [RPM_LOW]
  // Always 0 for 2-wire fans (no tachometer)
  Serial.write((uint8_t)0xFF);
  Serial.write((uint8_t)0x11);
  Serial.write(channel);
  Serial.write((uint8_t)0x00);  // RPM high byte = 0
  Serial.write((uint8_t)0x00);  // RPM low byte = 0
  Serial.flush();
}

void sendAck() {
  Serial.write((uint8_t)0xFF);
  Serial.write((uint8_t)0xAA);  // ACK
  Serial.flush();
}

void sendError() {
  Serial.write((uint8_t)0xFF);
  Serial.write((uint8_t)0xEE);  // Error
  Serial.flush();
}
