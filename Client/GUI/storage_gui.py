from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import *


class StorageWindow(QWidget):
    try_see_storage = Signal()
    try_play = Signal(str)
    try_rename = Signal(str)
    try_extract = Signal(str)
    try_delete = Signal(str)

    def __init__(self):
        super().__init__()

        # create gui objects
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(lambda: self.try_see_storage.emit())

        self.song_list = QListWidget()
        self.song_list.itemSelectionChanged.connect(self._on_selection_changed)

        self.play_btn = QPushButton("Play")
        self.rename_btn = QPushButton("Rename")
        self.extract_btn = QPushButton("Extract")
        self.delete_btn = QPushButton("Delete")

        self.play_btn.clicked.connect(self.handle_play)
        self.rename_btn.clicked.connect(self.handle_rename)
        self.extract_btn.clicked.connect(self.handle_extract)
        self.delete_btn.clicked.connect(self.handle_delete)

        self._set_action_buttons_enabled(False)  # all action buttons disabled until a song is selected

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.play_btn)
        buttons_row.addWidget(self.rename_btn)
        buttons_row.addWidget(self.extract_btn)
        buttons_row.addWidget(self.delete_btn)

        # add design
        self.refresh_btn.setObjectName("refresh_btn")
        self.play_btn.setObjectName("play_btn")
        self.rename_btn.setObjectName("rename_btn")
        self.extract_btn.setObjectName("extract_btn")
        self.delete_btn.setObjectName("delete_btn")

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.song_list)
        layout.addLayout(buttons_row)

    def _on_selection_changed(self):
        """enable action buttons only when a song is selected"""
        has_selection = len(self.song_list.selectedItems()) > 0
        self._set_action_buttons_enabled(has_selection)

    def _set_action_buttons_enabled(self, enabled: bool):
        self.play_btn.setEnabled(enabled)
        self.rename_btn.setEnabled(enabled)
        self.extract_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    def _selected_song_name(self) -> str | None:
        """helper to get the selected song's name, to be used in the handle_X functions below"""
        items = self.song_list.selectedItems()
        if not items:
            return None

        widget = self.song_list.itemWidget(items[0])
        if isinstance(widget, SongRow):
            return widget.song_name

        return None

    def handle_play(self):
        name = self._selected_song_name()
        if name:
            self.try_play.emit(name)

    def handle_rename(self):
        name = self._selected_song_name()
        if name:
            self.try_rename.emit(name)

    def handle_extract(self):
        name = self._selected_song_name()
        if name:
            self.try_extract.emit(name)

    def handle_delete(self):
        name = self._selected_song_name()
        if name:
            self.try_delete.emit(name)

class SongRow(QWidget):
    """a song in storage"""

    def __init__(self, song: dict):
        super().__init__()
        self.setAutoFillBackground(True)
        self.setMinimumHeight(60)
        self.song_name: str = song["name"]

        name_label = QLabel(song["name"])
        name_label.setObjectName("song_name_label")

        info_label = QLabel(
            f"{song['key']} {song['scale']} | {round(song['seconds'])}s | {song['complexity']}"
        )
        info_label.setObjectName("song_info_label")
        info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(info_label)
