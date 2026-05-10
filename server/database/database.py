from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

DB_NAME = "database.db"

BASE_DIR = Path(__file__).parent.parent  # points to Server/
DB_PATH = BASE_DIR / "database" / DB_NAME

engine = create_engine(f"sqlite:///{DB_PATH}", echo=True)
Base = declarative_base()  # a base class
