import numpy as np
import serial
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import serial.tools.list_ports
import warnings

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

port = serial.Serial(arduino_ports[0], 19200)

# Parameters
fftbuffer = 256 # 256
sample_rate = 16000
buffer_size = fftbuffer  # Number of bytes to read from serial
frequencies = fftfreq(fftbuffer, 1/sample_rate)

data = port.read(buffer_size)
print(data)
print(np.frombuffer(data, dtype=np.uint8))


# Initial data
data = port.read(buffer_size)
samples = np.frombuffer(data, dtype=np.uint8) # - 128 * np.ones(buffer_size)
spectrum = fft(samples)
amplitudes = np.abs(spectrum)
# for i in range(10):
#     amplitudes[i] = 0


# Create the Tkinter GUI window
window = tk.Tk()
window.title("Guitar Companion")
width = window.winfo_screenwidth()
height= window.winfo_screenheight()
window.geometry("%dx%d" % (width, height))

# Create a Figure object and subplots
fig = plt.figure()
ax1 = fig.add_subplot(2, 1, 1)
ln1, = ax1.plot(np.arange(fftbuffer), samples)
ax1.set_xlabel('Time')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, 600)
ax1.axes.xaxis.set_ticklabels([])
ax2 = fig.add_subplot(2, 1, 2)
ln2, = ax2.plot(frequencies, amplitudes)
ax2.set_xlabel('Frequency')
ax2.set_ylabel('Amplitude')
ax2.set_xlim(0, 2000)
ax2.set_ylim(0)
ax2.axes.yaxis.set_ticklabels([])

plt.ion()
plt.show(block=False)

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master = window)
# fig.show()
canvas.draw()

bg1 = canvas.copy_from_bbox(ax1.bbox)
bg2 = canvas.copy_from_bbox(ax2.bbox)

canvas.get_tk_widget().pack(side="top",fill='both',expand=True)


def annot_max(x,y, ax=None):
    ymax = max(y)
    xpos = np.where(y == ymax)
    xmax = x[xpos]
    ax.annotate('local max', xy=(xmax, ymax), xytext=(xmax, ymax + 5), arrowprops=dict(facecolor='black'),)


def update():
    # Update data
    data = port.read(buffer_size)
    samples = np.frombuffer(data, dtype=np.uint8) # - 128*np.ones(fftbuffer)
    spectrum = fft(samples)
    amplitudes = np.abs(spectrum)
    # for i in range(20):
    #     amplitudes[i] = 0
    
    # Update datapoints
    ln1.set_ydata(samples)
    ln2.set_ydata(amplitudes)
    
    # annot_max(xf, amplitudes, ax=ax2)  

    fig.canvas.restore_region(bg1)
    ax1.draw_artist(ln1)
    canvas.blit(ax1.bbox)

    fig.canvas.restore_region(bg2)
    ax2.draw_artist(ln2)
    canvas.blit(ax2.bbox)

    canvas.flush_events()
    window.after(1, update)


# Schedule the first update
window.after(1, update)

# Run the Tkinter event loop
window.mainloop()