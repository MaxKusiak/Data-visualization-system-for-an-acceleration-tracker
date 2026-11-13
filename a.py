import struct

with open('data.bin', 'wb') as f:
    data = [[-23.4, 41.1, -5.7], [18.3, -44.9, 30.2], [-12.1, 8.5, -37.4]]
    for row in data:
        for item in row:
            f.write(struct.pack('f', item))

# with open('data.bin', 'rb') as f:
#     data = []
#     while True:
#         bytes_read = f.read(4)  # Read 4 bytes for a float
#         if not bytes_read:
#             break
#         value = struct.unpack('f', bytes_read)[0]
#         data.append(value)
#     print(data)  # Output the list of floats read from the binary file