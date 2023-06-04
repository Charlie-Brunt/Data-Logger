"""
Guitar Companion App

Author: Charlie Brunt

"""
import tkinter as tk
import time
import numpy as np
import matplotlib.pyplot as plt
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


def connect_to_arduino(baud_rate, serial_number="95530343834351A0B091"):
    """
    Configure the serial port
    """
    for pinfo in serial.tools.list_ports.comports():
        if pinfo.serial_number == serial_number:
            return serial.Serial(pinfo.device, baud_rate)
    raise IOError("No Arduino found")


def animate():
    """
    Update plotted data on graphs
    """
    # Update data
    bits = port.read(CHUNK_SIZE//30) # ~ 30 fps
    decoded_bits = np.frombuffer(bits, dtype=np.uint8)
    r.extend(decoded_bits)
    data = np.array(r) # np.frombuffer(bit_data, dtype=np.uint8)
    data = data - np.average(data) # remove DC offset
    line1.set_ydata(np.pad(data, (0, CHUNK_SIZE - len(data)))) # Plot waveform

    # Calculate spectrum
    spectrum = fft(data)
    # psd = np.abs(spectrum)
    psd = np.abs((spectrum * np.conjugate(spectrum) / CHUNK_SIZE).real)
    line2.set_ydata(np.pad(fftshift(psd), (0, CHUNK_SIZE - len(data)))) # Plot spectrum
    
    # Find peaks
    peaks, _ = find_peaks(psd, threshold=10000)
    if peaks.size == 0:
        # If no peaks over 10000, give the strongest frequency
        peak_freq_index = np.argmax(psd)
        peak = psd[peak_freq_index]
        peak_freq = frequencies[peak_freq_index]
    else:
        # Find fundamental peak
        fundamental_index = peaks[0]
        peak = psd[fundamental_index]
        peak_freq = frequencies[fundamental_index]
    pklabel.set_text('{:.2f} Hz'.format(peak_freq))
    pklabel.set_position((
        max(40, peak_freq),
        max(10, min(YLIM/2, peak*1.5))
    ))
    if peak < 10:
        pklabel.set_position((32, 3))
        pklabel.set_text('{:.2f} Hz'.format(0.00))
    
    global timer
    temp = time.time()
    fr_number.set_text("FPS: {:.2f}".format(1.0 / (temp - timer)))
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
            note_labels[i].set_position((f, 0.5*YLIM))
            freq_labels[i].set_text(f)
            freq_labels[i].set_position((f, 1.2))
            i += 1

    # Tuning algorithm
    closest_note_freq = tune(peak_freq, peak, tuning)
    hline.set_ydata([peak,peak])
    hline.set_xdata([peak_freq, closest_note_freq])

    # Update the canvas
    bm.update()

    # Schedule the next update
    root.after(5, animate)


def toggle_distortion():
    """
    Toggle distortion effect, change appearance of button and signal a state change to Arduino
    """
    global pedalimg
    global distortion_enabled
    distortion_enabled = not distortion_enabled
    if distortion_enabled:
        pedalimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/pedal_on.png").resize((320,512)))
        pedal_btn.config(image=pedalimg)
        port.write(1)
    else:
        pedalimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/pedal.png").resize((320,512)))
        pedal_btn.config(image=pedalimg)
        port.write(2)
    # print(distortion_enabled)


def tune(peak_frequency, peak, tuning):
    """
    Find closest note and give tuning instructions
    """
    closest_note, note_freq = min(tuning.items(), key=lambda x: abs(peak_frequency - x[1]))
    error = round(peak_frequency - note_freq, 1)
    if peak > THRESHOLD and peak_frequency > 10:
        if abs(error) < 0.5:
            notevar.set(closest_note)
            tunervar.set("In Tune")
            note_freq_var.set(f"{note_freq} Hz")
            freq_diff_var.set(f"{error} Hz")
            peak_freq_var.set(f"{round(peak_frequency, 1)} Hz")
            note_frame.configure(border_color="green")
            equalimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/equal.png").resize((150,150)))
            tuner_instruction.config(image=equalimg)
            tuner_instruction.image = equalimg
        elif error < 0:
            notevar.set(closest_note)
            tunervar.set("Tune Up")
            note_freq_var.set(f"{note_freq} Hz")
            freq_diff_var.set(f"{error} Hz")
            peak_freq_var.set(f"{round(peak_frequency, 1)} Hz")
            note_frame.configure(border_color="#1a1a1a")
            upimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/up.png").resize((150,150)))
            tuner_instruction.config(image=upimg)
            tuner_instruction.image = upimg
        else:
            notevar.set(closest_note)
            tunervar.set("Tune Down")
            note_freq_var.set(f"{note_freq} Hz")
            freq_diff_var.set(f"{error} Hz")
            peak_freq_var.set(f"{round(peak_frequency, 1)} Hz")
            note_frame.configure(border_color="#1a1a1a")
            downimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/down.png").resize((150,150)))
            tuner_instruction.config(image=downimg)
            tuner_instruction.image = downimg
    else:
        tuner_instruction.config(image=noteimg)
        tuner_instruction.image = noteimg
        notevar.set("-")
        tunervar.set(" ")
        note_freq_var.set(" ")
        freq_diff_var.set("-")
        peak_freq_var.set("-")
        note_frame.configure(border_color="#1a1a1a")
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


def close_window():
    """
    Callback function to stop executing code when closing a window
    """
    exit()


if __name__== "__main__":
    # global variables
    distortion_enabled = False
    change_tuning = False
    timer = 0

    # Parameters
    CHUNK_SIZE = 32768
    SAMPLING_RATE = 20000
    BAUD_RATE = 1000000
    YLIM = 1000000 # 20000
    THRESHOLD = 100

    # Ring buffer object
    r = RingBuffer(capacity=CHUNK_SIZE, dtype=np.uint8)

    # Tunings from https://pages.mtu.edu/~suits/notefreqs.html
    standard_tuning = {
        'E2': 82.4,
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
        'F♯3': 185.0,
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
    root.iconbitmap("Guitar Companion/assets/icon.ico")
    root.protocol("WM_DELETE_WINDOW", close_window)
    root.configure(background="white")

    # Effects frame
    effects_frame = customtkinter.CTkFrame(master=root, width=400, fg_color="#1a1a1a")
    effects_frame.pack(fill=tk.BOTH, side=tk.RIGHT, padx=8, pady=8)
    effects_frame.propagate(False)

    effects_frame_title = tk.Label(
        master=effects_frame,
        text="Effects Window",
        font=("sans-serif", 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    effects_frame_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    pedalimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/pedal.png").resize((320,512)))
    pedal_btn = tk.Button(master=effects_frame, image=pedalimg, command=toggle_distortion, 
                        bd=0, bg="#1a1a1a", activebackground="#1a1a1a")
    pedal_btn.pack(expand=True, padx=20)

    # Graph frame
    graph_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a")
    graph_frame.pack(fill=tk.BOTH, side=tk.TOP, padx=8, pady=8, expand=True)
    
    graph_frame_title = tk.Label(
        master=graph_frame,
        text="Waveform and Power Spectral Density",
        font=("sans-serif", 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    graph_frame_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

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
    ax1.set_xlim(0, 0.125*CHUNK_SIZE/SAMPLING_RATE)
    ax1.set_ylim(-128,127)
    ax1.grid(axis="x")
    fr_number = ax1.text(0.001, 120, '', va='top', ha='left', fontdict=font)

    # Frequency spectrum plot setup
    ax2 = fig.add_subplot(2, 1, 2)
    line2, = ax2.plot(fftshift(frequencies), np.ones(CHUNK_SIZE), color="#7951FF")
    ax2.patch.set_alpha(0)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Power Spectral Density')
    ax2.set_yscale("log")
    ax2.set_xscale("log")
    ax2.set_xlim(30, 1000)
    ax2.set_ylim(1, YLIM)
    ax2.grid(axis="x")
    pklabel = ax2.text(0, 0, '', va='center', fontdict=font)
    fig.subplots_adjust(left=0.07, bottom=0.1, right=0.93, top=1, wspace=0.5, hspace=0.3)

    # Setup tuning lines
    note_lines = []
    note_labels = []
    freq_labels = []
    for note in tuning:
        f = tuning[note]
        note_lines.append(ax2.axvline(f, ymin=0.06, ymax=0.93, color ='white', linewidth=1))
        note_labels.append(ax2.text(f, 0.45*YLIM, note, ha="center", fontdict=font))
        freq_labels.append(ax2.text(f, 1.2, f, ha="center", fontdict=font))
 
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
        font=("sans-serif", 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    note_label_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    notevar = tk.StringVar()
    notevar.set("-")
    note_label = tk.Label(
        master=note_frame,
        textvar=notevar,
        font=("sans-serif", 80),
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    note_label.pack(expand=True, padx=20)

    # note_freq_title = tk.Label(
    #     master=note_frame,
    #     text="Note Frequency",
    #     font=("sans-serif", 10),
    #     bg="#1a1a1a",
    #     fg="#5f5f5f"
    # )
    # note_freq_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    note_freq_var = tk.StringVar()
    note_freq_var.set(" ")
    note_freq_label = tk.Label(
        master=note_frame,
        textvar=note_freq_var,
        font=("sans-serif", 15),
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
        font=("sans-serif", 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    peak_freq_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    peak_freq_var = tk.StringVar()
    peak_freq_var.set("-")
    peak_freq_label = tk.Label(
        master=freq_frame,
        textvar=peak_freq_var,
        font=("sans-serif", 40),
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    peak_freq_label.pack(side=tk.TOP, expand=True, pady=10)

    freq_diff_title = tk.Label(
        master=freq_frame,
        text="Frequency Error",
        font=("sans-serif", 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    freq_diff_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)

    freq_diff_var = tk.StringVar()
    freq_diff_var.set("-")
    freq_diff_label = tk.Label(
        master=freq_frame,
        textvar=freq_diff_var,
        font=("sans-serif", 40), 
        anchor=tk.CENTER,
        bg="#1a1a1a",
        fg="white"
    )
    freq_diff_label.pack(side=tk.TOP, expand=True, pady=10)

    # Tuner frame
    tuner_frame = customtkinter.CTkFrame(master=root, fg_color="#1a1a1a")
    tuner_frame.pack(fill=tk.BOTH, side=tk.LEFT, padx=8, pady=8, expand=True)

    tuner_frame_title = tk.Label(
        master=tuner_frame,
        text="Tuning",
        font=("sans-serif", 10),
        bg="#1a1a1a",
        fg="#5f5f5f"
    )
    tuner_frame_title.pack(side=tk.TOP, anchor=tk.NW, padx=10, pady=5)
    
    noteimg = ImageTk.PhotoImage(Image.open("Guitar Companion/assets/note.png").resize((150,150)))
    tunervar = tk.StringVar()
    tunervar.set(" ")
    tuner_instruction = tk.Label(
        master=tuner_frame,
        textvar=tunervar,
        font=("sans-serif", 60), 
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
    root.after(5, animate)

    # Run the Tkinter event loop
    root.mainloop()
