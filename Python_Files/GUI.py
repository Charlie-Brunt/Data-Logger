"""
Guitar Companion App

Author: Charlie Brunt

"""
import sys
import os
import tkinter as tk
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import seaborn as sns
import serial
import serial.tools.list_ports
import customtkinter
from numpy_ringbuffer import RingBuffer
from scipy.fft import fft, fftfreq, fftshift
from scipy.signal import find_peaks
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from BlitManager import BlitManager
from PIL import Image, ImageTk


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def connect_to_arduino(baud_rate, serial_number="95530343834351A0B091"):
    """
    Configure the serial port
    """
    for pinfo in serial.tools.list_ports.comports():
        if pinfo.serial_number == serial_number or "Arduino" in pinfo.description:
            return serial.Serial(pinfo.device, baud_rate)
    raise IOError("No Arduino found")


def animate():
    """
    Update plotted data on graphs
    """
    # Update data
    bits = port.read(CHUNK_SIZE//60) # ~ 30 fps
    decoded_bits = np.frombuffer(bits, dtype=np.uint8)
    r.extend(decoded_bits)
    data = np.array(r) # np.frombuffer(bit_data, dtype=np.uint8)
    data = (data - np.average(data))/128 # remove DC offset and normalise
    line1.set_ydata(np.pad(data, (0, CHUNK_SIZE - len(data)))) # Plot waveform

    # Hann window
    windowed_data = np.hanning(len(data)) * data

    # Calculate spectrum
    spectrum = fft(windowed_data)
    # psd = 20*np.log10(np.abs(spectrum))
    psd = 10*np.log10(np.abs((spectrum * np.conjugate(spectrum) / CHUNK_SIZE).real))
    line2.set_ydata(np.pad(fftshift(psd), (0, CHUNK_SIZE - len(data)))) # Plot spectrum

    # Find peaks
    peaks, _ = find_peaks(psd, height=THRESHOLD)
    if peaks.size == 0:
        # If no peaks over threshold, give the strongest frequency
        peak_freq_index = np.argmax(psd)
        peak = psd[peak_freq_index]
        peak_freq = frequencies[peak_freq_index]
    else:
        # Find fundamental peak
        fundamental_index = peaks[0]
        peak = psd[fundamental_index]
        peak_freq = frequencies[fundamental_index]

    # Call tuning function
    closest_note_freq = tune(peak_freq, peak, tuning)

    # Update peak label and line segment between peak and closest note
    if peak > -50 and peak_freq > 30:
        hline.set_ydata([peak,peak])
        hline.set_xdata([peak_freq, closest_note_freq])
        pklabel.set_text('{:.2f} Hz'.format(peak_freq))
        pklabel.set_position((max(40, peak_freq), max(-50, min(YLIM - 3, peak + 1.76))))
    else:
        hline.set_ydata([0,0])
        hline.set_xdata([0,0])
        pklabel.set_text("")

    global timer
    temp = time.time()
    fr_number.set_text("FPS: {:.1f}".format(1.0 / (temp - timer)))
    timer = temp

    # Update tuning lines
    global change_tuning
    if change_tuning:
        change_tuning = False
        i = 0
        for note in tuning:
            f = tuning[note]
            note_lines[i].set_xdata([f])
            note_labels[i].set_text(note)
            note_labels[i].set_position((f, YLIM - 3))
            freq_labels[i].set_text(f)
            freq_labels[i].set_position((f, -59.2))
            i += 1

    # Update the canvas
    bm.update()

    # Schedule the next update
    root.after(1, animate)


def toggle_distortion():
    """
    Toggle distortion effect, change appearance of button and signal a state change to Arduino
    """
    global pedalimg
    global distortion_enabled
    distortion_enabled = not distortion_enabled
    if distortion_enabled:
        pedalimg = ImageTk.PhotoImage(Image.open(resource_path("assets/pedal_on.png")).resize((320,512)))
        pedal_btn.config(image=pedalimg)
        port.write(1)
    else:
        pedalimg = ImageTk.PhotoImage(Image.open(resource_path("assets/pedal.png")).resize((320,512)))
        pedal_btn.config(image=pedalimg)
        port.write(2)
    # print(distortion_enabled)


def tune(peak_frequency, peak, tuning):
    """
    Find closest note and handle GUI updates with tuning instructions
    """
    global tuning_state
    prev_tuning_state = tuning_state
    closest_note, note_freq = min(tuning.items(), key=lambda x: abs(peak_frequency - x[1]))
    error = round(peak_frequency - note_freq, 1)
    try:
        error_c = round(1200 * np.log2(peak_frequency/note_freq), 1)
    except:
        error_c = 0
    if peak > THRESHOLD and peak_frequency > 30:
        if abs(error) < 1:
            # In tune
            tuning_state = "In Tune   "
            if tuning_state != prev_tuning_state:
                tunervar.set(tuning_state)
                note_frame.configure(border_color="#32C671")
                tuner_instruction.config(image=equalimg)
                tuner_instruction.image = equalimg
        elif error < 0:
            # Flat
            tuning_state = "Tune Up"
            if tuning_state != prev_tuning_state:
                tunervar.set(tuning_state)
                note_frame.configure(border_color="#1a1a1a")
                tuner_instruction.config(image=upimg)
                tuner_instruction.image = upimg
        else:
            # Sharp
            tuning_state = "Tune Down"
            if tuning_state != prev_tuning_state:
                tunervar.set(tuning_state)
                note_frame.configure(border_color="#1a1a1a")
                tuner_instruction.config(image=downimg)
                tuner_instruction.image = downimg
        notevar.set(closest_note)
        note_freq_var.set(f"{note_freq} Hz")
        if error_unit_var.get() == "Hz":
            freq_diff_var.set(f"{error} Hz")
        else:
            freq_diff_var.set(f"{error_c} c")
        peak_freq_var.set(f"{round(peak_frequency, 1)} Hz")
    else:
        # Below threshold
        tuning_state = " "
        if tuning_state != prev_tuning_state:
            tunervar.set(tuning_state)
            note_frame.configure(border_color="#1a1a1a")
            tuner_instruction.config(image=noteimg)
            tuner_instruction.image = noteimg
            notevar.set("-")
        note_freq_var.set(" ")
        freq_diff_var.set("-")
        peak_freq_var.set("-")
    return note_freq


def select_tuning():
    """
    Callback function to select a tuning
    """
    global tuning
    global change_tuning
    change_tuning = True
    selection = var.get()
    tuning = tunings[selection]


def toggle_units():
    units = error_unit_var.get()
    if units == "Hz":
        error_unit_var.set("Cents")
    else:
        error_unit_var.set("Hz")



def close_window():
    """
    Callback function to stop executing code when closing a window
    """
    # root.destroy()
    sys.exit()


if __name__== "__main__":
    # Set font family globally
    font_manager._load_fontmanager(try_read_cache=False)
    font_name = "Inter"


    # global variables
    distortion_enabled = False
    change_tuning = False
    timer = 0
    tuning_state = " "

    # Parameters
    CHUNK_SIZE = 32768
    SAMPLING_RATE = 20000
    BAUD_RATE = 1000000
    YLIM = 0 # dB
    THRESHOLD = -15 # dB

    # Ring buffer object
    r = RingBuffer(capacity=CHUNK_SIZE, dtype=np.uint8)

    # Tunings from https://pages.mtu.edu/~suits/notefreqs.html
    standard_tuning = {
        'E2': 82.4, # 82.4
        'A2': 110.0,
        'D3': 146.8,
        'G3': 196.0,
        'B3': 246.9,
        'E4': 329.6
    }

    drop_d_tuning = {
        'D2': 73.4,
        'A2': 110.0,
        'D3': 146.8,
        'G3': 196.0,
        'B3': 246.9,
        'E4': 329.6
    }

    half_step_down_tuning = {
        'Eb2': 77.8,
        'Ab2': 103.8,
        'Db3': 138.6,
        'Gb3': 185.0,
        'Bb3': 233.1,
        'Eb4': 311.1
    }

    open_g_tuning = {
        'D2': 73.4,
        'G2': 98.0,
        'D3': 146.8,
        'G3': 196.0,
        'B3': 246.9,
        'D4': 293.7
    }

    dadgad_tuning = {
        'D2': 73.4,
        'A2': 110.0,
        'D3': 146.8,
        'G3': 196.0,
        'A3': 220.0,
        'D4': 293.7
    }

    open_d_tuning = {
        'D2': 73.4,
        'A2': 110.0,
        'D3': 146.8,
        'F#3': 185.0,
        'A3': 220.0,
        'D4': 293.7
    }

    whole_step_down_tuning = {
        'D2': 73.4,
        'G2': 98.0,
        'C3': 130.8,
        'F3': 174.6,
        'A3': 220.0,
        'D4': 293.7
    }

    tunings = [standard_tuning,
               drop_d_tuning,
               half_step_down_tuning,
               open_g_tuning,
               dadgad_tuning,
               open_d_tuning,
               whole_step_down_tuning]
    
    tuning_labels = ["Standard","Drop D","Half Step","Open G","DADGAD","Open D","Whole Step"]
    tuning = standard_tuning

    # Frequency and time axes for plotting
    frequencies = fftfreq(CHUNK_SIZE, 1/SAMPLING_RATE)
    times = np.arange(CHUNK_SIZE)/SAMPLING_RATE

    # Create the Tkinter GUI window
    # root = tk.Tk()
    customtkinter.set_appearance_mode("Dark")
    root = customtkinter.CTk()
    root.title("Guitar Companion")
    root.geometry("1600x900")
    root.iconbitmap(resource_path("assets/icon.ico"))
    root.protocol("WM_DELETE_WINDOW", close_window)
    root.configure(background="white")

    # Effects frame
    effects_frame = customtkinter.CTkFrame(master=root, width=400, fg_color="#1a1a1a")
    effects_frame.pack(fill=tk.BOTH, side=tk.RIGHT, padx=8, pady=8)
    effects_frame.propagate(False)

    effects_frame_title = tk.Label(
        master=effects_frame,
        text="Effects Window",
        font=(font_name, 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    effects_frame_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    pedalimg = ImageTk.PhotoImage(Image.open(resource_path("assets/pedal.png")).resize((320,512)))
    pedal_btn = tk.Button(
        master=effects_frame,
        image=pedalimg,
        command=toggle_distortion,
        bd=0,
        bg="#1a1a1a",
        activebackground="#1a1a1a"
    )
    pedal_btn.pack(expand=True, padx=20)

    # Graph frame
    graph_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a")
    graph_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=8, pady=8, expand=True)

    graph_frame_title = tk.Label(
        master=graph_frame,
        text="Waveform and Power Spectral Density",
        font=(font_name, 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    graph_frame_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    # Create a Figure object
    fig = plt.figure()
    fig.patch.set_facecolor('.1')

    # Seaborn styles
    sns.set_style("dark", {
        'axes.grid': True,
        'grid.linestyle': '-',
        'grid.color': '0.3',
        'text.color': 'white',
        'xtick.color': 'white',
        'ytick.color': 'white',
        'axes.labelcolor': 'white',
        }
    )

    plt.rcParams["font.family"] = font_name

    # Font dictionary
    font = {
        'family': font_name,
        'color':  'white',
        'weight': 'normal',
        'size': 8
    }

    # Time domain plot setup
    ax1 = fig.add_subplot(2, 1, 1)
    line1, = ax1.plot(times, np.zeros(CHUNK_SIZE), "#7951FF")
    ax1.patch.set_alpha(0)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Amplitude')
    ax1.set_xlim(0, 0.125*CHUNK_SIZE/SAMPLING_RATE)
    ax1.set_ylim(-1,1)
    ax1.grid(axis="x")
    fr_number = ax1.text(0.001, 0.938, '', va='top', ha='left', fontdict=font)

    # Frequency spectrum plot setup
    ax2 = fig.add_subplot(2, 1, 2)
    line2, = ax2.plot(fftshift(frequencies), np.ones(CHUNK_SIZE), color="#7951FF")
    ax2.patch.set_alpha(0)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Power Spectral Density (dB)')
    # ax2.set_yscale("log")
    ax2.set_xscale("log")
    ax2.set_xlim(30, 1000)
    ax2.set_ylim(-60, YLIM)
    ax2.grid(axis="x")
    pklabel = ax2.text(0, 0, '', va='center', fontdict=font)
    fig.subplots_adjust(left=0.07, bottom=0.1, right=0.93, top=0.98, wspace=0.5, hspace=0.3)

    # Setup tuning lines
    note_lines = []
    note_labels = []
    freq_labels = []
    for note in tuning:
        f = tuning[note]
        note_lines.append(ax2.axvline(f, ymin=0.06, ymax=0.93, color ='white', linewidth=1))
        note_labels.append(ax2.text(f, YLIM - 3.47, note, ha="center", fontdict=font))
        freq_labels.append(ax2.text(f, -59.2, f, ha="center", fontdict=font))

    # Horizontal line
    hline, = ax2.plot([0,0], [0,0], ":", color="#afafaf", linewidth=1)

    animated_artists = [line1, line2, pklabel, fr_number, hline] + note_lines + note_labels + freq_labels

    # Create a canvas widget to display the plot
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side="top",fill='both', expand=True, padx=10, pady=10)

    # Create BlitManager object
    bm = BlitManager(canvas, animated_artists)

    # Tuning radio buttons
    radio_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a", height=30)
    radio_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=8, pady=8)
    radio_frame.pack_propagate(False)
    var = tk.IntVar()
    tuning_buttons = [customtkinter.CTkRadioButton(
        radio_frame,
        text=tuning_labels[i],
        variable=var,
        value=i,
        font=(font_name, 10),
        command=select_tuning,
        fg_color="#7951FF",
        hover_color="#3A218E")
        for i in range(len(tunings))]
    for button in tuning_buttons:
        button.pack(anchor=tk.CENTER, side=tk.LEFT, padx=30, expand=True)

    # Note frame
    note_frame = customtkinter.CTkFrame(
        master=root,
        fg_color="#1a1a1a",
        height=250,
        width=250,
        border_width=5,
        border_color="#1a1a1a"
    )
    note_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=8, pady=8)
    note_frame.pack_propagate(False)

    note_label_title = tk.Label(
        master=note_frame,
        text="Closest Note",
        font=(font_name, 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    note_label_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    notevar = tk.StringVar()
    notevar.set("-")
    note_label = tk.Label(
        master=note_frame,
        textvar=notevar,
        font=(font_name, 80),
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    note_label.pack(expand=True, padx=20)

    # note_freq_title = tk.Label(
    #     master=note_frame,
    #     text="Note Frequency",
    #     font=(font_name, 10),
    #     bg="#1a1a1a",
    #     fg="#5f5f5f"
    # )
    # note_freq_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    note_freq_var = tk.StringVar()
    note_freq_var.set(" ")
    note_freq_label = tk.Label(
        master=note_frame,
        textvar=note_freq_var,
        font=(font_name, 15),
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    note_freq_label.pack(side=tk.TOP, expand=True, anchor=tk.N)

    # Frequency frame
    freq_frame = customtkinter.CTkFrame(
        master=root,
        fg_color="#1a1a1a",
        height=250,
        width=250,
    )
    freq_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=8, pady=8)
    freq_frame.pack_propagate(False)

    peak_freq_title = tk.Label(
        master=freq_frame,
        text="Peak Frequency",
        font=(font_name, 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    peak_freq_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    peak_freq_var = tk.StringVar()
    peak_freq_var.set("-")
    peak_freq_label = tk.Label(
        master=freq_frame,
        textvar=peak_freq_var,
        font=(font_name, 40),
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    peak_freq_label.pack(side=tk.TOP, expand=True, pady=5)

    freq_diff_title = tk.Label(
        master=freq_frame,
        text="Error",
        font=(font_name, 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    freq_diff_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    freq_diff_var = tk.StringVar()
    freq_diff_var.set("-")
    freq_diff_label = tk.Label(
        master=freq_frame,
        textvar=freq_diff_var,
        font=(font_name, 40),
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    freq_diff_label.pack(side=tk.TOP, expand=True, pady=5)

    error_unit_var = tk.StringVar()
    error_unit_var.set("Hz")
    error_unit_button = customtkinter.CTkButton(
        master=freq_frame,
        textvariable=error_unit_var,
        fg_color="#2a2a2a",
        hover_color="#6a6a6a",
        command=toggle_units,
        font=(font_name, 10),
        width=40,
        height=15,
    )
    error_unit_button.pack(side=tk.TOP, anchor=tk.SE, padx=10, pady=5)

    # Tuner frame
    tuner_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a")
    tuner_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=8, pady=8, expand=True)

    tuner_frame_title = tk.Label(
        master=tuner_frame,
        text="Tuning",
        font=(font_name, 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    tuner_frame_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    noteimg = ImageTk.PhotoImage(Image.open(resource_path("assets/note.png")).resize((150,150)))
    equalimg = ImageTk.PhotoImage(Image.open(resource_path("assets/equal.png")).resize((70,70)))
    upimg = ImageTk.PhotoImage(Image.open(resource_path("assets/up.png")).resize((150,150)))
    downimg = ImageTk.PhotoImage(Image.open(resource_path("assets/down.png")).resize((150,150)))
    tunervar = tk.StringVar()
    tunervar.set(" ")
    tuner_instruction = tk.Label(
        master=tuner_frame,
        textvar=tunervar,
        font=(font_name, 60), 
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white",
        compound="right",
        image=noteimg
    )
    tuner_instruction.pack(expand=True, padx=20, pady=20, side=tk.TOP)

    # Open Arduino COM port
    port = connect_to_arduino(BAUD_RATE)

    canvas.draw()

    # Schedule the first update
    root.after(1, animate)

    # Run the Tkinter event loop
    root.mainloop()
