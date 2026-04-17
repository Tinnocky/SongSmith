import bcrypt
from sqlalchemy import Column, String, Integer, Float, LargeBinary, ForeignKey, Engine, UniqueConstraint
from sqlalchemy.orm import Session

from Server.DB.database import Base


class SongTable(Base):
    """ORM model for the songs table"""
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    midi_bytes = Column(LargeBinary, nullable=False)
    name = Column(String, nullable=False)
    root_key = Column(String, nullable=False)
    scale = Column(String, nullable=False)
    tempo = Column(Integer, nullable=False)
    length = Column(Float, nullable=False)
    complexity = Column(String, nullable=False)

    # no user can have more than one song with the same name
    __table_args__ = (UniqueConstraint("owner_id", "name"),)


class SongManager:
    def __init__(self, db_engine: Engine):
        self._engine = db_engine

    def save_song(self, owner_id: int, midi_bytes: bytes, name: str, root: str,
                  scale: str, tempo: int, length: float, complexity: str) -> int:
        """save a new song to the songs table and returns its ID"""
        with Session(self._engine) as session:
            new_song = SongTable(owner_id=owner_id,
                                 midi_bytes=midi_bytes,
                                 name=name,
                                 root_key=root,
                                 scale=scale,
                                 tempo=tempo,
                                 length=length,
                                 complexity=complexity
                                 )

            session.add(new_song)
            session.commit()

            session.refresh(new_song)  # so we can still reach the object after commit
            return new_song.id  # type: ignore

    def delete_song(self, owner_id: int, song_name: str) -> bool:
        """deletes a song from the table and returns if it was deleted or not."""
        with Session(self._engine) as session:
            song_deleted = session.query(SongTable).filter(
                SongTable.owner_id == owner_id,
                SongTable.name == song_name
            ).delete()  # delete it

            session.commit()

            # delete returns a number
            return song_deleted > 0

    def update_song_name(self, owner_id: int, old_song_name: str, new_song_name: str) -> bool | None:
        """changes the provided songs name to the new song name. return true if it worked, false if not."""
        with Session(self._engine) as session:
            song = session.query(SongTable).filter(
                SongTable.owner_id == owner_id,
                SongTable.name == old_song_name
            ).first()

            if song:  # run only if song exists
                if song.name == new_song_name:
                    return False

                song.name = new_song_name
                session.commit()
                return True

            return None

    def list_songs(self, owner_id: int) -> list[str]:
        """get all songs by the provided user and return them as a list of strings"""
        with Session(self._engine) as session:
            song_list = session.query(SongTable).filter(
                SongTable.owner_id == owner_id
            ).all()

        return [
            f"{s.name}: {s.root_key} {s.scale} | {s.tempo} BPM | {s.length:.2f} Seconds | Complexity: {s.complexity}"
            for s in song_list
        ]

    def get_midi_by_name(self, owner_id: int, song_name: str) -> bytes | None:
        """get the midi_bytes of the song with the provided username and id.
        return the bytes if found or none if not found"""
        with Session(self._engine) as session:
            song = session.query(SongTable).filter(
                SongTable.owner_id == owner_id,
                SongTable.name == song_name
            ).first()

            return song.midi_bytes if song else None


class UserTable(Base):
    """ORM model for the users table"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class UserManager:
    def __init__(self, db_engine):
        self._engine = db_engine

    @staticmethod
    def _hash_password(password: str):
        """hash the provided string and return it"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _compare_passwords(hashed_password: str, password: str) -> bool:
        """check if two passwords are the same when one is hashed."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())

    def save_user(self, username: str, password: str) -> bool:
        """save a new user to the users table. return true if user saved, else false."""
        with Session(self._engine) as session:
            # first of all, check if a user with this username already exists
            if session.query(UserTable).filter(
                    UserTable.username == username
            ).first():
                return False

            new_user = UserTable(username=username,
                                 hashed_password=self._hash_password(password)
                                 )

            session.add(new_user)
            session.commit()

            return True

    def delete_user(self, user_id: int) -> bool:
        """deletes a user from the table and returns if it was deleted or not."""
        with Session(self._engine) as session:
            user_deleted = session.query(UserTable).filter(
                UserTable.id == user_id
            ).delete()  # delete it

            session.commit()

            # delete returns an int
            return user_deleted > 0

    def update_password(self, user_id: int, new_password: str) -> bool:
        """changes the provided users password to the new password. return true if it worked, false if not."""
        with Session(self._engine) as session:
            user = session.query(UserTable).filter(
                UserTable.id == user_id
            ).first()

            if user:  # run only if user exists
                user.hashed_password = self._hash_password(new_password)
                session.commit()
                return True

            return False

    def get_user_by_id(self, user_id: int) -> UserTable | None:
        """return the user object with the user id."""
        with Session(self._engine) as session:
            return session.query(UserTable).filter(UserTable.id == user_id).first()

    def get_user_by_username(self, username: str) -> UserTable | None:
        """return the user object with the same username."""
        with Session(self._engine) as session:
            return session.query(UserTable).filter(UserTable.username == username).first()

    def verify_pair(self, username: str, password: str) -> bool:
        """return true if the username and password pair exists in the database, and false if it does not"""
        with Session(self._engine) as session:
            user = session.query(UserTable).filter(
                UserTable.username == username
            ).first()

            if not user:  # it wasn't found
                return False

            return self._compare_passwords(user.hashed_password, password)  # type: ignore
