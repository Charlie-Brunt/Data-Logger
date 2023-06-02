"""
Guitar Companion App

Author: Charlie Brunt

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


# global variables
distortion = False
switch_tuning = False
pause = False

# Parameters
CHUNK_SIZE = 1024
SAMPLING_RATE = 8000
BAUD_RATE = 1000000
YLIM = 1000000 # 20000
THRESHOLD = 10


def connect_to_arduino(BAUD_RATE, serial_number="95530343834351A0B091"):
    """
    Configure the serial port
    """
    for pinfo in serial.tools.list_ports.comports():
        if pinfo.serial_number == serial_number:
            return serial.Serial(pinfo.device, BAUD_RATE)
    # raise IOError("No Arduino found")


def animate():
    """
    Update plotted data on graphs
    """
    start_time = time.time()

    # Update data
    try:
        bit_data = port.read(CHUNK_SIZE)
        data = np.frombuffer(bit_data, dtype=np.uint8)
        data = data - np.average(data) # remove DC offset
        spectrum = fft(data)
        # amplitudes = np.abs(spectrum)
        psd = np.abs((spectrum * np.conjugate(spectrum) / CHUNK_SIZE).real)
        
        if pause == False:
            # Waveform
            line1.set_ydata(data)

            # Spectrum
            peak_freq_index = np.argmax(psd)
            peak_freq = frequencies[peak_freq_index]
            peak = psd[peak_freq_index]
            line2.set_ydata(fftshift(psd))
            pklabel.set_text('{:.2f} Hz'.format(peak_freq))
            pklabel.set_position((max(peak_freq*1.1, 40), min((YLIM - 0.5*YLIM, peak))))
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
            note_labels[i].set_position((f, 0.5*YLIM))
            freq_labels[i].set_text(f)
            freq_labels[i].set_position((f, 1.2))
            i +=1
    
    # Update the canvas
    bm.update()

    # Tuning algorithm
    try:
        tune(peak_freq, peak, tuning)
    except:
        pass

    # Schedule the next update
    root.after(5, animate)


def close_window():
    exit()


def toggle_distortion():
    """
    Toggle distortion effect, change appearance of button and signal a state change to Arduino
    """
    global pedalimg
    global distortion
    distortion = not distortion
    if distortion == True:
        pedalimg = ImageTk.PhotoImage(Image.open("Assets/pedal_on.png")) # .resize((300,480))
        pedal_btn.config(image=pedalimg)
        try:
            port.write(1)
        except:
            pass
    else:
        pedalimg = ImageTk.PhotoImage(Image.open("Assets/pedal.png")) # .resize((300,480))
        pedal_btn.config(image=pedalimg)
        try:
            port.write(0)
        except:
            pass
    print(distortion)
    


def tune(peak_frequency, peak, tuning):
    """
    Find closest note and give tuning instructions
    """
    noteimg = ImageTk.PhotoImage(Image.open("Assets/note.png").resize((200,200)))
    upimg = ImageTk.PhotoImage(Image.open("Assets/up.png").resize((200,200)))
    downimg = ImageTk.PhotoImage(Image.open("Assets/down.png").resize((200,200)))
    equalimg = ImageTk.PhotoImage(Image.open("Assets/equal.png").resize((200,200)))
    closest_note, note_freq = min(tuning.items(), key=lambda x: abs(peak_frequency - x[1]))
    if peak > THRESHOLD:
        if abs(peak_frequency - note_freq) < 1.5:
            notevar.set(closest_note)
            tunervar.set("In Tune")
            note_frame.config(border_color="green")
            tuner_instruction.config(image=equalimg)
        elif peak_frequency - note_freq < 0:
            notevar.set(closest_note)
            tunervar.set("Tune Up")
            note_frame.config(border_color="white")
            tuner_instruction.config(image=upimg)
        else:
            notevar.set(closest_note)
            tunervar.set("Tune Down")
            note_frame.config(border_color="white")
            tuner_instruction.config(image=downimg)
    else:
        tuner_instruction.config(image=noteimg)
        notevar.set("-")
        tunervar.set(" ")
        
    


def select_tuning():
   global tuning
   global switch_tuning
   switch_tuning = True
   selection = var.get()
   tuning = tunings[selection]
   print(tuning)


def pause_button():
    global pause
    pause = not pause


# Tunings from https://pages.mtu.edu/~suits/notefreqs.html
STANDARD = {
    "E2": 82.4,
    "A2": 110.0,
    "D3": 146.8,
    "G3": 196.0,
    "B3": 246.9,
    "E4": 329.6,
}
DROP_D = {
    "D2": 73.4,
    "A2": 110.0,
    "D3": 146.8,
    "G3": 196.0,
    "B3": 246.9,
    "E4": 329.6,
}
E_FLAT_STANDARD = {
    "Eb2": 77.8,
    "Ab2": 103.8,
    "Db3": 138.6,
    "Gb3": 185.0,
    "Bb3": 233.1,
    "Eb4": 311.1,
}
D_STANDARD = {
    "D2": 73.4,
    "G2": 98,
    "C3": 130.8,
    "F3": 174.6,
    "A3": 220,
    "D4": 293.7,
}
C_SHARP_STANDARD = {
    "C#2": 69.3,
    "F#2": 92.5,
    "B2": 123.5,
    "E3": 164.8,
    "G#3": 207.7,
    "C#4": 277.2,
}

tunings = [STANDARD, DROP_D, E_FLAT_STANDARD, D_STANDARD, C_SHARP_STANDARD]
tuning = STANDARD

# Frequency and time axes for plotting
frequencies = fftfreq(CHUNK_SIZE, 1/SAMPLING_RATE)
times = np.arange(CHUNK_SIZE)/SAMPLING_RATE

# Create the Tkinter GUI window
# root = tk.Tk()
root = customtkinter.CTk()
root.title("Guitar Companion")
root.geometry("1600x900")
root.iconbitmap("Assets/icon.ico")
root.protocol("WM_DELETE_WINDOW", close_window)
root.configure(background="white")

# Pedal frame / button
pedal_frame = customtkinter.CTkFrame(master=root, width=400, fg_color="#1a1a1a") # , bg="#1a1a1a"
pedal_frame.pack(fill=tk.BOTH, side=tk.RIGHT, padx=8, pady=8)
pedalimg = ImageTk.PhotoImage(Image.open("Assets/pedal.png")) # .resize((300,480))
pedal_btn = tk.Button(master=pedal_frame, image=pedalimg, command=toggle_distortion, bd=0, bg="#1a1a1a", activebackground="#1a1a1a")
pedal_btn.pack(expand=True, padx=20, pady=20)

# Tuning radio buttons
radio_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a", height=30)
radio_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=8, pady=8)
radio_frame.pack_propagate(False)
var = tk.IntVar()
std = customtkinter.CTkRadioButton(radio_frame, text="Standard", variable=var, value=0,
                  command=select_tuning) # .grid(row=0, column=1)
std.pack(anchor=tk.W, side=tk.LEFT, padx=60)
drop_d = customtkinter.CTkRadioButton(radio_frame, text="Drop D", variable=var, value=1,
                  command=select_tuning) # .grid(row=0, column=2)
drop_d.pack(anchor=tk.W, side=tk.LEFT, padx=60)
eb_std = customtkinter.CTkRadioButton(radio_frame, text="Eb Standard", variable=var, value=2,
                  command=select_tuning) # .grid(row=0, column=3)
eb_std.pack(anchor=tk.W, side=tk.LEFT, padx=60)
d_std = customtkinter.CTkRadioButton(radio_frame, text="D Standard", variable=var, value=3,
                  command=select_tuning) # .grid(row=0, column=4)
d_std.pack(anchor=tk.W, side=tk.LEFT, padx=60)
csharp_std = customtkinter.CTkRadioButton(radio_frame, text="C# Standard", variable=var, value=4,
                  command=select_tuning) # .grid(row=0, column=4)
csharp_std.pack(anchor=tk.W, side=tk.LEFT, padx=60)

# Graph frame
graph_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a") #bg="#1a1a1a", bd="5", relief="solid"
graph_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=8, pady=8, expand=True)

# Note frame
notevar = tk.StringVar()
note_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a", height=250, width=250, border_width=5, border_color="#1a1a1a")
note_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=8, pady=8)
note_frame.pack_propagate(False)
note_label = tk.Label(master=note_frame, textvar=notevar, font=("sans-serif", 80), anchor=tk.CENTER, bg="#1a1a1a", fg="white")
notevar.set("E")
note_label.pack(expand=True, padx=20, pady=20)

# Tuner frame
tunervar = tk.StringVar()
tuner_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a")
tuner_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=8, pady=8, expand=True)
noteimg = ImageTk.PhotoImage(Image.open("Assets/note.png").resize((200,200)))
upimg = ImageTk.PhotoImage(Image.open("Assets/up.png").resize((200,200)))
downimg = ImageTk.PhotoImage(Image.open("Assets/down.png").resize((200,200)))
equalimg = ImageTk.PhotoImage(Image.open("Assets/equal.png").resize((200,200)))
tuner_instruction = tk.Label(master=tuner_frame, textvar=tunervar, font=("sans-serif", 80), anchor=tk.CENTER, bg="#1a1a1a", fg="white", compound="right", image=noteimg)
tunervar.set(" ")
tuner_instruction.pack(expand=True, padx=60, pady=20, side=tk.LEFT)

# Create a Figure object
fig = plt.figure()
fig.patch.set_facecolor('.1')

# Font dictionary
font = {
    'family': 'sans-serif',
    'color':  'white',
    'weight': 'normal',
    'size': 8
}

# Seaborn styles
sns.set_style("dark", {
    'axes.grid': True,
    'grid.linestyle': '-',
    'grid.color': '0.3',
    'text.color': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'axes.labelcolor': 'white'
    }
)

# Time domain plot setup
ax1 = fig.add_subplot(2, 1, 1)
line1, = ax1.plot(times, np.zeros(CHUNK_SIZE), "#7951FF")
ax1.patch.set_alpha(0)
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude')
ax1.set_xlim(0, CHUNK_SIZE/SAMPLING_RATE)
ax1.set_ylim(-128,127)
ax1.grid(axis="x")
fr_number = ax1.text(0.001, 120, '', va='top', ha='left', fontdict=font)

# Frequency spectrum plot setup
ax2 = fig.add_subplot(2, 1, 2)
line2, = ax2.plot(fftshift(frequencies), np.ones(CHUNK_SIZE), color="#7951FF")
ax2.patch.set_alpha(0)
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Amplitude')
ax2.set_yscale("log")
ax2.set_xscale("log")
ax2.set_xlim(30, 1000)
ax2.set_ylim(1, YLIM)
ax2.grid(axis="x")
pklabel = ax2.text(0, 0, '', va='center', fontdict=font)
fig.subplots_adjust(hspace=0.5)

# Setup tuning lines
note_lines = []
note_labels = []
freq_labels = []

for note in tuning:
    f = tuning[note]
    note_lines.append(ax2.axvline(f, ymin=0.06, ymax=0.94, color ='white', linewidth=1))
    note_labels.append(ax2.text(f, 0.5*YLIM, note, ha="center", fontdict=font))
    freq_labels.append(ax2.text(f, 1.2, f, ha="center", fontdict=font))

animated_artists = [line1, line2, pklabel, fr_number] + note_lines + note_labels + freq_labels

# Create a canvas widget to display the plot
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(side="top",fill='both', expand=True)

# Open Arduino COM port
port = connect_to_arduino(BAUD_RATE)

# Create BlitManager object
bm = BlitManager(canvas, animated_artists)
canvas.draw()

# Schedule the first update
root.after(5, animate)

# Run the Tkinter event loop
root.mainloop()
