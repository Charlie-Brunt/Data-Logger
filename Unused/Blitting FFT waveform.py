import numpy as np
import matplotlib.pyplot as plt
import serial
import tkinter as tk
import serial.tools.list_ports
import warnings
from scipy.fft import fft, fftfreq
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
port = serial.Serial("COM5", 19200)

# Parameters
FFT_WINDOW = 512 # 256
SAMPLE_RATE = 5000
BUFFER_SIZE = FFT_WINDOW  # Number of bytes to read from serial
frequencies = fftfreq(FFT_WINDOW, 1/SAMPLE_RATE)

# Initial data
data = port.read(BUFFER_SIZE)
samples = np.frombuffer(data, dtype=np.uint8)
# print(data)
samples = samples - np.average(samples)
# print(samples)
spectrum = fft(samples)
amplitudes = np.abs(spectrum)


# Create the Tkinter GUI window
window = tk.Tk()
window.title("Guitar Companion")
width = window.winfo_screenwidth()
height= window.winfo_screenheight()
window.geometry("%dx%d" % (width, height))

# Create a Figure object and subplots
fig = plt.figure()
ax1 = fig.add_subplot(2, 1, 1)
ln1, = ax1.plot(np.arange(FFT_WINDOW)/SAMPLE_RATE, samples, animated=True)
ax1.set_xlabel('Time')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, FFT_WINDOW/SAMPLE_RATE)
# ax1.axes.xaxis.set_ticklabels([])
ax2 = fig.add_subplot(2, 1, 2)
ln2, = ax2.plot(frequencies, amplitudes, animated=True)
ax2.set_xlabel('Frequency')
ax2.set_ylabel('Amplitude')
ax2.set_xlim(0)
ax2.set_ylim(0)
# ax2.axes.yaxis.set_ticklabels([])

plt.ion()
# plt.show(block=False)

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master = window)
canvas.draw()
bg1 = canvas.copy_from_bbox(ax1.bbox)
bg2 = canvas.copy_from_bbox(ax2.bbox)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)


def annot_max(x, y, ax=None):
    xmax = x[np.argmax(y)]
    ymax = y.max()
    text = "{:.3f} Hz".format(xmax)
    ax.annotate(text, xy=(xmax, ymax), xytext=(xmax, ymax + 5))


def update():
    # Update data
    data = port.read(BUFFER_SIZE)
    samples = np.frombuffer(data, dtype=np.uint8)
    samples = samples - np.average(samples)
    spectrum = fft(samples)
    amplitudes = np.abs(spectrum)
    
    # Update datapoints
    ln1.set_ydata(samples)
    ln2.set_ydata(amplitudes)

    fig.canvas.restore_region(bg1)
    ax1.draw_artist(ln1)
    canvas.blit(ax1.bbox)

    fig.canvas.restore_region(bg2)
    ax2.draw_artist(ln2)
    # if max(amplitudes) > 0.1:
    #     ax2.draw_artist(annot_max(frequencies, amplitudes, ax=ax2))
    canvas.blit(ax2.bbox)

    canvas.flush_events()
    window.after(1, update)


# Schedule the first update
window.after(1, update)

# Run the Tkinter event loop
window.mainloop()