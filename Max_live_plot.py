import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import serial
import datetime as dt

ser = serial.Serial("COM3", 9600)
x=0
xs = []
ys = []
now = dt.datetime.now()
fig = plt.figure()
ax = plt.subplot(1, 1, 1)




def animate(i, xs, ys):
    global x
    # read serial data
    y = 0
    while y in range(0,1):
        print("Ayayayayay")
        line = ser.readline()
        print(line)
    #datastr = line.decode()
    #data = int(datastr.strip())

    #xs.append(x)
    #x += 1
    #ys.append(data)

    #xs = xs[-100:]
    #ys = ys[-100:]

    #ax.clear()
    #ax.plot(xs, ys)

    #plt.xticks(rotation=45, ha='right')
    #plt.subplots_adjust(bottom=0.30)
    #plt.title('Voltage over Time')
    #plt.ylabel('Voltage')

ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=5)
plt.show()


