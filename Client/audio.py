import threading
import time

import pretty_midi as pm
DSOUND = "dsound"

class MidiPlayer:
    def __init__(self, soundfont_path: str, on_finished=None):
        import fluidsynth

        # initialize synthesizer
        self.synth = fluidsynth.Synth()
        result = self.synth.start(driver=DSOUND)  # windows only
        print(f"synth start result: {result}")
        self.soundfont_id = self.synth.sfload(soundfont_path)

        # initialize state
        self._notes_list: list = []  # will contain all notes to play
        self._duration: float = 0.0
        self._current_second: float = 0.0
        self._is_playing: bool = False
        self.is_looped: bool = False

        # callback called when song finishes naturally
        self.on_finished = on_finished

        # threading
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()  # set = paused
        self._play_thread = None  # the thread object

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.synth.delete()

    @property
    def position(self) -> float:
        with self._lock:
            return self._current_second

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def load(self, midi: pm.PrettyMIDI, programs: dict = None):
        """load the notes_list and prepare the instruments"""
        self._programs = programs or {}  # ← add this
        self._duration = midi.get_end_time()
        notes = []

        for i, inst in enumerate(midi.instruments):
            channel = 9 if inst.is_drum else i
            print(
                f"instrument {i}: name={inst.name}, program={inst.program}, is_drum={inst.is_drum}, channel={channel}")
            for note in inst.notes:
                notes.append((note.start, "ON", note.pitch, note.velocity, channel))
                notes.append((note.end, "OFF", note.pitch, 0, channel))

        self._notes_list = sorted(notes)  # sort by starting time
        self._setup_channels(midi.instruments)

    def _setup_channels(self, instruments):
        """set up instruments on fluidsynth channels"""
        self.synth.system_reset()

        for i in range(16):
            self.synth.cc(i, 7, 0)
            self.synth.program_select(i, self.soundfont_id, 0, 0)

        for i, inst in enumerate(instruments):
            channel = 9 if inst.is_drum else i
            program = self._programs.get(channel, inst.program)  # ← get correct program
            result = self.synth.program_select(channel, self.soundfont_id, 128 if inst.is_drum else 0, program)
            print(f"program_select channel={channel} program={program} result={result}")

            self.synth.cc(channel, 7, 127)
            self.synth.cc(channel, 91, 40 if inst.is_drum else 60)
            self.synth.cc(channel, 93, 0 if inst.is_drum else 50)

    def play(self):
        """start playing from the beginning"""
        if not self._notes_list:  # nothing to play
            return

        self.stop()
        with self._lock:
            self._current_second = 0.0

        self._start_thread()

    def _resume(self):
        """resume from paused position"""
        if self._is_playing and self._pause_event.is_set():
            self._pause_event.clear()

    def _pause(self):
        """pause playback, keeping position"""
        if self._is_playing and not self._pause_event.is_set():
            self._pause_event.set()
            self.synth.system_reset()  # silence hanging notes

    def toggle_pause(self) -> str:
        """toggle between paused and playing. returns a string of what needs to be shown"""
        if self._pause_event.is_set():
            self._resume()
            return "Pause"
        else:
            self._pause()
            return "Play"

    def stop(self):
        """stop playback and reset position to beginning"""
        self._stop_event.set()
        self._pause_event.clear()  # unblock thread if paused

        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join()

        self._is_playing = False
        self._stop_event.clear()

        with self._lock:
            self._current_second = 0.0

        self.synth.system_reset()

    def toggle_loop(self) -> str:
        self.is_looped = not self.is_looped
        return "ON" if self.is_looped else "OFF"

    def _start_thread(self):
        """start the playback thread from current position"""
        self._stop_event.clear()
        self._pause_event.clear()
        self._is_playing = True
        self._play_thread = threading.Thread(target=self._run, daemon=True)
        self._play_thread.start()

    def _run(self):
        """main playback loop, runs on a background thread"""
        while True:
            with self._lock:
                start_pos = self._current_second

            # find first note at or after current position
            next_note_index = len(self._notes_list)  # index of last note
            for i, note in enumerate(self._notes_list):
                if note[0] >= start_pos:
                    next_note_index = i
                    break

            # add an offset so real time maps correctly to song playback time
            time_offset = time.perf_counter() - start_pos
            just_resumed = False

            while next_note_index < len(self._notes_list):  # keep playing until all notes have been played
                if self._stop_event.is_set():
                    return

                # handle pause
                if self._pause_event.is_set():
                    # save position while paused so we can continue from here later
                    with self._lock:
                        self._current_second = time.perf_counter() - time_offset

                    while self._pause_event.is_set():
                        if self._stop_event.is_set():
                            return
                        time.sleep(0.05)  # don't do this every millisecond

                    just_resumed = True

                # re-sync time_offset only after resuming from pause
                if just_resumed:
                    with self._lock:
                        time_offset = time.perf_counter() - self._current_second
                    just_resumed = False

                # update position
                current = time.perf_counter() - time_offset
                with self._lock:
                    self._current_second = current

                # check if finished
                if current >= self._duration:
                    break

                # play everything that's left
                note_time, note_type, pitch, velocity, channel = self._notes_list[next_note_index]

                wait = note_time - current
                if wait > 0:
                    time.sleep(wait)  # wait until the note's time has come

                if self._stop_event.is_set():
                    return

                if note_type == "ON":  # note starts
                    self.synth.noteon(channel, pitch, velocity)
                else:  # note ends
                    self.synth.noteoff(channel, pitch)

                next_note_index += 1  # onto the next note

            if self._stop_event.is_set():
                return

            # song finished
            self.synth.system_reset()

            if self.is_looped:
                # reset and play again from start
                with self._lock:
                    self._current_second = 0.0
                continue  # go back to the start of the full while loop

            else:
                # fully finished
                self._is_playing = False
                with self._lock:
                    self._current_second = 0.0
                if self.on_finished:
                    self.on_finished()  # callback to MainWindow
                return
