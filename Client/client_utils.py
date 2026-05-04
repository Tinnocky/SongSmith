import io
import os
from http import HTTPStatus as Status

import httpx
import pretty_midi as pm
from httpx import Response

from Client.audio import MidiPlayer

BASE_URL = "http://127.0.0.1:8000"
SF2_FILENAME = "GeneralUser_GS_v1.471.sf2"
SF2_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SF2_FILENAME)
client = httpx.Client(base_url=BASE_URL)

access_token: str | None = None  # global tokens
refresh_token: str | None = None  # global tokens


def set_tokens(new_access_token: str | None, new_refresh_token: str | None) -> None:
    global access_token, refresh_token
    access_token = new_access_token
    refresh_token = new_refresh_token


def get_auth_header(token: str) -> dict:
    """returns the token in the full format that FastAPIs oauth2_scheme expects"""
    return {"Authorization": f"Bearer {token}"}


def run_request(method, url, **kwargs) -> Response:
    """this is a helper, send the provided http request to the server and handle the access/refresh tokens,
    instead of doing it for every single request. kwargs includes the json with the information needed for the
    specific request."""
    global access_token

    headers = dict(kwargs.pop("headers", {}))  # get headers if there are any
    if access_token:
        headers.update(get_auth_header(access_token))

    response = client.request(method, url, headers=headers, **kwargs)

    if response.status_code == Status.UNAUTHORIZED:
        if not refresh_token or not refresh_access_token():
            return response

        headers.update(get_auth_header(access_token))
        response = client.request(method, url, headers=headers, **kwargs)

    return response


def refresh_access_token() -> bool:
    """runs the refresh token request and sets the access token to the new one"""
    global access_token, refresh_token

    response = client.post(
        "/auth/refresh_token",
        headers=get_auth_header(refresh_token)
    )

    if response.status_code == Status.OK:
        access_token = response.json()["access_token"]
        return True

    return False


def start_playing(player: MidiPlayer, midi_bytes: bytes):
    import mido

    programs = {}
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'program_change':
                programs[msg.channel] = msg.program  # last one wins

    midi_object = pm.PrettyMIDI(io.BytesIO(midi_bytes))
    player.load(midi_object, programs)
    player.play()
