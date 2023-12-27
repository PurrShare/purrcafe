from __future__ import annotations
import datetime
from typing import Final

from . import User
from ._database import _Nothing, database as db, database_lock as db_l
from .exceptions import IDNotFoundError, ObjectIDUnknownError, OperationPermissionError
from ..meowid import MeowID


class Session:
    DEFAULT_LIFETIME: Final[datetime.timedelta] = datetime.timedelta(days=30)

    _id: MeowID | type[_Nothing] = _Nothing
    _owner_id: MeowID | type[_Nothing] = _Nothing
    _creation_datetime: datetime.datetime | type[_Nothing] = _Nothing
    _expiration_datetime: datetime.datetime | None | type[_Nothing] = _Nothing

    @property
    def id(self) -> MeowID:
        if self._id is _Nothing:
            raise ObjectIDUnknownError

        return self._id

    @property
    def owner_id(self) -> MeowID:
        if self._owner_id is _Nothing:
            with db_l.reader:
                self._owner_id = db.execute("SELECT owner_id FROM sessions WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._owner_id

    @property
    def owner(self) -> User:
        return User.get(self.owner_id)

    @property
    def creation_datetime(self) -> datetime.datetime:
        if self._creation_datetime is _Nothing:
            with db_l.reader:
                self._creation_datetime = db.execute("SELECT creation_datetime FROM sessions WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._creation_datetime

    @property
    def expiration_datetime(self) -> datetime.datetime | None:
        if self._expiration_datetime is _Nothing:
            with db_l.reader:
                self._expiration_datetime = db.execute("SELECT expiration_datetime FROM sessions WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._expiration_datetime

    @expiration_datetime.setter
    def expiration_datetime(self, new_expiration_datetime: datetime.datetime | None) -> None:
        if int(self.id) == 0:
            raise OperationPermissionError("changing guest session properties")

        with db_l.writer:
            db.execute("UPDATE sessions SET expiration_datetime=(?) WHERE id=(?)", (new_expiration_datetime, int(self.id)))
            db.commit()

        self._expiration_datetime = _Nothing

    def __init__(
            self,
            id: MeowID | int | type[_Nothing] = _Nothing,
            owner_id: MeowID | type[_Nothing] = _Nothing,
            creation_datetime: datetime.datetime | type[_Nothing] = _Nothing,
            expiration_datetime: datetime.datetime | None | type[_Nothing] = _Nothing
    ) -> None:
        self._id = MeowID.from_int(id) if isinstance(id, int) else id
        self._owner_id = owner_id
        self._creation_datetime = creation_datetime
        self._expiration_datetime = expiration_datetime

    @classmethod
    def get(cls, id_: MeowID) -> Session:
        with db_l.reader:
            raw_data = db.execute("SELECT * FROM sessions WHERE id=(?)", (int(id_),)).fetchone()

        if raw_data is None:
            raise IDNotFoundError("session", id_)

        return cls(*raw_data)

    @classmethod
    def get_all(cls) -> list[Session]:
        with db_l.reader:
            return [cls(*session_data) for session_data in db.execute("SELECT * FROM sessions").fetchall()]

    @classmethod
    def get_owned_by(cls, owner: User) -> list[Session]:
        with db_l.reader:
            return [cls(*session_data) for session_data in db.execute("SELECT * FROM sessions WHERE owner_id=(?)", (int(owner.id),)).fetchall()]

    @classmethod
    def create(cls, owner: User, lifetime: datetime.timedelta | None = DEFAULT_LIFETIME) -> Session:
        session = cls(
            MeowID.generate(),
            owner.id,
            (timestamp := datetime.datetime.now(datetime.UTC)),
            lifetime and timestamp + lifetime
        )

        with db_l.writer:
            db.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?)",
                (int(session._id), session._owner_id, session._creation_datetime, session._expiration_datetime)
            )
            db.commit()

        return session

    def delete(self) -> None:
        if int(self.id) == 0:
            raise OperationPermissionError("deletion of guest session")

        with db_l.writer:
            db.execute("DELETE FROM sessions WHERE id=(?)", (int(self.id),))
            db.commit()