from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import *

from Client import client_auth, client_utils, client_songs
from Client.GUI.auth_gui import AuthWindow
from Client.GUI.compose_gui import ComposeWindow, ComposeWorker
from Client.GUI.profile_gui import ProfileWindow
from Client.GUI.sidebar_gui import Sidebar
from Client.GUI.storage_gui import StorageWindow, SongRow


class MainWindow(QMainWindow):
    def __init__(self, application: QApplication):
        super().__init__()
        self.app = application
        self.app.setStyleSheet(self.load_design())  # add design
        self._username = None
        self._access_token = None
        self._refresh_token = None

        self.setWindowTitle("SongSmith")
        self.resize(900, 600)

        # create gui objects
        self.outer_stack = QStackedWidget()
        self.setCentralWidget(self.outer_stack)

        # auth
        self.auth_window = AuthWindow()
        self.outer_stack.addWidget(self.auth_window)  # index 0

        # logged in view
        logged_in_view = QWidget()
        layout = QHBoxLayout(logged_in_view)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = Sidebar()
        self.inner_stack = QStackedWidget()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.inner_stack)

        self.compose_window = ComposeWindow()
        self.storage_window = StorageWindow()
        self.profile_window = ProfileWindow()

        self.inner_stack.addWidget(self.compose_window)  # index 0
        self.inner_stack.addWidget(self.storage_window)  # index 1
        self.inner_stack.addWidget(self.profile_window)  # index 2

        self.outer_stack.addWidget(logged_in_view)  # index 1

        self.sidebar.nav_clicked.connect(self.inner_stack.setCurrentIndex)
        self.sidebar.nav_clicked.connect(self.sidebar.set_active)
        self.sidebar.logout_clicked.connect(self._handle_logout)

        # connect all signals
        self.auth_window.try_auth.connect(self._handle_auth)
        self.profile_window.try_change_password.connect(self._handle_change_password)
        self.profile_window.try_delete_account.connect(self._handle_delete_account)
        self.storage_window.try_see_storage.connect(self._handle_see_storage)
        self.compose_window.try_compose.connect(self._handle_compose)
        self.compose_window.try_save.connect(self._handle_save_song)
        self.compose_window.try_discard.connect(self._handle_discard_song)

    @staticmethod
    def load_design() -> str:
        """gets all the qss files and returns them as a string"""
        styles_dir = Path(__file__).parent / "styles"
        files = ["base.qss", "sidebar.qss", "auth.qss", "compose.qss", "storage.qss", "profile.qss"]
        return "".join((styles_dir / f).read_text() for f in files)

    def _handle_auth(self, is_login_mode: bool, username: str, password: str):
        """receives username from auth signal, runs request and handles output"""
        if is_login_mode:
            output = client_auth.login(username, password)
        else:  # register mode
            output = client_auth.register(username, password)

        if isinstance(output, dict):  # got an okay
            # set all stuff
            self._username = output["username"]
            self._access_token = output["access_token"]
            self._refresh_token = output["refresh_token"]
            client_utils.set_tokens(self._access_token, self._refresh_token)  # for responses and such
            self.sidebar.set_username(self._username)
            self.profile_window.set_username(self._username)
            self.outer_stack.setCurrentIndex(1)
            self.auth_window.hide_error()
            self._handle_see_storage() # so it'd fetch songs immediately

        else:  # login_output is a str that contains the error, didn't go through
            self.auth_window.show_error(output)
            self.auth_window.password_input.clear()
            self.auth_window.confirm_password_input.clear()

    def _handle_change_password(self, old_password: str, new_password: str):
        """receives old and new password from signal and handles output"""
        error = client_auth.change_password(old_password, new_password)  # run request and get any error

        self.profile_window.new_password_input.clear()
        self.profile_window.confirm_new_password_input.clear()

        if error:
            self.profile_window.show_error(error)

        else:
            self.profile_window.show_success("Password changed successfully.")
            self.profile_window.old_password_input.clear()

    def _handle_delete_account(self):
        is_deleted = client_auth.delete_account()  # run request and get bool for if it worked (which is should)

        if is_deleted:
            self._handle_logout()

    def _handle_see_storage(self):
        list_widget = self.storage_window.song_list
        list_widget.clear()

        song_list = client_songs.see_storage()
        print(song_list)  #TODO: check if the songs pass correctly
        if not song_list:
            return  # nothing to show

        for song in song_list:
            item = QListWidgetItem()
            widget = SongRow(song)

            item.setSizeHint(widget.sizeHint())

            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)

    def _handle_compose(self, key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
                        verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str):
        self.compose_window.show_loading()  # show loading text
        self.compose_window.compose_btn.setEnabled(False)

        # initialize thread
        self.thread = QThread()
        self.worker = ComposeWorker(
            key, scale, tempo,
            chords_instrument, melody_instrument,
            verse_bars, chorus_bars,
            has_drums, complexity
        )
        self.worker.moveToThread(self.thread)

        # connect and run thread
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_compose_success)
        self.worker.error.connect(self._on_compose_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_compose_success(self, song_data):
        if isinstance(song_data, str):  # error, move to error function
            self._on_compose_error(song_data)
            return

        midi_bytes, song_uuid = song_data
        self.compose_window._midi_bytes = midi_bytes
        self.compose_window._song_uuid = song_uuid
        self.compose_window._is_playing = True
        self.compose_window.stop_btn.setText("Stop")
        self.compose_window.show_playback()

    def _on_compose_error(self, error):
        QMessageBox.critical(self, "Compose failed", error)
        self.compose_window.reset()
        self.compose_window.compose_btn.setEnabled(True)

    def _handle_save_song(self, song_uuid: str, song_name: str):
        error = client_songs.save_song(song_uuid, song_name)
        if error:
            QMessageBox.warning(self, "Save failed", error)
        else:
            self.compose_window.reset()

    def _handle_discard_song(self, song_uuid: str):
        error = client_songs.discard_song(song_uuid)
        if error:
            QMessageBox.warning(self, "Discard failed", error)
        else:
            self.compose_window.reset()

    def _handle_logout(self):
        # clear tokens
        if hasattr(self, "thread") and self.thread.isRunning():  # do not log out while thread is running
            self.thread.quit()
            self.thread.wait()

        self._username = None
        self._access_token = None
        self._refresh_token = None
        client_utils.set_tokens(None, None)

        # reset auth window
        self.auth_window.username_input.clear()
        self.auth_window.password_input.clear()
        self.auth_window.confirm_password_input.clear()
        self.auth_window.hide_error()

        # go back to auth screen
        self.outer_stack.setCurrentIndex(0)
        if not self.auth_window.is_login_mode:
            self.auth_window.toggle_auth_mode()
