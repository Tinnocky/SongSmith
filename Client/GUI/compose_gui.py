from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *

from Client.GUI.playback_widget import PlaybackWidget


class ComposeWindow(QWidget):
    # hardcoded constant properties
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    SCALES = ["Major", "Minor", "Mixolydian"]
    INSTRUMENTS = ["Piano", "Nylon Guitar", "Rock Guitar", "Synth"]
    BAR_AMOUNTS = ["4", "8", "12", "16"]
    COMPLEXITIES = ["Simple", "Medium", "Complex"]

    # signals
    try_compose = Signal(str, str, int, str, str, int, int, bool, str)
    try_pause = Signal()
    try_loop = Signal()
    try_save = Signal(str, str)
    try_discard = Signal(str)

    def __init__(self):
        super().__init__()
        self.midi_bytes = None
        self.song_uuid = None

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
        self.complexity_input.setCurrentIndex(1)

        self.compose_btn = QPushButton("Compose Song")
        self.compose_btn.clicked.connect(self._handle_compose)

        # form
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

        # playback section
        self.playback = PlaybackWidget()
        self.playback.try_pause.connect(self.try_pause)  # forward up to MainWindow
        self.playback.try_loop.connect(self.try_loop)

        self.save_btn = QPushButton("Save Song")
        self.discard_btn = QPushButton("Discard")
        self.save_btn.clicked.connect(self._handle_save)
        self.discard_btn.clicked.connect(self._handle_discard)

        save_discard_row = QHBoxLayout()
        save_discard_row.addWidget(self.save_btn)
        save_discard_row.addWidget(self.discard_btn)

        self.playback_widget = QWidget()
        playback_layout = QVBoxLayout(self.playback_widget)
        playback_layout.addWidget(self.playback)
        playback_layout.addLayout(save_discard_row)
        self.playback_widget.setVisible(False)

        # design
        self.compose_btn.setObjectName("compose_btn")
        self.save_btn.setObjectName("save_btn")
        self.discard_btn.setObjectName("discard_btn")
        self.playback_widget.setObjectName("playback_widget")

        # main layout
        self.form_widget = QWidget()
        self.form_widget.setFixedWidth(560)
        self.form_widget.setLayout(form)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.form_widget)
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

    def _handle_pause(self):
        self.try_pause.emit()

    def _handle_loop(self):
        self.try_loop.emit()

    def _handle_save(self):
        name, ok = QInputDialog.getText(self, "Save Song", "Enter song name:")
        if ok and name.strip():
            self.try_save.emit(self.song_uuid, name.strip())

    def _handle_discard(self):
        self.try_discard.emit(self.song_uuid)
        self.reset()

    def show_playback(self):
        """switch to playback state after song is ready"""
        self.form_widget.setVisible(False)  # make parameter inputs invisible
        self.playback_widget.setVisible(True)
        self.compose_btn.setEnabled(True)

    def reset(self):
        """return to the default compose form state"""
        self.form_widget.setVisible(True)
        self.playback_widget.setVisible(False)
        self.compose_btn.setEnabled(True)
