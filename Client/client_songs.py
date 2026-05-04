from http import HTTPStatus as Status
from pathlib import Path

from Client.client_utils import run_request


def compose(key: str, scale: str, tempo: int, chords_instrument: str, melody_instrument: str,
            verse_bars: int, chorus_bars: int, has_drums: bool, complexity: str) -> tuple[bytes, str] | str:
    """make compose request. returns a tuple with midi_bytes, song_uuid on success, error string on failure."""
    response = run_request(
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

    if response.status_code == Status.OK:
        song_uuid = response.headers.get("X-Song-Id")
        return response.content, song_uuid

    return response.json().get("detail", "Failed to compose song.")


def save_song(song_uuid: str, song_name: str) -> str | None:
    """saves song to user's DB, returns any errors."""
    response = run_request(
        "POST",
        f"/songs/save/{song_uuid}",
        json={"song_name": song_name}
    )

    if response.status_code == Status.CREATED:
        return None

    return response.json().get("detail", "Something went wrong.")


def discard_song(song_uuid: str) -> str | None:
    """discards song from the cache, returns any errors."""
    response = run_request(
        "DELETE",
        f"/songs/compose/{song_uuid}"
    )

    if response.status_code == Status.NO_CONTENT:
        return None

    return response.json().get("detail", "Something went wrong.")


def see_storage() -> list[dict] | None:
    response = run_request("GET", "/songs/storage")

    if response.status_code != Status.OK:
        return None

    song_list = response.json().get("song_list")
    return song_list  # return song_list even if its empty


def play_song(song_name: str) -> bytes | str:
    """run the play_song route. returns the song bytes or any errors."""
    response = run_request("GET", f"/songs/song/{song_name}")

    if response.status_code == Status.OK:
        return response.content

    return response.json().get("detail", "Something went wrong.")


def rename_song(song_name: str, new_song_name: str) -> str | None:
    """run the rename_song route"""
    response = run_request(
        "PATCH",
        f"/songs/rename/{song_name}",
        json={
            "old_song_name": song_name,
            "new_song_name": new_song_name
        }
    )

    if response.status_code == Status.NO_CONTENT:
        return None

    # didn't go through
    return response.json().get("detail", "Something went wrong.")  # NOT_FOUND or CONFLICT


def extract_song(song_name: str) -> str | None:
    """create a new file with the song midi in it. returns any errors"""
    response = run_request("GET", f"/songs/song/{song_name}")

    if response.status_code == Status.OK:
        song_name = response.headers["x-song-name"]
        downloads = Path.home() / "Downloads"
        file_path = downloads / f"{song_name}.mid"
        file_path.write_bytes(response.content)
        print(f"Song saved to {file_path}")  # test
        return None

    # didn't go through
    return response.json().get("detail", "Something went wrong.")


def delete_song(song_name: str) -> str | None:
    """run the delete_song route. returns any errors."""
    response = run_request("DELETE", f"/songs/song/{song_name}")

    if response.status_code == Status.NO_CONTENT:
        return None

    # didn't go through
    return response.json().get("detail", "Something went wrong.")  # NOT_FOUND
