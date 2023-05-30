import serial
import serial.tools.list_ports
import time
import warnings

def connectToArduino(BAUD_RATE):
    # Configure the serial port
    arduino_ports = [
        p.device
        for p in serial.tools.list_ports.comports()
        if 'Arduino' in p.description
    ]
    if not arduino_ports:
        raise IOError("No Arduino found")
    if len(arduino_ports) > 1:
        warnings.warn('Multiple Arduinos found - using the first')

    port = serial.Serial(arduino_ports[0], BAUD_RATE)
    # port = serial.Serial("COM5", 1000000)
    time.sleep(1); # allow time for serial port to open
    return port

# connectToArduino(1000

ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(p.serial_number)