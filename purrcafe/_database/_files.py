from __future__ import annotations
import datetime
import os
from typing import Final

from . import User
from ._database import _Nothing, database as db, database_lock as db_l
from .exceptions import WrongHashLengthError, IDNotFoundError, ObjectIDUnknownError, WrongValueLengthError, OperationPermissionError
from ..meowid import MeowID


class File:
    DEFAULT_LIFETIME: Final[datetime.timedelta] = datetime.timedelta(days=7)
    ENCRYPTED_DATA_HASH_LENGTH: Final[int] = 32
    GUEST_MAX_FILE_SIZE: Final[int] = os.environ.get('PURRCAFE_MAXSIZE_GUEST', 20971520)  # 20 MiB
    MAX_FILE_SIZE = os.environ.get('PURRCAFE_MAXSIZE', 31457280)  # 30 MiB

    _id: MeowID | type[_Nothing]
    _uploader_id: MeowID | type[_Nothing]
    _uploader_hidden: bool | type[_Nothing]
    _upload_datetime: datetime.datetime | type[_Nothing]
    _expiration_datetime: datetime.datetime | None | type[_Nothing]
    _filename: str | None | type[_Nothing]
    _data: bytes | type[_Nothing]
    _decrypted_data_hash: str | None | type[_Nothing]
    _mime_type: str | type[_Nothing]

    @property
    def id(self) -> MeowID:
        if self._id is _Nothing:
            raise ObjectIDUnknownError

        return self._id

    @property
    def uploader_id(self) -> MeowID:
        if self._uploader_id is _Nothing:
            with db_l.reader:
                self._uploader_id = db.execute("SELECT uploader_id FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._uploader_id

    @property
    def uploader(self) -> User:
        return User.get(self.uploader_id)

    @property
    def uploader_hidden(self) -> bool:
        if self._uploader_hidden is _Nothing:
            with db_l.reader:
                self._uploader_hidden = db.execute("SELECT uploader_hidden FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._uploader_hidden

    @uploader_hidden.setter
    def uploader_hidden(self, new_uploader_hidden: bool) -> None:
        with db_l.writer:
            db.execute("UPDATE files SET uploader_hidden=(?) WHERE id=(?)", (new_uploader_hidden, int(self.id)))
            db.commit()

        self._uploader_hidden = new_uploader_hidden

    @property
    def upload_datetime(self) -> datetime.datetime:
        if self._upload_datetime is _Nothing:
            with db_l.reader:
                self._upload_datetime = db.execute("SELECT upload_datetime FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._upload_datetime

    @property
    def expiration_datetime(self) -> datetime.datetime | None :
        if self._expiration_datetime is _Nothing:
            with db_l.reader:
                self._expiration_datetime = db.execute("SELECT expiration_datetime FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._expiration_datetime

    @expiration_datetime.setter
    def expiration_datetime(self, new_expiration_datetime: datetime.datetime | None ) -> None:
        with db_l.writer:
            db.execute("UPDATE files SET expiration_datetime=(?) WHERE id=(?)", (new_expiration_datetime, int(self.id)))
            db.commit()

        self._expiration_datetime = new_expiration_datetime

    @property
    def filename(self) -> str | None:
        if self._filename is _Nothing:
            with db_l.reader:
                self._filename = db.execute("SELECT filename FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._filename

    @filename.setter
    def filename(self, new_filename: str | None) -> None:
        with db_l.writer:
            db.execute("UPDATE files SET filename=(?) WHERE id=(?)", (new_filename, int(self.id)))
            db.commit()

        self._filename = _Nothing

    @property
    def data(self) -> bytes:
        if self._data is _Nothing:
            with db_l.reader:
                self._data = db.execute("SELECT data FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._data

    @data.setter
    def data(self, new_data: bytes) -> None:
        with db_l.writer:
            db.execute("UPDATE files SET data=(?) WHERE id=(?)", (new_data, int(self.id)))
            db.commit()

        self._data = new_data

    @property
    def decrypted_data_hash(self) -> str:
        if self._decrypted_data_hash is _Nothing:
            with db_l.reader:
                self._decrypted_data_hash = db.execute("SELECT decrypted_data_hash FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._decrypted_data_hash

    @decrypted_data_hash.setter
    def decrypted_data_hash(self, new_decrypted_data_hash: str) -> None:
        with db_l.writer:
            db.execute("UPDATE files SET decrypted_data_hash=(?) WHERE id=(?)", (new_decrypted_data_hash, int(self.id)))
            db.commit()

        self._decrypted_data_hash = new_decrypted_data_hash

    @property
    def mime_type(self) -> str:
        if self._mime_type is _Nothing:
            with db_l.reader:
                self._mime_type = db.execute("SELECT mime_type FROM files WHERE id=(?)", (int(self.id),)).fetchone()[0]

        return self._mime_type

    @mime_type.setter
    def mime_type(self, new_mime_type: str) -> None:
        with db_l.writer:
            db.execute("UPDATE files SET mime_type=(?) WHERE id=(?)", (new_mime_type, int(self.id)))
            db.commit()

        self._mime_type = new_mime_type

    def __init__(
            self,
            id: MeowID | int | type[_Nothing] = _Nothing,
            uploader_id: MeowID | type[_Nothing] = _Nothing,
            uploader_hidden: bool | type[_Nothing] = _Nothing,
            upload_datetime: datetime.datetime | type[_Nothing] = _Nothing,
            expiration_datetime: datetime.datetime | type[_Nothing] = _Nothing,
            filename: str | None | type[_Nothing] = _Nothing,
            data: bytes | type[_Nothing] = _Nothing,
            decrypted_data_hash: str | None | type[_Nothing] = _Nothing,
            mime_type: str | type[_Nothing] = _Nothing
    ) -> None:
        self._id = MeowID.from_int(id) if isinstance(id, int) else id
        self._uploader_id = uploader_id
        self._uploader_hidden = uploader_hidden
        self._upload_datetime = upload_datetime
        self._expiration_datetime = expiration_datetime
        self._filename = filename
        self._data = data
        self._decrypted_data_hash = decrypted_data_hash
        self._mime_type = mime_type

    @classmethod
    def get(cls, id_: MeowID) -> File:
        with db_l.reader:
            raw_data = db.execute("SELECT * FROM files WHERE id=(?)", (int(id_),)).fetchone()

        if raw_data is None:
            raise IDNotFoundError("file", id_)

        return cls(*raw_data)

    @classmethod
    def get_all(cls) -> list[File]:
        with db_l.reader:
            return [cls(*file_data) for file_data in db.execute("SELECT * FROM files").fetchall()]

    @classmethod
    def get_uploaded_by(cls, uploader: User) -> list[File]:
        with db_l.reader:
            return [cls(*file_data) for file_data in db.execute("SELECT * FROM files WHERE uploader_id=(?)", (int(uploader.id),)).fetchall()]

    @classmethod
    def create(cls, uploader: User, uploader_hidden: bool, filename: str | None, data: bytes, decrypted_data_hash: str | None, mime_type: str, lifetime: datetime.timedelta | None = DEFAULT_LIFETIME) -> File:
        if decrypted_data_hash is not None and len(decrypted_data_hash) != cls.ENCRYPTED_DATA_HASH_LENGTH:
            raise WrongHashLengthError("encrypted data", len(decrypted_data_hash), cls.ENCRYPTED_DATA_HASH_LENGTH)

        if uploader.id != User.ADMIN_ID:
            if len(data) > (max_file_size := (cls.MAX_FILE_SIZE if int(uploader.id) != User.GUEST_ID else cls.GUEST_MAX_FILE_SIZE)):
                raise WrongValueLengthError("encrypted data", "byte(s)", max_file_size, None, len(data))

        file = cls(
            MeowID.generate(),
            uploader.id,
            uploader_hidden,
            (timestamp := datetime.datetime.now(datetime.UTC)),
            lifetime and timestamp + lifetime,
            filename,
            data,
            decrypted_data_hash,
            mime_type
        )

        with db_l.writer:
            db.execute(
                "INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (int(file._id), int(file._uploader_id), file._uploader_hidden, file._upload_datetime, file._expiration_datetime, file._filename, file._data, file._decrypted_data_hash, file._mime_type)
            )
            db.commit()

        return file

    def delete(self) -> None:
        if int(self.uploader_id) == 0:
            raise OperationPermissionError("deletion of files uploaded by guest")

        with db_l.writer:
            db.execute("DELETE FROM files WHERE id=(?)", (int(self.id),))
            db.commit()
