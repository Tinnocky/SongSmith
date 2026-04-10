import io
import os
import time

import httpx
import pretty_midi as pm

from audio import MidiPlayer

BASE_URL = "http://127.0.0.1:8000"
SF2_FILENAME = "GeneralUser_GS_v1.471.sf2"
SF2_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SF2_FILENAME)
client = httpx.Client(base_url=BASE_URL)

DOWNLOADS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOADS_PATH, exist_ok=True)  # create a downloads folder if it does not exist

access_token: str | None = None  # global tokens
refresh_token: str | None = None  # global tokens


def startup_screen():
    print("""
    
    _____________________________
    |          WELCOME          |
    |                           |
    |           Enter:          |
    |     REGISTER or LOGIN     |
    |___________________________|
    """)


def _get_auth_header(token: str) -> dict:
    """returns the token in the full format that FastAPIs oauth2_scheme expects"""
    return {"Authorization": f"Bearer {token}"}


def _start_playing_song(midi_bytes):
    """play the provided audio"""
    midi_object = pm.PrettyMIDI(io.BytesIO(midi_bytes))  # turn bytes to object
    player = MidiPlayer(SF2_PATH)  # create player instance

    player.play(midi_object)
    time.sleep(midi_object.get_end_time() + 1)  # wait until song finishes
    player.stop()


def register() -> tuple[str, str, str]:
    """input username and password, run register request and return a tuple containing the
    username and the token to save."""
    while True:
        username = input("Enter Username: ")
        password = input("Enter Password: ")

        # run request
        response = client.post(f"{BASE_URL}/auth/register",
                               json={"username": username, "password": password})

        if response.status_code == 200:  # got an okay
            print(response.json()["message"])
            return login(username, password)  # run login + return the username and token tuple from it

        # didn't go through, try again after
        print(response.json()["detail"])


def login(username: str = None, password: str = None) -> tuple[str, str, str]:
    """input username and password, run login request and return a tuple containing the
    username and the token to save."""
    while True:
        if not username:
            username = input("Enter Username: ")
        if not password:
            password = input("Enter Password: ")

        # run request
        response = client.post(f"{BASE_URL}/auth/login",
                               json={"username": username, "password": password})

        if response.status_code == 200:  # got an okay
            print(response.json()["message"])
            return username, response.json()["access_token"], response.json()["refresh_token"]

        # didn't go through, try again after
        print(response.json()["detail"])
        username, password = None, None  # reset


def _refresh_token() -> bool:
    """runs the refresh token request and sets the access token to the new one"""
    global access_token, refresh_token

    response = client.post(f"{BASE_URL}/auth/refresh_token",
                           headers=_get_auth_header(refresh_token))

    if response.status_code == 200:
        access_token = response.json()["access_token"]
        return True

    print("Session expired. Please log in again.")
    return False  # refresh failed, token is fully invalid


def change_password():
    """input old and new passwords and run change password request"""

    while True:
        old_password = input("Enter old password (or BACK to stop): ")
        if old_password.upper() == "BACK":
            return  # go back

        new_password = input("Enter new password (or BACK to stop): ")
        if new_password.upper() == "BACK":
            return  # go back

        # run request
        response = client.post(f"{BASE_URL}/auth/change_password",
                               json={"old_password": old_password, "new_password": new_password},
                               headers=_get_auth_header(access_token))

        if response.status_code == 401:
            if not _refresh_token():
                return

            response = client.post(f"{BASE_URL}/auth/change_password",  # now we try again
                                   json={"old_password": old_password, "new_password": new_password},
                                   headers=_get_auth_header(access_token))

        if response.status_code == 200:  # got an okay
            print(response.json()["message"])
            return

        # didn't go through, try again after
        print(response.json()["detail"])


def delete_account() -> bool:
    """runs the /auth/delete request, and delete"""
    confirm = input("Are you sure? This cannot be undone. (YES to confirm): ")
    if confirm.strip().upper() != "YES":
        print("Cancelled.")
        return False

    response = client.delete(f"{BASE_URL}/auth/delete_user",
                             headers=_get_auth_header(access_token))

    if response.status_code == 401:
        if not _refresh_token():
            return False

        response = client.delete(f"{BASE_URL}/auth/delete_user",  # now we can try again
                                 headers=_get_auth_header(access_token))

    print(response.json()["message"])
    return response.status_code == 200


def compose():
    """input key, tempo and length, run compose response """

    #    def __init__(self, key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
    #                 verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str = "MEDIUM"):
    while True:
        try:
            print("Enter values for song creation (or \"BACK\", to stop creation). ")
            key = input("Enter Key: ").strip().upper()
            if key == "BACK":
                return  # go back

            scale = input("Enter Scale: ").strip().upper()
            if scale == "BACK":
                return  # go back

            tempo = input("Enter Tempo: ").strip().upper()
            if tempo == "BACK":
                return  # go back

            chords_instrument = input("Enter Chords Instrument: ").strip().upper()
            if chords_instrument == "BACK":
                return  # go back

            melody_instrument = input("Enter Melody Instrument: ").strip().upper()
            if melody_instrument == "BACK":
                return  # go back

            verse_bars = input("Enter Verse Bars: ").strip().upper()
            if verse_bars == "BACK":
                return  # go back

            chorus_bars = input("Enter Chorus Bars: ").strip().upper()
            if verse_bars == "BACK":
                return  # go back

            has_drums = input("Add drums? (YES or NO): ").strip().upper()
            if has_drums == "BACK":
                return  # go back

            complexity = input("Enter Complexity: ").strip().upper()
            if complexity == "BACK":
                return  # go back

            tempo, verse_bars, chorus_bars = int(tempo), int(verse_bars), int(chorus_bars)
            if key not in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
                raise ValueError
            if scale not in ["MAJOR", "MINOR", "MIXOLYDIAN"]:
                raise ValueError
            if (chords_instrument not in ["PIANO", "NYLON GUITAR", "ROCK GUITAR", "SYNTH"] or
                    melody_instrument not in ["PIANO", "NYLON GUITAR", "ROCK GUITAR", "SYNTH"]):
                raise ValueError
            if tempo <= 0 or verse_bars <= 0 or chorus_bars <= 0:
                raise ValueError
            if has_drums not in ["YES", "NO"]:
                raise ValueError
            if complexity not in ["SIMPLE", "MEDIUM", "COMPLEX"]:
                raise ValueError
            break

        except ValueError:
            print("Please enter valid parameters.")

    if has_drums == "YES":
        drums = True
    else:  # because we've ruled other statements, this is for == "NO"
        drums = False

    # run request
    response = client.post(f"{BASE_URL}/songs/compose",
                           json={"key": key, "scale": scale, "tempo": tempo, "chords_instrument": chords_instrument,
                                 "melody_instrument": melody_instrument, "verse_bars": verse_bars,
                                 "chorus_bars": chorus_bars, "has_drums": drums, "complexity": complexity},
                           headers=_get_auth_header(access_token))

    if response.status_code == 401:
        if not _refresh_token():
            return

        response = client.post(f"{BASE_URL}/songs/compose",  # now we can try again
                               json={"key": key, "scale": scale, "tempo": tempo, "chords_instrument": chords_instrument,
                                     "melody_instrument": melody_instrument, "verse_bars": verse_bars,
                                     "chorus_bars": chorus_bars, "has_drums": drums, "complexity": complexity},
                               headers=_get_auth_header(access_token))

    if response.status_code == 200:
        # start playing the song
        _start_playing_song(response.content)
    else:
        print("Failed to compose song.")


def storage() -> bool:
    """run the storage request and print it. returns false if there was nothing in the song list,
    and true if there was."""
    response = client.get(f"{BASE_URL}/songs/storage",
                          headers=_get_auth_header(access_token))

    if response.status_code == 401:
        if not _refresh_token():
            return False

        response = client.get(f"{BASE_URL}/songs/storage",  # now we can try again
                              headers=_get_auth_header(access_token))

    data = response.json()
    print(data["message"])

    if data["song_list"]:
        for song in data["song_list"]:
            print(song)
        return True

    return False  # nothing in the song list


def play_song(song_id: int):
    """run the play_song route"""
    response = client.get(f"{BASE_URL}/songs/song/{song_id}",
                          headers=_get_auth_header(access_token))

    if response.status_code == 401:
        if not _refresh_token():
            return

        response = client.get(f"{BASE_URL}/songs/song/{song_id}",  # now we can try again
                              headers=_get_auth_header(access_token))

    if response.status_code == 404:  # song doesn't exist
        print(response.json()["detail"])

    if response.status_code == 200:
        # start playing the song
        _start_playing_song(response.content)


def delete_song(song_id: int):
    """run the delete_song route"""
    response = client.delete(f"{BASE_URL}/songs/song/{song_id}",
                             headers=_get_auth_header(access_token))

    if response.status_code == 401:
        if not _refresh_token():
            return

        response = client.delete(f"{BASE_URL}/songs/song/{song_id}",  # now we can try again
                                 headers=_get_auth_header(access_token))

    if response.status_code == 404:  # song doesn't exist
        print(response.json()["detail"])

    if response.status_code == 200:
        print(response.json()["message"])


def extract_song(song_id: int):
    """create a new file with the song midi in it"""
    response = client.get(f"{BASE_URL}/songs/song/{song_id}",
                          headers=_get_auth_header(access_token))

    if response.status_code == 401:
        if not _refresh_token():
            return

        response = client.get(f"{BASE_URL}/songs/song/{song_id}",  # now we can try again
                              headers=_get_auth_header(access_token))

    if response.status_code == 404:  # song doesn't exist
        print(response.json()["detail"])

    if response.status_code == 200:  # got the song
        filename = input("Enter Name: ")
        filepath = os.path.join(DOWNLOADS_PATH, filename + ".midi")
        try:
            with open(filepath, "xb") as file:
                file.write(response.content)
            print(f"Saved as {filename} in {filepath}.")

        except FileExistsError:
            print("A file with that name already exists.")


def see_storage():
    """choose a song from the stored songs and start PLAY/DELETE functions"""
    if not storage():  # show the list first + check if there's nothing in the song list
        return  # return gracefully if there's nothing there

    # make sure song_id is indeed just an int
    print("Commands: PLAY {song_id} | DELETE {song_id} | EXTRACT {song_id} | (or \"BACK\", to stop). ")
    while True:
        try:
            prompt = input(">>> ").strip().upper()
            if prompt == "BACK":
                return  # go back

            prompt = prompt.split()
            if len(prompt) != 2:
                raise ValueError

            command, song_id = prompt[0], prompt[1]
            song_id = int(song_id)

            if command != "PLAY" and command != "DELETE" and command != "EXTRACT":
                raise ValueError
            if song_id < 1:  # only positive song ID's exist
                raise ValueError

            break

        except ValueError:
            print("Please enter a valid command and song id.")

    # run query
    if command == "PLAY":
        play_song(song_id)

    elif command == "DELETE":
        delete_song(song_id)

    elif command == "EXTRACT":
        extract_song(song_id)


def main():
    global access_token, refresh_token

    while True:
        startup_screen()

        username = None
        while not username:
            choice = input(">>> ").strip().upper()
            if choice == "REGISTER":
                username, access_token, refresh_token = register()
            elif choice == "LOGIN":
                username, access_token, refresh_token = login()
            else:
                print("Please enter REGISTER or LOGIN.")

        # main loop, only reachable after login/register
        while True:
            print("\nCommands: COMPOSE | STORAGE | CHANGE PASSWORD | DELETE ACCOUNT | LOGOUT")
            choice = input(">>> ").strip().upper()

            if choice == "COMPOSE":
                compose()
            elif choice == "STORAGE":
                see_storage()
            elif choice == "CHANGE PASSWORD":
                change_password()
            elif choice == "DELETE ACCOUNT":
                if delete_account():
                    break  # account deleted, exit
            elif choice == "LOGOUT":
                break  # session ended, exit to startup screen
            else:
                print("Command does not exist. Please try again.")


if __name__ == "__main__":
    main()
