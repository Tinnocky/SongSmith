from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *


class AuthWindow(QWidget):
    # signals
    try_auth = Signal(bool, str, str)

    def __init__(self):
        super().__init__()
        self._is_login_mode = True  # starts in login mode

        # create gui objects
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")

        self.reveal_password_btn = QPushButton("Show")
        self.reveal_password_btn.setCheckable(True)
        self.reveal_password_btn.toggled.connect(self._toggle_see_password)

        password_row = QHBoxLayout()
        password_row.addWidget(self.password_input)
        password_row.addWidget(self.reveal_password_btn)

        self.confirm_password_label = QLabel("Confirm Password")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_label.setVisible(False)  # isn't visible in login mode
        self.confirm_password_input.setVisible(False)  # isn't visible in login mode

        self.submit_btn = QPushButton("Login")
        self.submit_btn.clicked.connect(self._handle_submit)

        self.switch_mode_btn = QPushButton("Don't have an account? Register")
        self.switch_mode_btn.clicked.connect(self.toggle_auth_mode)

        self.error_label = QLabel("")
        self.error_label.setVisible(False)

        # add design
        self.submit_btn.setObjectName("submit_btn")
        self.switch_mode_btn.setObjectName("switch_mode_btn")
        self.reveal_password_btn.setObjectName("reveal_password_btn")
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True) # so it'd take full width

        # add all rows
        form = QFormLayout()
        form.addRow("Username", self.username_input)
        form.addRow("Password", password_row)
        form.addRow(self.confirm_password_label, self.confirm_password_input)
        form.addRow(self.error_label)
        form.addRow(self.submit_btn)
        form.addRow(self.switch_mode_btn)
        form.setVerticalSpacing(25)

        # wrap all
        wrapper = QVBoxLayout(self)
        wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_widget = QWidget()
        form_widget.setFixedWidth(420)
        form_widget.setLayout(form)
        wrapper.addWidget(form_widget)

    def toggle_auth_mode(self):
        """switch between login and register modes"""
        self._is_login_mode = not self._is_login_mode  # switch mode

        # not visible in login mode and visible in register mode
        self.confirm_password_label.setVisible(not self._is_login_mode)
        self.confirm_password_input.setVisible(not self._is_login_mode)

        # clear all inputs
        self.username_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.hide_error()

        # change text to fit current mode
        self.submit_btn.setText("Login" if self._is_login_mode else "Register")
        self.switch_mode_btn.setText(
            "Don't have an account? Register" if self._is_login_mode
            else "Already have an account? Login"
        )

    def _toggle_see_password(self, button_checked: bool):
        """toggle password visibility"""
        self.reveal_password_btn.setText("Hide" if button_checked else "Show")
        mode = QLineEdit.EchoMode.Normal if button_checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_password_input.setEchoMode(mode)

    def _handle_submit(self):
        """validate fields and emit a signal to MainWindow"""
        username = self.username_input.text()
        password = self.password_input.text()
        if not username or not password:
            self.show_error("Please fill in all fields.")
            return  # exit early

        if not self._is_login_mode:  # in register mode we check confirm password too
            if not self.confirm_password_input.text():
                self.show_error("Please fill in all fields.")
                return  # exit early

            if not self.confirm_password_input.text() == password:
                self.show_error("'Confirm Password' field must match the 'Password' field.")
                self.confirm_password_input.clear()
                return  # exit early

        if self._is_login_mode:
            self.try_auth.emit(self._is_login_mode, username, password)
        else:
            self.try_auth.emit(self._is_login_mode, username, password)

    def show_error(self, message: str):
        """show an error message under the fields"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def hide_error(self):
        """remove an error message under the fields"""
        self.error_label.setVisible(False)

    def reset(self):
        self._is_login_mode = False
        self.toggle_auth_mode() # so it would switch to log in
        self.hide_error()
