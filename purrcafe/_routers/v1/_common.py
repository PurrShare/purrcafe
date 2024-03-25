from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

import meowid
from meowid import MeowID

from ..._database import Session as m_Session, User as m_User, File as m_File
from ..._database.exceptions import IDNotFoundError

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/session/oauth2', auto_error=False)


def parse_meowid(meowid_str: str) -> MeowID:
    try:
        return MeowID.from_str(meowid_str)
    except meowid.MeowIDInvalid:
        raise HTTPException(
            status_code=422,
            detail="invalid meowid"
        )


def authorize_token(token: Annotated[str | None, Depends(_oauth2_scheme)]) -> m_Session:
    try:
        if token is not None:
            return m_Session.get(parse_meowid(token))
        else:
            return m_Session.get(MeowID.from_int(0))
    except IDNotFoundError:
        raise HTTPException(
            status_code=401,
            detail="token was not found",
            headers={'WWW-Authenticate': "Bearer"}
        ) from None


def get_user(id: str) -> m_User:
    try:
        return m_User.get(parse_meowid(id))
    except IDNotFoundError as err:
        raise HTTPException(
            status_code=404,
            detail=str(err)
        )


def authorize_user(session: Annotated[m_Session, Depends(authorize_token)]) -> m_User:
    return session.owner


def get_file(id: str) -> m_File:
    try:
        file = m_File.get(parse_meowid(id))
    except IDNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="file was not found"
        )
    else:
        if file.is_expired():
            file.delete()

            raise HTTPException(
                status_code=404,
                detail="file was not found"
            )

        return file
