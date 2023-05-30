import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import seaborn as sns
import warnings
import time
import serial
import serial.tools.list_ports
from scipy.fft import fft, fftfreq, fftshift
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def connectToArduino(BAUD_RATE, serial_number="95530343834351A0B091"):
    # Configure the serial port
    for pinfo in serial.tools.list_ports.comports():
        if pinfo.serial_number == serial_number:
            return serial.Serial(pinfo.device, BAUD_RATE)
    raise IOError("No Arduino found")


# Parameters
CHUNK_SIZE = 2048
SAMPLING_RATE = 8000
BAUD_RATE = 1000000
YLIM = 20000

# Frequency and time axes for plotting
frequencies = fftfreq(CHUNK_SIZE, 1/SAMPLING_RATE)
times = np.arange(CHUNK_SIZE)/SAMPLING_RATE

# Hanning window
window = 0.5 * (1 - np.cos(np.linspace(0, 2*np.pi, CHUNK_SIZE, False)))

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
sns.set_style("dark", {"axes.facecolor": ".1"}) # 
# sns.set_context("paper")
fig = plt.figure()
# fig.patch.set_facecolor('.1')
ax1 = fig.add_subplot(2, 1, 1)
line1, = ax1.plot(times, np.zeros(CHUNK_SIZE), "aquamarine")
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, CHUNK_SIZE/SAMPLING_RATE)
ax1.set_ylim(-128,127)

ax2 = fig.add_subplot(2, 1, 2)
line2, = ax2.plot(fftshift(frequencies), np.zeros(CHUNK_SIZE), "aquamarine")
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Amplitude')
ax2.set_xlim(0, 2000)
ax2.set_ylim(0, YLIM)
text = ax2.text(0, 0, '', va='center', fontdict=font)

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)

port = connectToArduino(BAUD_RATE)


def animate():
    # Update data
    bit_data = port.read(CHUNK_SIZE)
    data = np.frombuffer(bit_data, dtype=np.uint8)
    data = data - np.average(data) # remove DC offset
    spectrum = fft(data)
    amplitudes = np.abs(spectrum)
    # psd = np.abs((spectrum * np.conjugate(spectrum) / CHUNK_SIZE).real)

    # Waveform
    line1.set_ydata(data)

    # Spectrum
    peak_freq_index = np.argmax(amplitudes)
    peak_freq = frequencies[peak_freq_index]
    line2.set_ydata(fftshift(amplitudes))
    text.set_text('{:.2f} Hz'.format(peak_freq))
    text.set_position((peak_freq + 10, min((YLIM - 2000, amplitudes[peak_freq_index]))))  # Update annotation position amplitudes[peak_freq_index]

    # Update the canvas
    canvas.draw()
    canvas.flush_events()

    # Schedule the next update
    root.after(1, animate)


def close_window():
    exit()


root.protocol("WM_DELETE_WINDOW", close_window)

# Schedule the first update
root.after(1, animate)

# Run the Tkinter event loop
root.mainloop()

