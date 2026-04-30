from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *


class ProfileWindow(QWidget):
    try_change_password = Signal(str, str)
    try_delete_account = Signal()

    def __init__(self):
        super().__init__()

        # create gui objects
        # header
        self.username_label = QLabel("Username")
        self.username_label.setObjectName("username_label")

        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.username_label)

        header_separator = QFrame()
        header_separator.setFrameShape(QFrame.Shape.HLine)

        # change password
        self.change_password_title = QLabel("Change Password")
        self.change_password_title.setObjectName("section_title")

        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password_input.setPlaceholderText("Current password")

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("New password")

        self.confirm_new_password_input = QLineEdit()
        self.confirm_new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_new_password_input.setPlaceholderText("Confirm new password")

        self.change_password_btn = QPushButton("Change Password")
        self.change_password_btn.setObjectName("change_password_btn")
        self.change_password_btn.clicked.connect(self._handle_change_password)

        # error label
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setVisible(False)

        password_form = QFormLayout()
        password_form.addRow("Current password", self.old_password_input)
        password_form.addRow("New password", self.new_password_input)
        password_form.addRow("Confirm", self.confirm_new_password_input)
        password_form.addRow(self.error_label)  # ← error above button
        password_form.addRow(self.change_password_btn)

        password_separator = QFrame()
        password_separator.setFrameShape(QFrame.Shape.HLine)

        # danger zone
        self.danger_title = QLabel("Danger Zone")
        self.danger_title.setObjectName("danger_title")

        self.danger_description = QLabel("Deleting your account is permanent and cannot be undone.")
        self.danger_description.setObjectName("danger_description")
        self.danger_description.setWordWrap(True)

        self.delete_account_btn = QPushButton("Delete Account")
        self.delete_account_btn.setObjectName("delete_account_btn")
        self.delete_account_btn.clicked.connect(self._handle_delete_account)

        danger_layout = QVBoxLayout()
        danger_layout.addWidget(self.danger_title)
        danger_layout.addWidget(self.danger_description)
        danger_layout.addWidget(self.delete_account_btn)

        # main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)
        layout.addLayout(header_layout)
        layout.addWidget(header_separator)
        layout.addWidget(self.change_password_title)
        layout.addLayout(password_form)
        layout.addWidget(password_separator)
        layout.addStretch()
        layout.addLayout(danger_layout)

    def _handle_delete_account(self):
        """run a confirmation check and emit a try_delete_account signal to main window"""
        # initialize a confirm deleting account popup box
        confirm_popup = QMessageBox(self)
        confirm_popup.setWindowTitle("Delete Account")
        confirm_popup.setText("Are you sure you want to delete your account?")
        confirm_popup.setInformativeText("This action is permanent and cannot be undone.")
        confirm_popup.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        confirm_popup.setDefaultButton(QMessageBox.StandardButton.Cancel)

        if confirm_popup.exec() == QMessageBox.StandardButton.Yes:
            self.try_delete_account.emit()

    def _handle_change_password(self):
        """validate fields and emit a try_change_password signal to main window"""
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_new_password = self.confirm_new_password_input.text()

        if not old_password or not new_password or not confirm_new_password:
            self.show_error("Please fill in all fields.")
            return  # exit early

        if new_password != confirm_new_password:
            self.show_error("'Confirm New Password' field must match the 'New Password' field.")
            return  # exit early

        self.try_change_password.emit(old_password, new_password)

    def show_error(self, message: str):
        """show an error message under the change password fields"""
        self.error_label.setStyleSheet("color: #f7768e;")
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def show_success(self, message: str):
        """show a success message under the change password fields"""
        self.error_label.setStyleSheet("color: #9ece6a;")
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def hide_error(self):
        """remove an error message under the change password fields"""
        self.error_label.setVisible(False)
        self.error_label.setStyleSheet("")

    def set_username(self, username: str):
        self.username_label.setText(username)
