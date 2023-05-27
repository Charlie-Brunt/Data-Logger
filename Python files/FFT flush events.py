import numpy as np
import matplotlib.pyplot as plt
import serial
import tkinter as tk
import serial.tools.list_ports
import warnings
import time
import seaborn as sns
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
port = serial.Serial("COM5", 19200)
time.sleep(1); # allow time for serial port to open

# Parameters
FFT_WINDOW = 512
SAMPLE_RATE = 9000
BUFFER_SIZE = FFT_WINDOW  # Number of bytes to read from serial

# Frequency and time axes for plotting
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

# Font dictionary
font = {'family': 'sans-serif',
        'color':  'white',
        'weight': 'normal',
        'size': 8,
        }

# Create a Figure object and subplots
sns.set_style("ticks", {"axes.facecolor": ".2"})
sns.set_context("paper")
fig = plt.figure()
fig.patch.set_facecolor('xkcd:white')
ax1 = fig.add_subplot(2, 1, 1)
line1, = ax1.plot(times, samples, "w")
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, FFT_WINDOW/SAMPLE_RATE)
ax1.set_ylim(-128,127)
# ax1.axes.xaxis.set_ticklabels([])
ax2 = fig.add_subplot(2, 1, 2)
line2, = ax2.plot(fftshift(frequencies), fftshift(amplitudes), "w")
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Amplitude')
ax2.set_xlim(0)
ax2.set_ylim(0, 15000)
text = ax2.text(0, 0, '', va='center', fontdict=font)
# ax2.axes.yaxis.set_ticklabels([])

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)


def update_graphs():
    # Update data
    data = port.read(BUFFER_SIZE)
    samples = np.frombuffer(data, dtype=np.uint8)
    samples = samples - np.average(samples)
    spectrum = fft(samples * window)
    amplitudes = np.abs(spectrum)

    # Waveform
    line1.set_ydata(samples)

    # Spectrum
    peak_freq_index = np.argmax(amplitudes)
    peak_freq = frequencies[peak_freq_index]
    line2.set_ydata(fftshift(amplitudes))
    text.set_text('{:.2f} Hz'.format(peak_freq))
    text.set_position((peak_freq + 10, amplitudes[peak_freq_index]))  # Update annotation position

    # Update the canvas
    canvas.draw()
    canvas.flush_events()

    # Schedule the next update
    root.after(5, update_graphs)


# Schedule the first update
root.after(5, update_graphs)

# Run the Tkinter event loop
root.mainloop()