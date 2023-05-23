import tkinter as Tk
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# from Backend import Backend  #self written data acquisition handler  
import random

#global variables
t0 = datetime.now() #start time of program

#Returns time difference in seconds
def time_difference(t1, t2):
    delta = t2-t1
    delta = delta.total_seconds()
    return delta

# Define Class for Flow data display
class FlowFig():
    def __init__(self, master): #master:Parent frame for plot
        #Initialize plot data
        self.t = []
        self.Flow = []

        #Initialize plot for FlowFig
        self.fig = plt.figure(figsize=(4,4))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Flow Control Monitor")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Flow")
        self.ax.axis([0,100,0,5])
        self.line = self.ax.plot(self.t, self.Flow, '-')

        #Set up canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master = master)
        self.canvas.draw()
        self.ax.add_line(self.line[0])
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.grid(True)

        # # Initialize handler for data aqcuisition
        # self.Data= Backend() 
        # self.Data.initialize()

    #update figure
    def update(self):
        # get new data values
        self.t.append(time_difference(t0, datetime.now()))
        Flow = random.uniform(1, 5)
        self.Flow.append(Flow)

        # shorten data vector if too long
        if len(self.t) > 200:
            del self.t[0]
            del self.Flow[0]

        #adjust xlims, add new data to plot
        self.ax.set_xlim([np.min(self.t), np.max(self.t)])
        self.line[0].set_data(self.t, self.Flow) 

        #blit new data into old frame
        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.line[0])
        self.canvas.blit(self.ax.bbox)
        self.canvas.flush_events()
        root.after(1,self.update)

#Flow Frame of GUI
class FlowPage(Tk.Frame):
    def __init__(self, parent, controller):
        Tk.Frame.__init__(self,parent)    
        self.parent = parent    
        self.FlowPlot = FlowFig(self)
        self.FlowPlot.canvas.get_tk_widget().grid(row=0, column=0, rowspan=9, columnspan=9)

# Mainloop
root= Tk.Tk()
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

Flowmonitor = FlowPage(root, root)
Flowmonitor.grid(row =0, column=0, rowspan =10, columnspan=10)
Flowmonitor.rowconfigure(0, weight=1)
Flowmonitor.columnconfigure(0, weight=1)

root.after(25, Flowmonitor.FlowPlot.update)
root.mainloop()