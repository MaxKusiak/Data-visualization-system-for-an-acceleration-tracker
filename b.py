# import serial

# ser = serial.Serial("COM4", 9600, timeout=1)

# # while True:
# #     data = ser.readline().decode().strip()
    
# #     if data:
# #         x, y, z = map(float, data.split(","))
# #         print(x, y, z)

# # from serial.tools import list_ports
# # for port in list_ports.comports():
# #     print(port.device, "|", port.description)



import serial
import struct
import time
import math

# Налаштування симулятора
PORT = "COM3"
BAUDRATE = 115200

FREQUENCY = 100  # Гц
DURATION = 1     # секунд

# Підключення
ser = serial.Serial(PORT, BAUDRATE, timeout=1)

print("Tracker connected")

# Імітація збору даних
measurements = []

N = FREQUENCY * DURATION

for i in range(N):
    t = i / FREQUENCY

    # Імітація показників акселерометра
    x = math.sin(2 * math.pi * 1 * t)
    y = math.cos(2 * math.pi * 0.5 * t)
    z = 9.81 + 0.2 * math.sin(2 * math.pi * 2 * t)

    measurements.append((x, y, z))

    time.sleep(1 / FREQUENCY)

print(f"Collected {len(measurements)} measurements")

# Передача зібраних даних
print("Sending data...")

for x, y, z in measurements:

    # 3 числа float32, little-endian
    packet = struct.pack("<fff", x, y, z)

    ser.write(packet)

    # Імітація швидкості передачі
    # (приблизно 100 вимірювань за секунду)
    time.sleep(1 / FREQUENCY)

print("Transmission completed")

ser.close()
