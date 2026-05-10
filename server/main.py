from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from server.database.database import Base, engine
from server.routers import auth, songs

# fastapi
app = FastAPI()

app.include_router(auth.router)
app.include_router(songs.router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """handle value error exceptions by returning a 400 bad request response"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


Base.metadata.create_all(engine)  # ensure tables exist

print("server initialized.")
