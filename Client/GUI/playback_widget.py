from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout


class PlaybackWidget(QWidget):
    try_pause = Signal()
    try_loop = Signal()

    def __init__(self):
        super().__init__()

        self.now_playing_label = QLabel("Now playing")
        self.now_playing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pause_btn = QPushButton("Pause")
        self.loop_btn = QPushButton("Loop: OFF")

        self.pause_btn.clicked.connect(self.try_pause)
        self.loop_btn.clicked.connect(self.try_loop)

        controls_row = QHBoxLayout()
        controls_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_row.addWidget(self.pause_btn)
        controls_row.addWidget(self.loop_btn)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.now_playing_label)
        layout.addLayout(controls_row)

        # design
        self.now_playing_label.setObjectName("now_playing_label")
        self.pause_btn.setObjectName("pause_btn")
        self.loop_btn.setObjectName("loop_btn")
