import numpy as np
import serial
import scipy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

# Configure the serial port
port = serial.Serial('COM5', 19200)  # Replace 'COM1' with the appropriate serial port
fftbuffer = 256
sample_rate = 10000
buffer_size = fftbuffer * 5  # Number of bytes to read from serial

# Create the Tkinter GUI window
window = tk.Tk()
window.title("Audio FFT Analyzer")

# Create a Figure object and a subplot
fig = plt.Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=window)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)

# data = port.read(buffer_size)
# print(data)
# print(np.frombuffer(data, dtype=np.uint8))


def update_f():
    data = port.read(buffer_size)
    samples = np.frombuffer(data, dtype=np.uint8)
    ax.clear()

    # Plot the spectrum
    ax.plot(samples)
    ax.set_xlabel('Time')
    ax.set_ylabel('Amplitude')
    # Update the canvas
    canvas.draw()

    # Schedule the next update
    window.after(100, update_f)

    

# Function to update the FFT plot
def update_fft():
    # Read the audio data from the serial port
    data = port.read(buffer_size)

    # Convert the received data into an array of integers
    samples = np.frombuffer(data, dtype=np.uint8)

    # Perform FFT on the samples
    spectrum = sp.fft.fft(samples)

    # Calculate the amplitudes of the spectrum
    amplitudes = np.abs(spectrum)
    xf = sp.fft.fftfreq(buffer_size, 1/sample_rate)


    # Clear the previous plot
    ax.clear()

    # Plot the spectrum
    ax.plot(xf, amplitudes)
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Amplitude')
    ax.set_xlim(0, 2000)

    # Update the canvas
    canvas.draw()

    # Schedule the next update
    window.after(10, update_fft)

# Schedule the first update
window.after(100, update_fft)

# Run the Tkinter event loop
window.mainloop()