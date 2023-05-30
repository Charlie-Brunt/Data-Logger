import numpy as np
import matplotlib.pyplot as plt
import serial
import tkinter as tk
import serial.tools.list_ports
import warnings
import time
from scipy.fft import fft, fftfreq, fftshift
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Configure the serial port
# arduino_ports = [
#     p.device
#     for p in serial.tools.list_ports.comports()
#     if 'Arduino' in p.description
# ]
# if not arduino_ports:
#     raise IOError("No Arduino found")
# if len(arduino_ports) > 1:
#     warnings.warn('Multiple Arduinos found - using the first')

# port = serial.Serial(arduino_ports[0], 19200)
port = serial.Serial("COM6", 1000000)
time.sleep(1); # allow time for serial port to open

# Parameters
FFT_WINDOW = 512
SAMPLE_RATE = 8000
BUFFER_SIZE = FFT_WINDOW  # Number of bytes to read from serial
frequencies = fftfreq(FFT_WINDOW, 1/SAMPLE_RATE)
times = np.arange(FFT_WINDOW)/SAMPLE_RATE
# Hanning window
window = 0.5 * (1 - np.cos(np.linspace(0, 2*np.pi, FFT_WINDOW, False)))

# Initial data
data = port.read(BUFFER_SIZE)
samples = np.frombuffer(data, dtype=np.uint8)
# print(data)
# print(samples)
samples = samples - np.average(samples)
spectrum = fft(samples * window)
amplitudes = np.abs(spectrum)

# Create the Tkinter GUI window
root = tk.Tk()
root.title("Guitar Companion")
width = root.winfo_screenwidth()
height = root.winfo_screenheight()
root.geometry("%dx%d" % (width, height))

# Create a Figure object and subplots
fig = plt.figure()
ax1 = fig.add_subplot(2, 1, 1)
ax1.set_xlabel('Time')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, FFT_WINDOW/SAMPLE_RATE)
line1, = ax1.plot(times, samples)
# ax1.axes.xaxis.set_ticklabels([])
ax2 = fig.add_subplot(2, 1, 2)
ax2.set_xlabel('Frequency')
ax2.set_ylabel('Amplitude')
ax2.set_xlim(0)
ax2.set_ylim(0)
line2, = ax1.plot(fftshift(frequencies), fftshift(amplitudes))
# ax2.axes.yaxis.set_ticklabels([])

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)


def annot_max(x, y, ax=None):
    xmax = x[np.argmax(y)]
    ymax = y.max()
    text = "{:.2f} Hz".format(xmax)
    ax.annotate(text, xy=(xmax, ymax), xytext=(xmax, ymax + 5))

def update_graphs():
    # Update data
    data = port.read(BUFFER_SIZE)
    samples = np.frombuffer(data, dtype=np.uint8)
    samples = samples - np.average(samples)
    spectrum = fft(samples * window)
    amplitudes = np.abs(spectrum)

    # Waveform
    ax1.clear()
    ax1.plot(times, samples)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Amplitude')
    ax1.set_xlim(0, FFT_WINDOW/SAMPLE_RATE)

    # Spectrum
    ax2.clear()
    ax2.plot(fftshift(frequencies), fftshift(amplitudes))
    ax2.set_xlabel('Frequency')
    ax2.set_ylabel('Amplitude')
    ax2.set_xlim(0)
    ax2.set_ylim(0)
    # if max(amplitudes) > 0.1:
    annot_max(frequencies, amplitudes, ax=ax2)

    # Update the canvas
    canvas.draw()

    # Schedule the next update
    root.after(5, update_graphs)

# Schedule the first update
root.after(5, update_graphs)

# Run the Tkinter event loop
root.mainloop()