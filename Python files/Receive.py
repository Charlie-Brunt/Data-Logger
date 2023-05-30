import serial

# Configure the serial port
port = serial.Serial('COM6', 1000000)  # Replace 'COM1' with the appropriate serial port

# Create a buffer to store the received data
buffer_size = 1024
buffer = bytearray(buffer_size)

# Read and store the data in the buffer
while True:
    # Read data from the serial port
    data = port.read(buffer_size)
    
    # Store the data in the buffer
    buffer[:len(data)] = data
    
    # Process the received data
    # ...

    # Print the received data
    print(buffer[:len(data)])
