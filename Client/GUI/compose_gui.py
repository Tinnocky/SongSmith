from PySide6.QtCore import Qt
from PySide6.QtWidgets import *


class ComposeWindow(QWidget):
    # hardcoded constant properties
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    SCALES = ["Major", "Minor", "Mixolydian"]
    INSTRUMENTS = ["Piano", "Nylon Guitar", "Rock Guitar", "Synth"]
    BAR_AMOUNTS = ["4", "8", "12", "16"]
    COMPLEXITIES = ["Simple", "Medium", "Complex"]

    def __init__(self):
        super().__init__()

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
        self.compose_btn.clicked.connect(self.handle_compose)

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

        # progress bar (hidden until composing starts)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)

        # playback section (hidden until song is ready)
        self.now_playing_label = QLabel("Song ready!")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.handle_stop)

        self.save_btn = QPushButton("Save Song")
        self.discard_btn = QPushButton("Discard")
        self.save_btn.clicked.connect(self.handle_save)
        self.discard_btn.clicked.connect(self.handle_discard)

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
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.playback_widget)

    def handle_compose(self):
        """placeholder — will trigger compose request and show progress bar"""
        pass

    def handle_stop(self):
        """placeholder — will stop audio playback"""
        pass

    def handle_save(self):
        """placeholder — will ask for song name and save"""
        pass

    def handle_discard(self):
        """placeholder — will discard the composed song"""
        pass

    def show_progress(self):
        """switch to generating state"""
        self.compose_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.playback_widget.setVisible(False)

    def show_playback(self):
        """switch to playback state after song is ready"""
        self.progress_bar.setVisible(False)
        self.playback_widget.setVisible(True)
        self.compose_btn.setEnabled(True)

    def reset(self):
        """return to the default compose form state"""
        self.progress_bar.setVisible(False)
        self.playback_widget.setVisible(False)
        self.compose_btn.setEnabled(True)
