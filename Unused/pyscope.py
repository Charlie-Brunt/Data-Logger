# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 16:56:46 2022

@author: TsiamDev
"""

from matplotlib import pyplot as plt
from matplotlib.widgets import Button

from serial import Serial

modifier = 3
offset = 200 * modifier

# Button event handlers
class EventHandlers:
    def __init__(self):
        self.isPaused = False
    
    def Pause(self, event):
        self.isPaused = not self.isPaused
        print(self.isPaused)
        
    def ZoomIn(self, event):
        global offset, modifier
        if offset - (modifier * 10) > 20:
            offset = offset - (modifier * 10)
        
    def ZoomOut(self, event):
        global offset, modifier
        offset = offset + (modifier * 10)

#ser = Serial('COM6', 115200, timeout=None)
ser = Serial('COM7', 1000000, timeout=None)
ser.set_buffer_size(rx_size = offset)
ser.flushInput()

eh = EventHandlers()

i = []
data = []
int_data = []
while True:

    if eh.isPaused is False:
        ser.flushInput()
        while True:
            bytesToRead = ser.inWaiting()
            print(bytesToRead)
            if bytesToRead >= offset:
                break
    
        try:
            # read line, convert to python string
            temp = ser.read(offset).decode()
            # remove \r\n
            temp = temp.split('\r\n')
            temp = [x for x in temp if x != '']
            #print(temp)
            print("offset: ", offset)
            if temp != "":
                buf = [int(float(x)) for x in temp]
    
                data = []
                for b in buf:
                    data.append(b * (3.3 / 4095.0))
                    #total_data.append(b * (3.3 / 1023.0))
                
                int_data = [int(x) for x in data]
    
                # Triggering
                #"""
                index = int_data.index(0)
                indices = [i for i, x in enumerate(int_data) if x == 0]
                for i in range(0, len(indices)-1):
                    if int_data[indices[i]] == 0 and int_data[indices[i+1]] > 0:
                        index = i                    
                        break
                int_data = int_data[index:]
                #print(int_data[index], index)
                #"""
                i = range(0, len(int_data))
                #i = range(0, offset)

                #Plot(int_data, i, eh)
                plt.cla()
                axPause = plt.axes([0.81, 0.05, 0.1, 0.075])
                pause_btn = Button(axPause, 'Hold')
                pause_btn.on_clicked(eh.Pause)
                axZoomIn = plt.axes([0.81, 0.15, 0.1, 0.075])
                axZoomIn = Button(axZoomIn, 'ZoomIn')
                axZoomIn.on_clicked(eh.ZoomIn)
                axZoomOut = plt.axes([0.81, 0.25, 0.1, 0.075])
                axZoomOut = Button(axZoomOut, 'ZoomOut')
                axZoomOut.on_clicked(eh.ZoomOut)
                plt.subplot(1, 2, 1)
                plt.plot(i, int_data)
                plt.grid(True)
                plt.rc('axes', axisbelow=True)
                plt.ylabel('Volts (V)')
                plt.xlabel('Time (ns)')
                plt.pause(0.05)

        except Exception as ex:
            #in case we receive some unidentified characters from serial port
            print(ex)
    else:
        print(eh.isPaused)
        #Plot(int_data, i, eh)
        plt.cla()
        axPause = plt.axes([0.81, 0.05, 0.1, 0.075])
        pause_btn = Button(axPause, 'Hold')
        pause_btn.on_clicked(eh.Pause)
        axZoomIn = plt.axes([0.81, 0.15, 0.1, 0.075])
        axZoomIn = Button(axZoomIn, 'ZoomIn')
        axZoomIn.on_clicked(eh.ZoomIn)
        axZoomOut = plt.axes([0.81, 0.25, 0.1, 0.075])
        axZoomOut = Button(axZoomOut, 'ZoomOut')
        axZoomOut.on_clicked(eh.ZoomOut)
        plt.subplot(1, 2, 1)
        plt.plot(i, int_data)
        plt.grid(True)
        plt.rc('axes', axisbelow=True)
        plt.ylabel('Volts (V)')
        plt.xlabel('Time (ns)')
        plt.pause(0.05)
        
plt.show()
ser.close()