import numpy as np
import serial
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Configure the serial port
port = serial.Serial('COM6', 19200)  # Replace 'COM1' with the appropriate serial port
fftbuffer = 128
sample_rate = 5000
buffer_size = fftbuffer * 5  # Number of bytes to read from serial

# Create the Tkinter GUI window
window = tk.Tk()
window.title("Guitar Companion")

# getting screen width and height of display
width= window.winfo_screenwidth()
height= window.winfo_screenheight()
# setting tkinter window size
window.geometry("%dx%d" % (width, height))


# Create a Figure object and subplots
gs = gridspec.GridSpec(2,1)
fig = plt.figure(figsize=(16, 9), dpi=100)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)

# data = port.read(buffer_size)
# print(data)
# print(np.frombuffer(data, dtype=np.uint8))


def annot_max(x,y, ax=None):
    ymax = max(y)
    xpos = np.where(y == ymax)
    xmax = x[xpos]
    ax.annotate('local max', xy=(xmax, ymax), xytext=(xmax, ymax + 5), arrowprops=dict(facecolor='black'),)


def update_graphs():
    data = port.read(buffer_size)
    samples = np.frombuffer(data, dtype=np.uint8) - 128*np.ones(buffer_size)
    
    # Perform FFT on the samples
    spectrum = fft(samples)

    # Calculate the amplitudes of the spectrum
    amplitudes = np.abs(spectrum)
    xf = fftfreq(buffer_size, 1/sample_rate)

    # Spectrum
    ax2.clear()
    ax2.plot(xf, amplitudes)
    ax2.set_xlabel('Frequency')
    ax2.set_ylabel('Amplitude')
    ax2.set_xlim(0, 2000)
    ax2.set_ylim(0)
    ax2.axes.yaxis.set_ticklabels([])
    # annot_max(xf, amplitudes, ax=ax2)

    # Waveform
    ax1.clear()
    ax1.plot(samples)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Amplitude')
    ax1.set_xlim(0, 600)
    ax1.axes.xaxis.set_ticklabels([])    

    # Update the canvas
    canvas.draw()

    # Schedule the next update
    window.after(10, update_graphs)


# Schedule the first update
window.after(10, update_graphs)

# Run the Tkinter event loop
window.mainloop()