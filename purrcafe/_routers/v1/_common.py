from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from ..._database import Session as m_Session, User as m_User, File as m_File
from ..._database.exceptions import IDNotFoundError
from ...meowid import MeowID

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/session/oauth2')


def authorize_token(token: Annotated[str, Depends(_oauth2_scheme)]) -> m_Session:
    try:
        return m_Session.get(MeowID.from_str(token))
    except IDNotFoundError:
        raise HTTPException(
            status_code=401,
            detail="token was not found",
            headers={'WWW-Authenticate': "Bearer"}
        ) from None


def authorize_user(session: Annotated[m_Session, Depends(authorize_token)]) -> m_User:
    return session.owner


def get_file(id: str) -> m_File:
    try:
        return m_File.get(MeowID.from_str(id))
    except IDNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="file was not found"
        )
