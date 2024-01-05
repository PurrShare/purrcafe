import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import PlainTextResponse
from slowapi.util import get_remote_address
from starlette.requests import Request

from ._common import authorize_token, authorize_user
from ._schemas import CreateSession as s_CreateSession, Session as s_Session, OAuth2LoginInfo
from ... import limiter
from ..._database import User as m_User, Session as m_Session
from ..._database.exceptions import ObjectNotFound, ValueMismatchError

router = APIRouter()


@router.get("/")
def session_info(session: Annotated[m_Session, Depends(authorize_token)]) -> s_Session:
    return s_Session(
        creation_datetime=session.creation_datetime,
        expiration_datetime=session.expiration_datetime
    )


@router.get("/all")
def get_all_sessions(user: Annotated[m_User, Depends(authorize_user)]) -> list[str]:
    return [str(session.id) for session in user.sessions]


# @router.post("/", response_class=PlainTextResponse)
# @limiter.limit("20/minute", key_func=get_remote_address)
# def login(
#         request: Request,
#         credentials: s_CreateSession
# ) -> str:
#     try:
#         return str(m_User.find(credentials.owner_name).authorize(credentials.password).id)
#     except (ObjectNotFound, ValueMismatchError):
#         raise HTTPException(
#             status_code=401,
#             detail="user was not found or password is invalid"
#         )


@router.post("/")
@limiter.limit("20/minute", key_func=get_remote_address)
def login_oauth2(
        request: Request,
        credentials: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> OAuth2LoginInfo:
    try:
        return OAuth2LoginInfo(access_token=str(m_User.find(credentials.username).authorize(hashlib.sha3_512(credentials.password.encode('utf-8')).hexdigest()).id))
    except (ObjectNotFound, ValueMismatchError):
        raise HTTPException(
            status_code=401,
            detail="user was not found or password is invalid"
        )


@router.delete("/")
@limiter.limit("20/minute")
def logout(
        request: Request,
        user: Annotated[m_User, Depends(authorize_user)],
        session: Annotated[m_Session, Depends(authorize_token)]
) -> None:
    if int(session.id) == 0:
        raise HTTPException(
            status_code=403,
            detail="cannot delete guest session"
        )

    session.delete()
