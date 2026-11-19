# import struct

# with open('data.bin', 'wb') as f:
#     data = [[-23.4, 41.1, -5.7], [18.3, -44.9, 30.2], [-12.1, 8.5, -37.4]]
#     for row in data:
#         for item in row:
#             f.write(struct.pack('f', item))

# # with open('data.bin', 'rb') as f:
# #     data = []
# #     while True:
# #         bytes_read = f.read(4)  # Read 4 bytes for a float
# #         if not bytes_read:
# #             break
# #         value = struct.unpack('f', bytes_read)[0]
# #         data.append(value)
# #     print(data)  # Output the list of floats read from the binary file

# import serial
# import random
# import time

# ser = serial.Serial("COM3", 9600)

# while True:
#     x = random.randint(-10, 10)
#     y = random.randint(-10, 10)
#     z = random.randint(-10, 10)
    
#     data = f"{x:.2f}, {y:.2f}, {z:.2f}\n"
    
#     ser.write(data.encode())
    
#     time.sleep(0.3)

import struct

with open("data.bin", "rb") as file:
    data = file.read()

# Кожне вимірювання містить 3 float32
measurements = list(struct.iter_unpack("<fff", data))

print("Measurements:", len(measurements))

for x, y, z in measurements:
    print(f"X={x:.3f}, Y={y:.3f}, Z={z:.3f}")
    