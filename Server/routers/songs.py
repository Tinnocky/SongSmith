from uuid import uuid4

from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from Server.utils.utils import get_midi, get_user_data, get_song_manager, get_song_cache

router = APIRouter(prefix="/songs")


class ComposeRequest(BaseModel):
    key: str
    scale: str
    tempo: int
    chords_instrument: str
    melody_instrument: str
    verse_bars: int
    chorus_bars: int
    has_drums: bool
    complexity: str = "MEDIUM"


@router.post("/compose")
def compose(request: ComposeRequest, user_data: dict = Depends(get_user_data),
            song_cache: dict = Depends(get_song_cache)):
    """generate the song with the provided key, tempo and length and return it."""
    # make the raw midi bytes from
    midi_bytes, midi_length = get_midi(request)

    # put songs in song_cache to hold
    song_id_in_cache = str(uuid4())
    song_data = {
        "midi_bytes": midi_bytes,
        "key": request.key,
        "scale": request.scale,
        "tempo": request.tempo,
        "length": midi_length,
        "complexity": request.complexity
    }

    song_cache.setdefault(user_data["user_id"], {})[song_id_in_cache] = song_data  # add to cache

    return Response(content=midi_bytes, media_type="audio/midi", headers={"X-Song-Id": song_id_in_cache})


class StorageResponse(BaseModel):
    song_list: list[str] | None


@router.get("/storage")
def storage(user_data: dict = Depends(get_user_data),
            songs_table=Depends(get_song_manager)) -> StorageResponse:
    """send the songs that are stored in the database under the users name"""
    song_list = songs_table.list_songs(user_data["user_id"])
    if not song_list:
        return StorageResponse(song_list=None)  # empty

    return StorageResponse(song_list=song_list)


@router.get("/song/{song_name}")
def get_song(song_name: str, user_data: dict = Depends(get_user_data),
             songs_table=Depends(get_song_manager)) -> Response:
    """send the midi bytes for the song with the provided song name"""
    midi_bytes = songs_table.get_midi_by_name(user_data["user_id"], song_name)

    if not midi_bytes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Song {song_name} not found.")

    return Response(content=midi_bytes,
                    media_type="audio/midi")


class SaveSongRequest(BaseModel):
    song_name: str = Field(min_length=1, max_length=50, pattern=r"^[\w\s\-]+$")


@router.post("/save/{song_uuid}", status_code=status.HTTP_201_CREATED)
def save_song(song_uuid: str, request: SaveSongRequest, user_data: dict = Depends(get_user_data),
              songs_table=Depends(get_song_manager), song_cache: dict = Depends(get_song_cache)):
    """save the song with the provided song uuid to the user's database, taking it from the song_cache."""
    # check if the song to save exists in the cache
    song_data = song_cache.get(user_data["user_id"], {}).get(song_uuid)
    if not song_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Song not found or expired")

    try:
        songs_table.save_song(user_data["user_id"], song_data["midi_bytes"], request.song_name, song_data["key"],
                              song_data["scale"], song_data["tempo"], song_data["length"], song_data["complexity"])
    except IntegrityError:  # song with that name already exists for this user
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="You already have a song with that name.")

    song_cache[user_data["user_id"]].pop(song_uuid)  # remove from cache


@router.delete("/compose/{song_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song_from_cache(song_uuid: str, user_data: dict = Depends(get_user_data),
                           song_cache: dict = Depends(get_song_cache)):
    """discards the song with the provided song uuid from the song_cache"""
    if not song_cache.get(user_data["user_id"], {}).get(song_uuid):  # check if song exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Song not found or expired")

    song_cache[user_data["user_id"]].pop(song_uuid)  # it exists, remove from cache


@router.delete("/song/{song_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(song_name: str, user_data: dict = Depends(get_user_data),
                songs_table=Depends(get_song_manager)):
    """delete the song with the provided song name from the user's database"""
    if not songs_table.delete_song(user_data["user_id"], song_name):  # delete song + check if worked
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Song {song_name} not found")


class RenameSongRequest(BaseModel):
    old_song_name: str = Field(min_length=1, max_length=50, pattern=r"^[\w\s\-]+$")
    new_song_name: str = Field(min_length=1, max_length=50, pattern=r"^[\w\s\-]+$")


@router.patch("/rename/", status_code=status.HTTP_204_NO_CONTENT)
def rename_song(request: RenameSongRequest, user_data: dict = Depends(get_user_data),
                songs_table=Depends(get_song_manager)):
    """rename the song with the provided song name."""
    result = songs_table.update_song_name(user_data["user_id"], request.old_song_name, request.new_song_name)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Song '{request.old_song_name}' not found.")
    elif result is False:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"You already have a song with that name.")

    # result must be True so that's it
