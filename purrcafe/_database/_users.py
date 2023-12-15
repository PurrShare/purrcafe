from __future__ import annotations
import datetime
from typing import Final
import typing

from ._database import database as db, database_lock as db_l, _Nothing
from .exceptions import WrongHashLengthError, IDNotFoundError, ObjectIDUnknownError, WrongValueLengthError, ValueMismatchError, ObjectNotFound, OperationPermissionError
from ..meowid import MeowID
if typing.TYPE_CHECKING:
    from ._sessions import Session
    from ._files import File


class User:
    NAME_MAX_LENGTH: Final[int] = 32
    PASSWORD_HASH_LENGTH: Final[int] = 128

    _id: MeowID | type[_Nothing] = _Nothing
    _name: str | type[_Nothing] = _Nothing
    _email: str | type[_Nothing] = _Nothing
    _password_hash: str | type[_Nothing] = _Nothing
    _creation_datetime: datetime.datetime | type[_Nothing] = _Nothing

    @property
    def id(self) -> MeowID:
        if self._id is _Nothing:
            raise ObjectIDUnknownError

        return self._id

    @property
    def name(self) -> str:
        if self._name is _Nothing:
            with db_l.reader:
                self._name = db.execute("SELECT name FROM users WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        if int(self.id) == 0:
            raise OperationPermissionError("changing guest user properties")

        if len(new_name) > self.NAME_MAX_LENGTH:
            raise WrongValueLengthError("name", "characters", self.NAME_MAX_LENGTH, None, len(new_name))

        with db_l.writer:
            db.execute("UPDATE users SET name=(?) WHERE id=(?)", (new_name, int(self.id)))
            db.commit()

        self._name = _Nothing

    @property
    def email(self) -> str:
        if self._email is _Nothing:
            with db_l.reader:
                self._email = db.execute("SELECT email FROM users WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._email

    @email.setter
    def email(self, new_email: str) -> None:
        if int(self.id) == 0:
            raise OperationPermissionError("changing guest user properties")

        with db_l.writer:
            db.execute("UPDATE users SET email=(?) WHERE id=(?)", (new_email, int(self.id)))
            db.commit()

        self._email = _Nothing

    @property
    def password_hash(self) -> str:
        if self._password_hash is _Nothing:
            with db_l.reader:
                self._password_hash = db.execute("SELECT password_hash FROM users WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._password_hash

    @password_hash.setter
    def password_hash(self, new_password_hash: str) -> None:
        if int(self.id) == 0:
            raise OperationPermissionError("changing guest user properties")

        if len(new_password_hash) != self.PASSWORD_HASH_LENGTH:
            raise WrongHashLengthError("password", self.PASSWORD_HASH_LENGTH, len(new_password_hash))

        with db_l.writer:
            db.execute("UPDATE users SET password_hash=(?) WHERE id=(?)", (new_password_hash, int(self.id)))
            db.commit()

        self._password_hash = _Nothing

    @property
    def creation_datetime(self):
        if self._creation_datetime is _Nothing:
            with db_l.reader:
                self._creation_datetime = db.execute("SELECT creation_datetime FROM users WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._creation_datetime

    @property
    def sessions(self) -> list[Session]:
        from ._sessions import Session

        return Session.get_owned_by(self)

    @property
    def files(self):
        return File.get_uploaded_by(self)

    def __init__(
            self,
            id: MeowID | int | type[_Nothing] = _Nothing,
            name: str | type[_Nothing] = _Nothing,
            email: str | type[_Nothing] = _Nothing,
            password_hash: str | type[_Nothing] = _Nothing,
            creation_datetime: datetime.datetime | type[_Nothing] = _Nothing
    ) -> None:
        self._id = MeowID.from_int(id) if isinstance(id, int) else id
        self._name = name
        self._email = email
        self._password_hash = password_hash
        self._creation_datetime = creation_datetime

    @classmethod
    def create(cls, name: str, email: str, password_hash: str) -> User:
        # TODO somehow remove the need to duplicate the checks
        if len(name) > cls.NAME_MAX_LENGTH:
            raise WrongValueLengthError("name", "characters", cls.NAME_MAX_LENGTH, None, len(name))

        if len(password_hash) != cls.PASSWORD_HASH_LENGTH:
            raise WrongHashLengthError("password", cls.PASSWORD_HASH_LENGTH, len(password_hash))

        user = cls(
            MeowID.generate(),
            name,
            email,
            password_hash
        )

        with db_l.writer:
            db.execute(
                "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (int(user._id), user._name, user._email, user._password_hash)
            )
            db.commit()

        return user

    def authorize(self, password_hash: str, lifetime: datetime.timedelta = datetime.timedelta(days=7)) -> Session:  # i LOVE circular dependency error
        if int(self.id) == 0:
            raise OperationPermissionError("logging into guest account")

        from ._sessions import Session

        if self.password_hash != password_hash:
            raise ValueMismatchError("password", None, None)

        return Session.create(self, lifetime)

    @classmethod
    def get(cls, id_: MeowID) -> User:
        with db_l.reader:
            raw_data = db.execute("SELECT * FROM users WHERE id=(?)", (int(id_),)).fetchone()

        if raw_data is None:
            raise IDNotFoundError("session", id_)

        return cls(*raw_data)

    @classmethod
    def get_all(cls) -> list[User]:
        with db_l.reader:
            return [cls(*user_data) for user_data in db.execute("SELECT * FROM users").fetchall()]

    @classmethod
    def find(cls, name: str) -> User:
        with db_l.reader:
            raw_data = db.execute("SELECT * FROM users WHERE name=(?)", (name,)).fetchone()

        if raw_data is None:
            raise ObjectNotFound("user", "name", str, name)

        return cls(*raw_data)

    def delete(self) -> None:
        if int(self.id) == 0:
            raise OperationPermissionError("deletion of guest user")

        for session in self.sessions:
            session.delete()

        for file in self.files:
            file.delete()

        with db_l.writer:
            db.execute("DELETE FROM users WHERE id=(?)", (int(self.id),))
            db.commit()
