from dotenv import load_dotenv, find_dotenv
from os import getenv

load_dotenv(find_dotenv())

DB_USERNAME = getenv("POSTGRES_USERNAME", "root")
DB_PASSWORD = getenv("POSTGRES_PASSWORD", "password")
DB_NAME = getenv("POSTGRES_DB", "database")
DB_HOST = getenv("POSTGRES_HOST", "localhost")
DB_PORT = getenv("POSTGRES_PORT", 5432)
DB_URL = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

WEB_HOST = getenv("WEB_HOST", "0.0.0.0")
API_PORT = getenv("API_PORT", 8000)
