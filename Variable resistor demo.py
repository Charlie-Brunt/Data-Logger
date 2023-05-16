import matplotlib.pyplot as plt
import numpy as np
import serial
import time

ser = serial.Serial("COM6", 9600)

while True:
    line = ser.readline()
    datastr = line.decode()
    data = datastr.strip()
    print(data)


