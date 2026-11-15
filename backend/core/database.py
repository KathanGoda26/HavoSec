"""MongoDB configuration shared by the API and explicit maintenance commands."""
from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request


def load_backend_environment():
    # Resolve independently of the shell working directory; process env wins.
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)


@dataclass(frozen=True)
class DatabaseSettings:
    mongo_url: str = field(repr=False)
    database_name: str

    @classmethod
    def from_environment(cls):
        return cls(
            os.environ.get('MONGO_URL', 'mongodb://localhost:27017'),
            os.environ.get('DB_NAME', 'havosec'),
        )


def create_database_client(settings: DatabaseSettings):
    # Preserve legacy datetime decoding until legacy auth dates are migrated.
    return AsyncIOMotorClient(settings.mongo_url, serverSelectionTimeoutMS=5000)


def get_database(request: Request):
    return request.app.state.db
