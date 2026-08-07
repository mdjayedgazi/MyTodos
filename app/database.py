from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

DATABASE_URL = (
    f"postgresql+psycopg://"
    f'{settings.DB_USER}:'
    f'{settings.DB_PASSWORD}@'
    f'{settings.DB_HOST}:'
    f'{settings.DB_PORT}/'
    f'{settings.DB_NAME}'
)

engine = create_engine(
    DATABASE_URL,
    echo=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass
