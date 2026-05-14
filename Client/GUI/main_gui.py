from pathlib import Path

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import *

from client.api import auth, songs, utils
from client.audio_engine.audio import MidiPlayer, SF2_PATH
from client.gui.auth_gui import AuthWindow
from client.gui.compose_gui import ComposeWindow
from client.gui.profile_gui import ProfileWindow
from client.gui.sidebar_gui import Sidebar
from client.gui.storage_gui import StorageWindow, SongRow


class MainWindow(QMainWindow):
    # signals
    _song_finished_signal = Signal()

    def __init__(self, application: QApplication):
        super().__init__()
        self.app = application
        self.app.setStyleSheet(self.load_design())  # add design
        self._username = None
        self._access_token = None
        self._refresh_token = None
        self._song_finished_signal.connect(self._on_song_finished)  # connect this before player
        self._player = MidiPlayer(SF2_PATH, on_finished=self._song_finished_signal.emit)  # init player

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
        self.storage_window.try_play.connect(self._handle_play)
        self.storage_window.try_rename.connect(self._handle_rename)
        self.storage_window.try_extract.connect(self._handle_extract)
        self.storage_window.try_delete.connect(self._handle_delete)
        self.storage_window.try_pause.connect(self._handle_pause)
        self.storage_window.try_loop.connect(self._handle_loop)
        self.storage_window.try_stop.connect(self._handle_storage_stop)

        self.compose_window.try_compose.connect(self._handle_compose)
        self.compose_window.try_pause.connect(self._handle_pause)
        self.compose_window.try_loop.connect(self._handle_loop)
        self.compose_window.try_save.connect(self._handle_save_song)
        self.compose_window.try_discard.connect(self._handle_discard_song)

    @staticmethod
    def load_design() -> str:
        """gets all the qss files and returns them as a string"""
        styles_dir = Path(__file__).parent / "styles"
        files = ["base.qss", "sidebar.qss", "auth.qss", "compose.qss", "storage.qss", "profile.qss"]
        return "".join((styles_dir / f).read_text() for f in files)

    def _handle_auth(self, is_login_mode: bool, username: str, password: str):
        """receives username from auth signal, runs login/register api function and handles output"""
        if is_login_mode:
            output = auth.login(username, password)
        else:  # register mode
            output = auth.register(username, password)

        if isinstance(output, dict):  # got an okay
            # set all stuff
            self._username = output["username"]
            self._access_token = output["access_token"]
            self._refresh_token = output["refresh_token"]
            utils.set_tokens(self._access_token, self._refresh_token)  # for responses and such
            self.sidebar.set_username(self._username)
            self.profile_window.set_username(self._username)
            self.outer_stack.setCurrentIndex(1)
            self.auth_window.hide_error()
            self._handle_see_storage()  # so it'd fetch songs immediately

        else:  # login_output is a str that contains the error, didn't go through
            self.auth_window.show_error(output)
            self.auth_window.password_input.clear()
            self.auth_window.confirm_password_input.clear()

    def _handle_change_password(self, old_password: str, new_password: str):
        """receives old and new password from signal, runs change_password api
        function and handles output"""
        error = auth.change_password(old_password, new_password)  # run request and get any error

        self.profile_window.new_password_input.clear()
        self.profile_window.confirm_new_password_input.clear()

        if error:
            self.profile_window.show_error(error)

        else:
            self.profile_window.show_success("Password changed successfully.")
            self.profile_window.old_password_input.clear()

    def _handle_delete_account(self):
        """runs delete_account api function and logout if worked"""
        is_deleted = auth.delete_account()

        if is_deleted:
            self._handle_logout()

    def _handle_see_storage(self):
        """runs see_storage api function and handles output"""
        list_widget = self.storage_window.song_list
        list_widget.clear()

        song_list = songs.see_storage()
        if not song_list:
            return  # nothing to show

        for song in song_list:
            item = QListWidgetItem()
            widget = SongRow(song)

            item.setSizeHint(QSize(0, 60))

            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)

    def _handle_play(self, song_name: str):
        """fetches midi bytes for the selected song and starts playback"""
        result = songs.play_song(song_name)
        if isinstance(result, str):
            QMessageBox.warning(self, "Playback failed", result)
            return
        self._player.start_playing( result)
        self.storage_window.show_playback(song_name)
        self.sidebar.setEnabled(False)

    def _handle_storage_stop(self):
        """stops playback and returns storage to the song list"""
        self._player.stop()
        self.storage_window.show_list()
        self.sidebar.setEnabled(True)

    def _handle_rename(self, song_name: str):
        """prompts for a new name and runs rename api function"""
        new_name, ok = QInputDialog.getText(self, "Rename Song", "Enter new name:")
        if not ok or not new_name.strip():
            return

        error = songs.rename_song(song_name, new_name)  # run request and get any errors
        if error:
            QMessageBox.warning(self, "Rename failed", error)
        else:
            self._handle_see_storage()

    def _handle_extract(self, song_name: str):
        """runs extract api function and notifies the user of the result"""
        error = songs.extract_song(song_name)  # run request and get any errors

        if error:
            QMessageBox.warning(self, "Extract failed", error)
        else:
            QMessageBox.information(self, "Extracted", "Song saved to Downloads folder.")

    def _handle_delete(self, song_name: str):
        """shows confirmation dialog and runs delete api function if confirmed"""
        # confirmation box
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Delete Song")
        confirm.setText(f"Delete '{song_name}'?")
        confirm.setInformativeText("This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)

        if confirm.exec() == QMessageBox.StandardButton.Yes:
            error = songs.delete_song(song_name)  # run request and get any errors
            if error:
                QMessageBox.warning(self, "Delete failed", error)
            else:
                self._handle_see_storage()

    def _handle_compose(self, key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
                        verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str):
        """runs compose api function, starts playback and switches to playback state"""
        self.compose_window.compose_btn.setEnabled(False)

        try:
            song_data = songs.compose(key, scale, tempo, chords_instrument, melody_instrument,
                                      verse_bars, chorus_bars, has_drums, complexity)

            if isinstance(song_data, str):
                self._on_compose_error(song_data)
                return

            midi_bytes, song_uuid = song_data
            self.compose_window.midi_bytes = midi_bytes
            self.compose_window.song_uuid = song_uuid

            self.compose_window.playback.pause_btn.setText("Pause")
            self.compose_window.show_playback()
            self.sidebar.setEnabled(False)

            self._player.start_playing(midi_bytes)

        except Exception as e:
            self._on_compose_error(str(e))

        finally:
            self.compose_window.compose_btn.setEnabled(True)

    def _on_compose_error(self, error):
        """shows compose error and resets compose window to form state"""
        QMessageBox.critical(self, "Compose failed", error)
        self.compose_window.reset()
        self.compose_window.compose_btn.setEnabled(True)

    def _on_song_finished(self):
        """called when song ends naturally, resets playback ui and re-enables sidebar"""
        self.compose_window.playback.pause_btn.setText("Play")
        self.storage_window.playback.pause_btn.setText("Play")
        self.storage_window.show_list()
        self.sidebar.setEnabled(True)

    def _handle_pause(self):
        """toggles pause/resume, or restarts song if it has finished"""
        if not self._player.is_playing:
            # determine which window is active
            if self.inner_stack.currentIndex() == 0:  # compose
                self._player.start_playing(self.compose_window.midi_bytes)
                self.compose_window.playback.pause_btn.setText("Pause")
            else:  # storage — song finished, just reset
                self.storage_window.show_list()
                self.sidebar.setEnabled(True)
        else:
            mode = self._player.toggle_pause()
            self.compose_window.playback.pause_btn.setText(mode)
            self.storage_window.playback.pause_btn.setText(mode)

    def _handle_loop(self):
        """toggles loop on/off and updates button text on both windows"""
        mode = self._player.toggle_loop()
        self.compose_window.playback.loop_btn.setText(f"Loop: {mode}")
        self.storage_window.playback.loop_btn.setText(f"Loop: {mode}")

    def _handle_save_song(self, song_uuid: str, song_name: str):
        """runs save api function and resets compose window on success"""
        error = songs.save_song(song_uuid, song_name)
        if error:
            QMessageBox.warning(self, "Save failed", error)
        else:
            self.compose_window.reset()
            self.sidebar.setEnabled(True)
            self._player.stop()

    def _handle_discard_song(self, song_uuid: str):
        """runs discard api function and resets compose window on success"""
        error = songs.discard_song(song_uuid)
        if error:
            QMessageBox.warning(self, "Discard failed", error)
        else:
            self.compose_window.reset()
            self.sidebar.setEnabled(True)
            self._player.stop()

    def _handle_logout(self):
        """reset the whole app and logout"""
        # kill any song currently playing
        self._player.stop()

        # clear tokens
        self._username = None
        self._access_token = None
        self._refresh_token = None
        utils.set_tokens(None, None)

        # reset windows
        self.sidebar.setEnabled(True)
        self.auth_window.reset()
        self.compose_window.reset()
        self.profile_window.reset()

        # go back to auth screen
        self.outer_stack.setCurrentIndex(0)
