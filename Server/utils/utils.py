import hashlib
import io
import os
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from Server.CompositionEngine.composer import Generator
from Server.CompositionEngine.midi import MidiEngine
from Server.CompositionEngine.theory import Ruleset
from Server.DB.database import engine
from Server.DB.managers import SongManager, UserManager

# auth related
load_dotenv()
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 30
REFRESH_EXPIRE_MINUTES = 7 * 24 * 60  # seven days
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # the access token


def create_access_token(user_id: int, username: str) -> str:
    """generate a jwt access token for the provided user and return it"""
    return _create_token(user_id, username, ACCESS_EXPIRE_MINUTES, "access")


def create_refresh_token(user_id: int, username: str) -> str:
    """generate a jwt refresh token for the provided user and return it"""
    return _create_token(user_id, username, REFRESH_EXPIRE_MINUTES, "refresh")


def _create_token(user_id: int, username: str, expire_minutes: int, token_type: str) -> str:
    """create a token and return it"""
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    token_payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire_time,
        "type": token_type
    }

    return jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)


def get_user_data(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency. validates session, decodes JWT, returns the user's id and username"""
    # decode jwt to get username
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # sub (subject) is the user id
        username = payload.get("username")
        token_type = payload.get("type")

        if not user_id or not username or token_type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"user_id": int(user_id), "username": username}


def get_refresh_token_data(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency. validates session, decodes JWT, returns the user's id and username
    unlike the get_user_data function, this is used to validate refresh tokens only. a shame I had to create this"""
    # decode jwt to get username
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # sub (subject) is the user id
        username = payload.get("username")
        token_type = payload.get("type")

        if not user_id or not username or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"user_id": int(user_id), "username": username}


# database related
_song_manager = SongManager(engine)
_user_manager = UserManager(engine)


def get_song_manager() -> SongManager:
    """FastAPI dependency. returns the song manager object instead of importing everywhere"""
    return _song_manager


def get_user_manager() -> UserManager:
    """FastAPI dependency. returns the user manager object instead of importing everywhere"""
    return _user_manager


# password related
def sha1_hash(password: str) -> str:
    """return the provided string's sha1 hash"""
    return hashlib.sha1(password.encode("utf-8")).hexdigest().upper()


async def check_hibp(password: str) -> int:
    """returns how many times the password has been in data breaches using haveibeenpwned api"""
    hashed_password = sha1_hash(password)
    prefix, suffix = hashed_password[:5], hashed_password[5:]  # the api uses only the first 5 characters

    try:
        async with httpx.AsyncClient() as client:
            hash_list = await client.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
            hash_list.raise_for_status()  # raise any error
    except httpx.HTTPError:  # catch the raised error
        return 0  # probably better not to block registration if the api is down as it is not in my control

    # the api gave us a big list with hashes with the same prefix.
    # now we will look for the same suffix = our password
    for line in hash_list.text.splitlines():
        hash_str, breaches_amount = line.split(":")
        if hash_str == suffix:  # found in data breach
            return int(breaches_amount)

    return 0  # not found in data breach


async def validate_strong_password(password: str) -> list[str] | None:
    """calculate the provided passwords strength based on HIBP check (if it was breached) and length.
    if it failed, return strings explaining what to change and if its correct return None."""

    error_messages = []

    if password.count(" ") > 0:  # no spaces allowed
        error_messages.append("Password must not include any spaces.")

    if len(password) < 10:
        error_messages.append("Password is too short. Use at least 10 characters.")

    if len(error_messages) > 0:  # best to return now and not call the api for no reason
        return error_messages

    breaches_amount = await check_hibp(password)
    if breaches_amount > 0:  # I feel like 1 data breach is still fine
        error_messages.append(f"Password was found in {breaches_amount} breaches. Please choose another password.")
        return error_messages

    return None  # password strong


# songs related
def get_midi(rq) -> tuple[bytes, float]:
    """create a new song and return the midi file in bytes, and it's length in seconds, using the request."""
    # create song
    ruleset = Ruleset(rq.key, rq.scale, rq.tempo, rq.chords_instrument, rq.melody_instrument, rq.verse_bars,
                      rq.chorus_bars, rq.has_drums, rq.complexity)
    song = Generator(ruleset).generate_song()

    # turn song to midi and then to bytes
    midi_object = MidiEngine(song)
    midi_data = midi_object.generate_midi()
    midi_file = io.BytesIO()
    midi_data.write(midi_file)

    return midi_file.getvalue(), midi_data.get_end_time()
