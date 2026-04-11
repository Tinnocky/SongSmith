import ctypes
import threading
import time

ctypes.CDLL(r"C:\Program Files\fluidsynth\bin\libfluidsynth-3.dll")

import fluidsynth


class MidiPlayer:
    def __init__(self, soundfont_path):
        # initialize the synthesizer object
        self.synth = fluidsynth.Synth()
        self.synth.start(driver='dsound')  # windows only

        # loading instruments
        self.soundfont_id = self.synth.sfload(soundfont_path)

        self.stop_event = threading.Event()  # flag for if the music stopped
        self.play_thread = None  # thread not linked just yet

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.synth.delete()

    def _setup_channels(self, instruments):
        """set up the instruments before playing"""
        self.synth.system_reset()

        # go over all 16 channels and reset them explicitly
        for i in range(16):
            self.synth.cc(i, 7, 0)  # mute all
            self.synth.program_select(i, self.soundfont_id, 0, 0)  # reset every channel to program 0

        for i, inst in enumerate(instruments):
            channel = 9 if inst.is_drum else i  # drums always on channel 9
            self.synth.program_select(channel, self.soundfont_id, 128 if inst.is_drum else 0, inst.program)
            # audio enhancements
            self.synth.cc(channel, 7, 127)  # raise volume
            self.synth.cc(channel, 91, 40 if inst.is_drum else 60)  # add reverb
            self.synth.cc(channel, 93, 0 if inst.is_drum else 50)  # chorus

    def play_logic(self, midi):
        """play a midi using fluidsynth"""
        self._setup_channels(midi.instruments)
        all_note_events = []

        for i, inst in enumerate(midi.instruments):
            channel = 9 if inst.is_drum else i
            for note in inst.notes:
                all_note_events.append((note.start, "ON", note.pitch, note.velocity, channel))
                all_note_events.append((note.end, "OFF", note.pitch, 0, channel))

        all_note_events.sort()  # sort by time so that it plays notes correctly
        start_time = time.perf_counter()

        for event_time, event_type, pitch, velocity, channel in all_note_events:
            if self.stop_event.is_set():  # if sound is stopped
                break

            current_time = time.perf_counter() - start_time
            wait_time = event_time - current_time
            if wait_time > 0:
                time.sleep(wait_time)

            # trigger the sound after enough time has passed
            if event_type == "ON":
                self.synth.noteon(channel, pitch, velocity)
            else:
                self.synth.noteoff(channel, pitch)

        self.synth.system_reset()  # silence at the end of the song

    def play(self, midi):
        """start playing a pretty midi object with threading"""
        self.stop()  # stop anything that's already playing
        self.stop_event.clear()  # set flag to false

        # initialize thread
        self.play_thread = threading.Thread(target=self.play_logic,
                                            args=(midi,),
                                            daemon=True)
        self.play_thread.start()

    def stop(self):
        """signal to stop playing the midi"""
        self.stop_event.set()
        if self.play_thread and self.play_thread.is_alive():  # join active thread
            self.play_thread.join()

        self.synth.system_reset()  # silence and kill any hanging notes
