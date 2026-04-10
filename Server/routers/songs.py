from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from Server.utils.utils import get_midi, get_user_data, get_song_manager

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
            songs_table=Depends(get_song_manager)):
    """generate the song with the provided key, tempo and length and return it."""
    # make the raw midi bytes from
    midi_bytes, midi_length = get_midi(request)
    songs_table.save_song(user_data["user_id"], midi_bytes, request.key, request.scale,
                          request.tempo, midi_length,
                          request.complexity)  # save to db

    return Response(content=midi_bytes,
                    media_type="audio/midi")


class StorageResponse(BaseModel):
    message: str = "Stored Songs are: "
    song_list: list[str] | None


@router.get("/storage")
def storage(user_data: dict = Depends(get_user_data),
            songs_table=Depends(get_song_manager)) -> StorageResponse:
    """send the songs that are stored in the database under the users name"""
    song_list = songs_table.list_songs(user_data["user_id"])
    if not song_list:
        return StorageResponse(message="You don't have any stored songs.",
                               song_list=None)  # empty

    return StorageResponse(song_list=song_list)


@router.get("/song/{song_id}")
def get_song(song_id: int, user_data: dict = Depends(get_user_data),
             songs_table=Depends(get_song_manager)) -> Response:
    """send the midi bytes for the song with the provided id"""
    midi_bytes = songs_table.get_midi_by_id(user_data["user_id"], song_id)

    if not midi_bytes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Song {song_id} not found.")

    return Response(content=midi_bytes,
                    media_type="audio/midi")


class DeleteSongResponse(BaseModel):
    message: str = "Song deleted successfully."


@router.delete("/song/{song_id}")
def delete_song(song_id: int, user_data: dict = Depends(get_user_data),
                songs_table=Depends(get_song_manager)) -> DeleteSongResponse:
    """delete the song with the provided song id from the user's database"""
    if not songs_table.delete_song(user_data["user_id"], song_id):  # delete song + check if worked
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Song {song_id} not found")

    return DeleteSongResponse()
