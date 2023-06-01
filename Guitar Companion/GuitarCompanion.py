"""
Guitar Companion app

"""
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
import seaborn as sns
import serial
import serial.tools.list_ports
import time
import customtkinter
from scipy.fft import fft, fftfreq, fftshift
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from BlitManager import BlitManager
from tkinter import ttk
from ttkthemes import ThemedTk
from PIL import Image, ImageTk

def connect_to_arduino(BAUD_RATE, serial_number="95530343834351A0B091"):
    """
    Configure the serial port
    """
    for pinfo in serial.tools.list_ports.comports():
        if pinfo.serial_number == serial_number:
            return serial.Serial(pinfo.device, BAUD_RATE)
    raise IOError("No Arduino found")


def animate():
    """
    Update plotted data on graphs
    """
    start_time = time.time()

    # Update data
    bit_data = port.read(CHUNK_SIZE)
    data = np.frombuffer(bit_data, dtype=np.uint8)
    data = data - np.average(data) # remove DC offset
    spectrum = fft(data)
    # amplitudes = np.abs(spectrum)
    psd = np.abs((spectrum * np.conjugate(spectrum) / CHUNK_SIZE).real)

    # Waveform
    line1.set_ydata(data)

    # Spectrum
    peak_freq_index = np.argmax(psd)
    peak_freq = frequencies[peak_freq_index]
    line2.set_ydata(fftshift(psd))
    pklabel.set_text('{:.2f} Hz'.format(peak_freq))
    pklabel.set_position((peak_freq + 10, min((YLIM - 0.5*YLIM, psd[peak_freq_index]))))
    try:
        fr_number.set_text("FPS: {:.2f}".format(1.0 / (time.time() - start_time)))
    except:
        pass
    
    # Update tuning lines
    global switch_tuning
    if switch_tuning == True:
        switch_tuning = False
        i = 0
        for note in tuning:
            f = tuning[note]
            note_lines[i].set_xdata(f)
            note_labels[i].set_text(note)
            note_labels[i].set_position((f, 0.55*YLIM))
            freq_labels[i].set_text(f)
            freq_labels[i].set_position((f, 1.1))
            i +=1
    
    # Update the canvas
    bm.update()

    # Schedule the next update
    root.after(5, animate)


def close_window():
    exit()


def toggle_distortion():
    """
    Toggle distortion effect and change appearance of button
    """
    global pedalimg
    global distortion
    distortion = not(distortion) 
    if distortion == True:
        pedalimg = ImageTk.PhotoImage(Image.open("Assets/pedal_on.png").resize((300,480)))
        pedal_btn.config(image=pedalimg)
    else:
        pedalimg = ImageTk.PhotoImage(Image.open("Assets/pedal.png").resize((300,480)))
        pedal_btn.config(image=pedalimg)
    print(distortion)


def tune(freq, tuning):
    """
    Find closest note and give tuning instructions
    """
    closest_note, note_freq = min(tuning.items(), key=lambda x: abs(freq - x[1]))
    if abs(freq - note_freq) < 1.5:
        instruction = "In Tune"
    elif freq - note_freq < 0:
        instruction = "Tune Up"
    else:
        instruction = "Tune Down"
    return closest_note, instruction


def select_tuning():
   global tuning
   global switch_tuning
   switch_tuning = True
   selection = var.get()
   tuning = tunings[selection]
   print(tuning)



# global variables
distortion = False
switch_tuning = False

# Parameters
CHUNK_SIZE = 1024
SAMPLING_RATE = 8000
BAUD_RATE = 1000000
YLIM = 1000000 # 20000

# Tunings
STANDARD_TUNING = {"E2": 82.4,
         "A2": 110.0,
         "D3": 146.8,
         "G3": 196.0,
         "B3": 246.9,
         "E4": 329.6}
DROP_D = {"D2": 73.4,
         "A2": 110.0,
         "D3": 146.8,
         "G3": 196.0,
         "B3": 246.9,
         "E4": 329.6}
HALF_STEP = {"Eb2": 77.8,
         "Ab2": 103.8,
         "Db3": 138.6,
         "Gb3": 185.0,
         "Bb3": 233.1,
         "Eb4": 311.1}
FULL_STEP = {"D2": 73.4,
         "G2": 98,
         "C3": 130.8,
         "F3": 174.6,
         "A3": 220,
         "D4": 293.7}

tunings = [STANDARD_TUNING, DROP_D, HALF_STEP, FULL_STEP]
tuning = STANDARD_TUNING

# Frequency and time axes for plotting
frequencies = fftfreq(CHUNK_SIZE, 1/SAMPLING_RATE)
times = np.arange(CHUNK_SIZE)/SAMPLING_RATE

# Create the Tkinter GUI window
# root = tk.Tk()
root = customtkinter.CTk()
root.title("Guitar Companion")
root.geometry("1280x720")
root.state('zoomed')
root.iconbitmap("Assets/icon.ico")
root.protocol("WM_DELETE_WINDOW", close_window)

# Pedal frame / button
pedal_frame = tk.Frame(master=root, width=100, bg="#1a1a1a") # , bg="#1a1a1a"
pedal_frame.pack(fill=tk.BOTH, side=tk.RIGHT, padx=5, pady=5)
pedalimg = ImageTk.PhotoImage(Image.open("Assets/pedal.png").resize((300,480)))
pedal_btn = tk.Button(master=pedal_frame, image=pedalimg, command=toggle_distortion, bd=0, bg="#1a1a1a", activebackground="#1a1a1a")
pedal_btn.pack(expand=True, padx=20, pady=20)

# radio button frame
radio_frame = tk.Frame(master=root, bg="#1a1a1a")
radio_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5)
var = tk.IntVar()
std_tuning = customtkinter.CTkRadioButton(radio_frame, text="E-A-D-G-B-E", variable=var, value=0,
                  command=select_tuning) # .grid(row=0, column=1)
std_tuning.pack(anchor=tk.W, side=tk.LEFT, ipadx=20)
drop_d_tuning = customtkinter.CTkRadioButton(radio_frame, text="D-A-D-G-B-E", variable=var, value=1,
                  command=select_tuning) # .grid(row=0, column=2)
drop_d_tuning.pack(anchor=tk.W, side=tk.LEFT, ipadx=20)
half_step_tuning = customtkinter.CTkRadioButton(radio_frame, text="Eb-Ab-Db-Gb-Bb-Eb", variable=var, value=2,
                  command=select_tuning) # .grid(row=0, column=3)
half_step_tuning.pack(anchor=tk.W, side=tk.LEFT, ipadx=20)
full_step_tuning = customtkinter.CTkRadioButton(radio_frame, text="D-G-C-F-A-D", variable=var, value=3,
                  command=select_tuning) # .grid(row=0, column=4)
full_step_tuning.pack(anchor=tk.W, side=tk.LEFT)

# Graph frame
graph_frame = tk.Frame(master=root, width=200, height=100) #bg="#1a1a1a", bd="5", relief="solid"
graph_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=5, pady=5, expand=True)

# Create a Figure object
fig = plt.figure()
fig.patch.set_facecolor('.1')

# Font dictionary
font = {'family': 'sans-serif',
        'color':  'white',
        'weight': 'normal',
        'size': 8}

# Seaborn styles
sns.set_style("dark", {'axes.facecolor': '0.1',
                       'axes.grid': True,
                       'grid.linestyle': '-',
                       'grid.color': '0.3',
                       'text.color': 'white',
                       'xtick.color': 'white',
                       'ytick.color': 'white',
                       'axes.labelcolor': 'white'}
)

# Time domain plot setup
ax1 = fig.add_subplot(2, 1, 1)
line1, = ax1.plot(times, np.zeros(CHUNK_SIZE), "aquamarine")
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, CHUNK_SIZE/SAMPLING_RATE)
ax1.set_ylim(-128,127)
ax1.grid(axis="x")
fr_number = ax1.text(0.001, 120, '', va='top', ha='left', fontdict=font)

# Frequency spectrum plot setup
ax2 = fig.add_subplot(2, 1, 2)
line2, = ax2.plot(fftshift(frequencies), np.ones(CHUNK_SIZE), color="aquamarine")
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Amplitude')
ax2.set_yscale("log")
ax2.set_xscale("log")
ax2.set_xlim(30, 1000)
ax2.set_ylim(1, YLIM)
ax2.grid(axis="x")
pklabel = ax2.text(0, 0, '', va='center', fontdict=font)

# Setup tuning lines
note_lines = []
note_labels = []
freq_labels = []

for note in tuning:
    f = tuning[note]
    note_lines.append(ax2.axvline(f, ymin=0.05, ymax=0.95, color ='white', linewidth=1))
    note_labels.append(ax2.text(f, 0.55*YLIM, note, ha="center", fontdict=font))
    freq_labels.append(ax2.text(f, 1.1, f, ha="center", fontdict=font))

animated_artists = [line1, line2, pklabel, fr_number] + note_lines + note_labels + freq_labels

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(side="top",fill='both',expand=True)

# Open Arduino COM port
port = connect_to_arduino(BAUD_RATE)

# Create BlitManager object
bm = BlitManager(canvas, animated_artists)

# Schedule the first update
root.after(5, animate)

# Run the Tkinter event loop
root.mainloop()
