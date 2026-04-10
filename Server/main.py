from fastapi import FastAPI

from Server.DB.database import Base, engine
from Server.routers import auth, songs

# fastapi
app = FastAPI()

app.include_router(auth.router)
app.include_router(songs.router)

Base.metadata.create_all(engine)  # ensure tables exist

print("Server initialized.")
