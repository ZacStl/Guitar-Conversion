# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 15:14:09 2022

@author: bassz
"""


import numpy as np
import pyaudio
import time
import threading
from scipy import signal
from scipy.io.wavfile import read
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os


class Stream:
    def __init__(self, master):

        self.master = master
        self.rate = 44100

        self.notes = [82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 
                      130.00, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00]
        self.Q = [9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 
                  9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0]
        self.note_name = ['E2', 'F2', 'F#2/Gb2', 'G2', 'G#2/Ab2', 'A2', 'A#2/Bb2', 'B2', 
                          'C3', 'C#3/Db3', 'D3', 'D#3/Eb3', 'E3', 'F3', 'F#3/Gb3', 'G3']
        self.Nnotes = len(self.notes)

        self.Bs = np.zeros((self.Nnotes, 3))
        self.As = np.zeros((self.Nnotes, 3))

        self.IC = np.zeros((2, self.Nnotes))
        self.rmsMatrix = np.array([])
        self.rmsCurrentFrame = np.zeros((self.Nnotes,))

        self.devIdxIN = 1
        self.devIdxOUT = 3
        self.CHANNELS = 1
        self.CHUNK = 128
        self.FORMAT = pyaudio.paFloat32

        self.p = pyaudio.PyAudio()
        self.len_devices = self.p.get_device_count()
        self.len_devices_list = (range(self.len_devices))

        self.volume = 0.8
        self.guitar_vol = 0.2
        

        self.wavfiles = ['BassE1', 'TromboneE2', 'Man_voice', 'Select file']

        self.pitchnote = ['E1', 'F1', 'F#1/Gb1', 'G1', 'G#1/Ab1', 'A1', 'A#1/Bb1', 'B1', 
                          'C2', 'C#2/Db2', 'D2', 'D#2/Eb2', 'E2', 'F2', 'F#2/Gb2', 'G2']

        self.currentIndex = 0.0
        self.currentSample = 0.0
        self.amp = 0.0
       
        self.alpha = 0.002
        self.output = np.zeros((self.CHUNK,))

        self.paused = True
        self.playing = False


        
        self.iir_peak()
        self.buttons()
        self.change_wavetable()

    

    def buttons(self):
        '''frame0'''
        frame0 = tk.Frame(self.master, bg='#659d79')
        self.var1 = tk.StringVar(self.master)
        self.label_note = tk.Label(frame0, textvariable=self.var1, width=38, height=6, 
                                   font=('calibri', 20)).pack(padx=40, pady=40)
        
        
        self.button_2 = tk.Button(frame0, text='stop', width=13, height=1,
                             relief='solid', command=self.pause).pack(side='bottom')

        
        self.button = tk.Button(frame0, text='start', width=13, height=1,
                           relief='solid', command=self.play).pack(side='bottom')

        
        frame0.pack(side='top', fill='both')

        '''frame2'''

        frame2 = tk.Frame(self.master, bg='#659d79')

        self.Guitar_vol = tk.Scale(frame2, from_=6, to_=-80,
                                label="Guitar Volume", length=200, resolution=1.0,
                                command=self.set_guitar_vol, highlightcolor="red", fg='red',
                                font=('calibri', 8), bg="#838B8B", orient="vertical")
        self.Guitar_vol.set(self.guitar_vol)
        self.Guitar_vol.place(relx=0.18, rely=0.5, anchor='center')

        
        self.Alpha = tk.Scale(frame2, from_=-20, to_=-80,
                                label="Alpha", length=200, resolution=1.0,
                                command=self.set_alpha, highlightcolor="red", fg='red',
                                font=('calibri', 8), bg="#838B8B", orient="vertical")
        self.Alpha.set(self.alpha)
        self.Alpha.place(relx=0.43333, rely=0.5, anchor='center')

        
        self.Volume = tk.Scale(frame2, from_=6, to_=-80,
                                label="Volume", length=200, resolution=1.0,
                                command=self.set_volume, highlightcolor="red", fg='red',
                                font=('calibri', 8), bg="#838B8B", orient="vertical")
        self.Volume.set(self.volume)
        self.Volume.place(relx=0.66, rely=0.5, anchor='center')

        frame2.pack(side='right', expand=True, fill='both')

        '''frame1'''

        frame1 = tk.Frame(self.master, bg='#659d79')

        
        self.var0 = tk.StringVar(root)
        self.Pitch_height = tk.OptionMenu(
            frame1, self.var0, *self.pitchnote).place(relx=0.57, rely=0.23, anchor='center')
        self.var0.trace('w', self.set_pitch_height)


        self.var = tk.StringVar(root)
        self.var.set(self.wavfiles[0])
        self.dropmenu = tk.OptionMenu(
            frame1, self.var, *self.wavfiles).place(relx=0.38, rely=0.23, anchor='center')
        self.var.trace('w', self.change_wavetable)


        self.var3 = tk.StringVar(root)
        self.var3.set(self.devIdxIN)
        self.choose_inport = tk.OptionMenu(
            frame1, self.var3, *self.len_devices_list).place(relx=0.358, rely=0.7, anchor='center')
        self.var3.trace('w', self.in_port)


        self.var4 = tk.StringVar(root)
        self.var4.set(self.devIdxOUT)
        self.choose_output = tk.OptionMenu(
            frame1, self.var4, *self.len_devices_list).place(relx=0.56, rely=0.7, anchor='center')
        self.var4.trace('w', self.out_port)


        self.devices = tk.Button(frame1,  text='See Available Ports', command=self.choose_ports,
                                 relief='solid',
                                 font=('calibri', 12)).place(relx=0.457, rely=0.48, anchor='center')

        
        frame1.pack(side='right', expand=True, fill='both')


    def choose_ports(self):
        top = tk.Toplevel()
        top.geometry("850x600")
        top.configure(background='black')
        top.title("In-Out Ports")

        top.grid_columnconfigure(0, weight=1)
        top.grid_rowconfigure(0, weight=1)

        text = tk.Text(top, height=60, width=200,
                       pady=10, padx=10, bg='orange')
        text.grid(row=0, column=0, sticky=tk.NW)

        scrollbar = ttk.Scrollbar(top, orient='vertical', command=text.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)

        text['yscrollcommand'] = scrollbar.set

        gap = 0
        for dev in range(self.p.get_device_count()):

            nam = self.p.get_device_info_by_index(dev).get('name')
            inf = self.p.get_device_info_by_index(dev)
            dev_num = 'device=' + str(dev)
            posision = f'{gap}.0'
            printed = f'{nam}\n{inf}\n{dev_num}\n\n'

            text.insert(posision, printed)
            gap += 5

        top.mainloop()

        
    def set_volume(self, value):
        self.volume = float(10**(float(value)/20))
        return self.volume


    def set_guitar_vol(self, value):
        self.guitar_vol = float(10**(float(value)/20))
        return self.guitar_vol



    def set_alpha(self, value):
        self.alpha = float(10**(float(value)/20))
        return self.alpha
    
 

    def in_port(self, *args):
        current_inport = self.var3.get()
        return int(current_inport)



    def out_port(self, *args):
        current_outport = self.var4.get()
        return int(current_outport)


    
    def set_pitch_height(self, *args):
        current0 = self.var0.get()

        if current0 == 'E1':
            self.pitch = 41.2

        elif current0 == 'F1':
            self.pitch = 43.65

        elif current0 == 'F#1/Gb1':
            self.pitch = 46.25

        elif current0 == 'G1':
            self.pitch = 49.00

        elif current0 == 'G#1/Ab1':
            self.pitch = 51.91

        elif current0 == 'A1':
            self.pitch = 55.00

        elif current0 == 'A#1/Bb1':
            self.pitch = 58.27

        elif current0 == 'B1':
            self.pitch = 61.74

        elif current0 == 'C2':
            self.pitch = 65.41

        elif current0 == 'C#2/Db2':
            self.pitch = 69.30

        elif current0 == 'D2':
            self.pitch = 73.42

        elif current0 == 'D#2/Eb2':
            self.pitch = 77.78

        elif current0 == 'E2':
            self.pitch = 82.41

        elif current0 == 'F2':
            self.pitch = 87.31

        elif current0 == 'F#2/Gb2':
            self.pitch = 92.50

        elif current0 == 'G2':
            self.pitch = 98.00

        return self.pitch


    '''Definition of IIR peak filters'''
    def iir_peak(self):
        for idx, freq in enumerate(self.notes):
            B, A = signal.iirpeak(freq, self.Q[idx], int(self.rate))
            self.Bs[idx] = B
            self.As[idx] = A


    ''' Wavetables '''
    def change_wavetable(self, *args):

        curent = self.var.get()

        if curent == 'BassE1':
            self.currentIndex = 0.0
            self.currentSample = 0.0
            self.var0.set(self.pitchnote[0])
            self.samplerate, self.wave_table = read('E1662_44.wav')
            self.waveTable = self.wave_table / 32000.0
            self.waveTable_length = len(self.waveTable)-1

        elif curent == 'TromboneE2':
            self.currentIndex = 0.0
            self.currentSample = 0.0
            self.var0.set(self.pitchnote[12])
            self.samplerate, self.wave_table = read('tromboneE2.wav')
            self.waveTable = self.wave_table / 32000.0
            self.waveTable_length = len(self.waveTable)-1

        elif curent == 'Man_voice':
            self.currentIndex = 0.0
            self.currentSample = 0.0
            self.var0.set(self.pitchnote[6])
            self.samplerate, self.wave_table = read('man_voice_Bb.wav')
            self.waveTable = self.wave_table / 32000.0
            self.waveTable_length = len(self.waveTable)-1

        elif curent == 'Select file':
            try:
                file_select = filedialog.askopenfilename(initialdir='/',
                                                         title='Select file',
                                                         filetypes=(('wav files', '*.wav'), 
                                                            ('All files', '*.*')))

                basename = os.path.basename(file_select)
                self.currentIndex = 0.0
                self.currentSample = 0.0
                self.var0.set(self.pitchnote[0])
                self.samplerate, self.wave_table = read(str(basename))
                self.waveTable = self.wave_table / 32000.0
                self.waveTable_length = len(self.waveTable)-1
            except:
                ValueError


   
    '''Interpolation'''
    def interpolate_linearly(self, inote):

        tableDelta = inote / float(self.set_pitch_height())
        index0 = int(self.currentIndex)
        index1 = index0 + 1
        frac = self.currentIndex - index0
        value0 = self.waveTable[index0]
        value1 = self.waveTable[index1]
        self.currentSample = value0 + frac * (value1-value0)
        self.currentIndex += tableDelta
        if self.currentIndex > self.waveTable_length:
            self.currentIndex -= self.waveTable_length

        return self.currentSample


    '''Pyaudio Callback Function'''
    def callback(self, in_data, frame_count, time_info, status):

        sIN = np.frombuffer(in_data, dtype=np.float32)

        for i in range(self.Nnotes):
            filtsig, ic = signal.lfilter(
                self.Bs[i], self.As[i], sIN, zi=self.IC[:, i])
            self.IC[:, i] = ic
            self.rmsCurrentFrame[i] = np.linalg.norm(filtsig)

        maxpos = np.argmax(self.rmsCurrentFrame)
        printed = self.note_name[maxpos]
        self.var1.set(printed)
        inote = self.notes[maxpos]
        inote *= 0.5

        for n in range(self.CHUNK):
            self.amp = self.amp*(1-self.alpha) + self.alpha*np.abs(sIN[n])
            self.output[n] = self.interpolate_linearly(inote) * self.amp
        
        
        self.output = self.volume * (self.output + self.guitar_vol *sIN)
    
        return (self.output.astype(np.float32), pyaudio.paContinue)


    ''' Setup Pyaudio '''
    def Pyaudio(self):
        p = pyaudio.PyAudio()
        stream = self.p.open(format=self.FORMAT,
                             channels=self.CHANNELS, input_device_index=self.in_port(),
                             output_device_index=self.out_port(),
                             rate=self.rate,
                             input=True,
                             output=True,
                             frames_per_buffer=self.CHUNK,
                             stream_callback=self.callback)

        stream.start_stream()
        while stream.is_active and self.playing:
            if self.pause:
                time.sleep(0.001)
            else:
                time.sleep(0.001)

        self.playing = False
        stream.close()
        p.terminate()


    def pause(self):
        p = pyaudio.PyAudio()
        self.paused = True
        self.playing = False
        p.terminate()


    def play(self):
        if not self.playing:
            self.playing = True

            threading.Thread(target=self.Pyaudio, daemon=True).start()
            self.paused = False

        self.paused = False


    def stop(self):
        self.playing = False



def handle_close():
    player.stop()
    root.destroy()


''' SETUP AND RUN '''
root = tk.Tk()
root.title("Guitar Conversion")
root.configure(background='black')
root.geometry("800x600")
root.iconbitmap('logowhite.ico')
player = Stream(root)
root.protocol("WM_DELETE_WINDOW", handle_close)
root.mainloop()
