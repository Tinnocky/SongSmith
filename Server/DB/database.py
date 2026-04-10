import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

DB_NAME = "database.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # points to Server/
DB_PATH = os.path.join(BASE_DIR, "DB", DB_NAME)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=True)
Base = declarative_base()  # a base class

