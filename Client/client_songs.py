import io
import time
from http import HTTPStatus as Status
from pathlib import Path
import pretty_midi as pm

from Client.client_utils import run_request, SF2_PATH
from audio import MidiPlayer


def _start_playing_song(midi_bytes: bytes):
    """helper, play the provided audio"""
    midi_object = pm.PrettyMIDI(io.BytesIO(midi_bytes))  # turn bytes to object
    player = MidiPlayer(SF2_PATH)  # create player instance

    player.play(midi_object)
    time.sleep(midi_object.get_end_time() + 1)  # wait until song finishes
    player.stop()


def compose(key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
            verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str):

    compose_response = run_request(
        "POST",
        "/songs/compose",
        json={
            "key": key,
            "scale": scale,
            "tempo": tempo,
            "chords_instrument": chords_instrument,
            "melody_instrument": melody_instrument,
            "verse_bars": verse_bars,
            "chorus_bars": chorus_bars,
            "has_drums": has_drums,
            "complexity": complexity
        }
    )

    if compose_response.status_code == Status.OK:
        # start playing the song
        _start_playing_song(compose_response.content)

        # decide to save or discard song
        while True:
            try:
                to_save_str = input("Save song? (YES or NO): ").strip().upper()
                if to_save_str not in ["YES", "NO"]:
                    raise ValueError

                break

            except ValueError:
                print("Please enter valid parameters.")

        to_save = to_save_str == "YES"
        song_uuid = compose_response.headers.get("X-Song-Id")
        if not song_uuid:
            print("Error: missing song UUID from server.")
            return

        if to_save:  # save
            while True:
                name = input("Enter song name: ").strip()
                if not name:
                    print("Invalid name.")
                    continue

                save_response = run_request(
                    "POST",
                    f"/songs/save/{song_uuid}",
                    json={"song_name": name}  # server checks for correct spelling
                )

                if save_response.status_code == Status.CREATED:
                    print("Song saved!")
                    break

                elif save_response.status_code == Status.UNPROCESSABLE_ENTITY:
                    print("Invalid song name.")

                elif save_response.status_code == Status.CONFLICT:
                    print("Song name already exists.")

                elif save_response.status_code == Status.NOT_FOUND:
                    print("Song expired or missing.")

        else:  # discard
            discard_response = run_request(
                "DELETE",
                f"/songs/compose/{song_uuid}"
            )

            if discard_response.status_code == Status.NO_CONTENT:
                print("Song discarded.")

            elif discard_response.status_code == Status.NOT_FOUND:
                print(discard_response.json()["detail"])
    else:
        print("Failed to compose song.")


def save_song():
    pass

def discard_song():
    pass

def _see_storage() -> bool:
    """run the storage request and print it. returns false if there was nothing in the song list,
    and true if there was."""

    response = run_request("GET", "/songs/storage")

    if response.status_code != Status.OK:
        print("Failed to fetch storage.")
        return False

    data = response.json()

    song_list = data.get("song_list")

    if len(song_list) > 0:
        for song in song_list:
            print(song)
        return True
    else:  # len == 0
        print("No songs found in storage.")
        return False


def handle_storage_requests():
    """choose a song from the stored songs and start PLAY/DELETE/EXTRACT functions"""

    if not _see_storage():  # display storage
        return

    print('Commands: PLAY {name} | DELETE {name} | EXTRACT {name} | RENAME {name} | "BACK" to stop.')

    while True:
        try:
            prompt = input(">>> ").strip()

            if prompt == "BACK":
                return

            parts = prompt.split()
            if len(parts) < 2:
                raise ValueError

            command, song_name = parts[0].upper(), " ".join(parts[1:])

            if command not in ["PLAY", "DELETE", "EXTRACT", "RENAME"]:
                raise ValueError

            break

        except ValueError:
            print("Please enter a valid command and song id.")

    # run the corresponding function
    handlers = {
        "PLAY": play_song,
        "DELETE": delete_song,
        "EXTRACT": extract_song,
        "RENAME": rename_song
    }

    handlers[command](song_name)


def play_song(song_name: str):
    """run the play_song route"""
    response = run_request("GET", f"/songs/song/{song_name}")

    if response.status_code == Status.NOT_FOUND:
        print(response.json()["detail"])

    elif response.status_code == Status.OK:
        _start_playing_song(response.content)


def delete_song(song_name: str):
    """run the delete_song route"""
    response = run_request("DELETE", f"/songs/song/{song_name}")

    if response.status_code == Status.NOT_FOUND:
        print(response.json()["detail"])

    elif response.status_code == Status.NO_CONTENT:
        print("Song deleted.")


def extract_song(song_name: str):
    """create a new file with the song midi in it"""
    response = run_request("GET", f"/songs/song/{song_name}")

    if response.status_code == Status.NOT_FOUND:
        print(response.json()["detail"])

    elif response.status_code == Status.OK:
        song_name = response.headers["x-song-name"]
        downloads = Path.home() / "Downloads"
        file_path = downloads / f"{song_name}.mid"
        file_path.write_bytes(response.content)
        print(f"Song saved to {file_path}")


def rename_song(song_name: str):
    """run the rename_song route"""
    while True:
        try:
            new_song_name = input("Enter new name: ").strip()

            if not new_song_name:
                raise ValueError

            break

        except ValueError:
            print("Invalid name.")

    response = run_request(
        "PATCH",
        f"/songs/rename/{song_name}",
        json={
            "old_song_name": song_name,
            "new_song_name": new_song_name
        }
    )

    if response.status_code == Status.NOT_FOUND or response.status_code == Status.CONFLICT:
        print(response.json()["detail"])

    elif response.status_code == Status.NO_CONTENT:
        print("Song renamed.")
