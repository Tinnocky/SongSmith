from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import *


class Sidebar(QWidget):
    nav_clicked = Signal(int)
    logout_clicked = Signal()

    def __init__(self):
        logout_clicked = Signal()

        super().__init__()
        self.setFixedWidth(150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)

        self.compose_btn = QPushButton("Compose")
        self.storage_btn = QPushButton("Storage")
        self.profile_btn = QPushButton("Profile")

        self.compose_btn.clicked.connect(lambda: self.nav_clicked.emit(0))
        self.storage_btn.clicked.connect(lambda: self.nav_clicked.emit(1))
        self.profile_btn.clicked.connect(lambda: self.nav_clicked.emit(2))

        # set compose as default active
        self.compose_btn.setProperty("active", True)
        self._active_btn = self.compose_btn

        layout.addWidget(self.compose_btn)
        layout.addWidget(self.storage_btn)
        layout.addWidget(self.profile_btn)

        layout.addStretch()

        self.username_label = QLabel("")
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout_clicked)

        layout.addWidget(self.username_label)
        layout.addWidget(self.logout_btn)

        # add design
        self.logout_btn.setObjectName("logout_btn")
        self.username_label.setObjectName("username_label")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # make sure this has a border

    def set_active(self, index: int):
        """changes the current active screen (in design)"""
        # remove active from current
        self._active_btn.setProperty("active", False)
        self._active_btn.style().unpolish(self._active_btn)
        self._active_btn.style().polish(self._active_btn)

        # set new active
        btn = [self.compose_btn, self.storage_btn, self.profile_btn][index]
        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        self._active_btn = btn

    def set_username(self, username: str):
        self.username_label.setText(username)
