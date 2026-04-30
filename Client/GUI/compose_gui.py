from PySide6.QtCore import Qt, Signal, QObject, Slot, QTimer
from PySide6.QtWidgets import *

from Client import client_songs


class ComposeWindow(QWidget):
    # hardcoded constant properties
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    SCALES = ["Major", "Minor", "Mixolydian"]
    INSTRUMENTS = ["Piano", "Nylon Guitar", "Rock Guitar", "Synth"]
    BAR_AMOUNTS = ["4", "8", "12", "16"]
    COMPLEXITIES = ["Simple", "Medium", "Complex"]

    # signals
    try_compose = Signal(str, str, int, str, str, int, int, bool, str)
    try_save = Signal(str, str)
    try_discard = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_playing = False
        self._midi_bytes = None
        self._song_uuid = None

        # create gui objects
        # form fields
        self.key_input = QComboBox()
        self.key_input.addItems(self.NOTES)

        self.scale_input = QComboBox()
        self.scale_input.addItems(self.SCALES)

        self.tempo_input = QSpinBox()
        self.tempo_input.setRange(40, 400)
        self.tempo_input.setValue(120)

        self.chords_instrument_input = QComboBox()
        self.chords_instrument_input.addItems(self.INSTRUMENTS)

        self.melody_instrument_input = QComboBox()
        self.melody_instrument_input.addItems(self.INSTRUMENTS)

        self.has_drums_input = QCheckBox()
        self.has_drums_input.setChecked(True)

        self.verse_bars_input = QComboBox()
        self.verse_bars_input.addItems(self.BAR_AMOUNTS)

        self.chorus_bars_input = QComboBox()
        self.chorus_bars_input.addItems(self.BAR_AMOUNTS)

        self.complexity_input = QComboBox()
        self.complexity_input.addItems(self.COMPLEXITIES)
        self.complexity_input.setCurrentIndex(1)  # default to Medium

        self.compose_btn = QPushButton("Compose Song")
        self.compose_btn.clicked.connect(self._handle_compose)

        # make form
        form = QFormLayout()
        form.addRow("Key", self.key_input)
        form.addRow("Scale", self.scale_input)
        form.addRow("Tempo (BPM)", self.tempo_input)
        form.addRow("Chords Instrument", self.chords_instrument_input)
        form.addRow("Melody Instrument", self.melody_instrument_input)
        form.addRow("Add Drums", self.has_drums_input)
        form.addRow("Verse Length (bars)", self.verse_bars_input)
        form.addRow("Chorus Length (bars)", self.chorus_bars_input)
        form.addRow("Complexity", self.complexity_input)
        form.addRow(self.compose_btn)
        form.setVerticalSpacing(25)

        # generation text
        self.loading_label = QLabel("Generating song")
        self.loading_label.setVisible(False)

        self._dot_timer = QTimer()  # animated dots ... for loading
        self._dot_timer.setInterval(500)
        self._dot_timer.timeout.connect(self._animate_loading)
        self._dot_count = 0

        # playback section (hidden until song is ready)
        self.now_playing_label = QLabel("Song ready!")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._handle_stop)

        self.save_btn = QPushButton("Save Song")
        self.discard_btn = QPushButton("Discard")
        self.save_btn.clicked.connect(self._handle_save)
        self.discard_btn.clicked.connect(self._handle_discard)

        save_discard_row = QHBoxLayout()
        save_discard_row.addWidget(self.save_btn)
        save_discard_row.addWidget(self.discard_btn)

        self.playback_widget = QWidget()
        playback_layout = QVBoxLayout(self.playback_widget)
        playback_layout.addWidget(self.now_playing_label)
        playback_layout.addWidget(self.stop_btn)
        playback_layout.addLayout(save_discard_row)
        self.playback_widget.setVisible(False)

        # add design
        self.compose_btn.setObjectName("compose_btn")
        self.stop_btn.setObjectName("stop_btn")
        self.save_btn.setObjectName("save_btn")
        self.discard_btn.setObjectName("discard_btn")
        self.now_playing_label.setObjectName("now_playing_label")
        self.playback_widget.setObjectName("playback_widget")

        # main layout
        form_widget = QWidget()
        form_widget.setFixedWidth(560)
        form_widget.setLayout(form)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(self.playback_widget)

    def _handle_compose(self):
        """placeholder — will trigger compose request and show progress bar"""
        key = self.key_input.currentText().upper()
        scale = self.scale_input.currentText().upper()
        tempo = self.tempo_input.value()
        chords_instrument = self.chords_instrument_input.currentText().upper()
        melody_instrument = self.melody_instrument_input.currentText().upper()

        verse_bars = int(self.verse_bars_input.currentText())
        chorus_bars = int(self.chorus_bars_input.currentText())

        has_drums = self.has_drums_input.isChecked()
        complexity = self.complexity_input.currentText().upper()

        self.try_compose.emit(key, scale, tempo, chords_instrument, melody_instrument,
                              verse_bars, chorus_bars, has_drums, complexity)

    def _handle_stop(self):
        """stop playing a song"""
        self._is_playing = not self._is_playing
        self.stop_btn.setText("Play" if not self._is_playing else "Stop")

    def _handle_save(self):
        name, ok = QInputDialog.getText(self, "Save Song", "Enter song name:")
        if ok and name.strip():
            self.try_save.emit(self._song_uuid, name.strip())

    def _handle_discard(self):
        self.try_discard.emit(self._song_uuid)
        self.reset()

    def show_loading(self):
        """switch to showing loading text while song is being created"""
        self.compose_btn.setEnabled(False)
        self.loading_label.setVisible(True)
        self._dot_count = 0
        self._dot_timer.start()
        self.playback_widget.setVisible(False)

    def _animate_loading(self):
        """animate 3 dots after the loading_label text while generating a song"""
        self._dot_count = (self._dot_count + 1) % 4
        self.loading_label.setText("Generating song" + "." * self._dot_count)

    def show_playback(self):
        """switch to playback state after song is ready"""
        self.loading_label.setVisible(False)
        self.playback_widget.setVisible(True)
        self.compose_btn.setEnabled(True)

    def reset(self):
        """return to the default compose form state"""
        self.loading_label.setVisible(False)
        self.playback_widget.setVisible(False)
        self.compose_btn.setEnabled(True)


class ComposeWorker(QObject):
    """a class used to compose in a separate thread than the GUI"""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
                 verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str):
        super().__init__()
        self.key = key
        self.scale = scale
        self.tempo = tempo
        self.chords_instrument = chords_instrument
        self.melody_instrument = melody_instrument
        self.verse_bars = verse_bars
        self.chorus_bars = chorus_bars
        self.has_drums = has_drums
        self.complexity = complexity

    @Slot()
    def run(self):
        try:
            song_data = client_songs.compose(self.key, self.scale, self.tempo, self.chords_instrument,
                                             self.melody_instrument, self.verse_bars, self.chorus_bars, self.has_drums,
                                             self.complexity)
            if isinstance(song_data, str):  # error
                self.error.emit(song_data)
            else:
                self.finished.emit(song_data)


        except Exception as e:
            self.error.emit(str(e))
