from __future__ import annotations
import datetime
from typing import Literal

from pydantic.dataclasses import dataclass

from ..._database import Session as m_Session


@dataclass
class User:
    id: str
    name: str
    email: str
    creation_datetime: datetime.datetime


@dataclass
class ForeignUser:
    name: str
    creation_datetime: datetime.datetime

    @classmethod
    def from_user(cls, user: User) -> ForeignUser:
        return cls(
            name=user.name,
            creation_datetime=user.creation_datetime
        )


@dataclass
class CreateUser:
    name: str
    email: str
    password_hash: str


@dataclass
class UpdateUser:
    name: str | None = None
    email: str | None = None
    password_hash: str | None = None


@dataclass
class Session:
    creation_datetime: datetime.datetime
    expiration_datetime: datetime.datetime | None


@dataclass
class CreateSession:
    owner_name: str
    password_hash: str
    lifetime: datetime.timedelta = m_Session.DEFAULT_LIFETIME


@dataclass
class FileMetadata:
    uploader_id: str | None
    upload_datetime: datetime.datetime
    expiration_datetime: datetime.datetime | None
    filename: str | None


@dataclass
class OAuth2LoginInfo:
    access_token: str
    token_type: Literal["bearer"] = "bearer"
