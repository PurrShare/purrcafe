from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from slowapi.util import get_remote_address
from starlette.requests import Request

from ._common import authorize_user
from ._schemas import CreateUser as s_CreateUser, User as s_User, ForeignUser as s_ForeignUser, UpdateUser as s_UpdateUser
from ... import limiter
from ..._database import User as m_User
from ..._database._database import _Nothing
from ..._database.exceptions import WrongHashLengthError, IDNotFoundError
from ..._utils import hash_password
from ...meowid import MeowID

router = APIRouter()


@router.post("/", response_class=PlainTextResponse)
@limiter.limit("3/hour", key_func=get_remote_address)
def create_account(
        request: Request,
        user_info: s_CreateUser
) -> str:
    try:
        return str(m_User.create(
            name=user_info.name,
            email=user_info.email,
            password_hash=hash_password(user_info.password)
        ).id)
    except WrongHashLengthError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        ) from None


@router.get("/me")
def get_account(user: Annotated[m_User, Depends(authorize_user)]) -> s_User:
    return s_User(
        id=str(user.id),
        name=user.name,
        email=user.email,
        creation_datetime=user.creation_datetime
    )


@router.get("/me/files")
def get_uploaded_files(user: Annotated[m_User, Depends(authorize_user)]) -> list[str]:
    if int(user.id) == 0:
        raise HTTPException(
            status_code=403,
            detail="can't view uploaded files if a guest",
        )

    return [str(file.id) for file in user.uploaded_files]


@router.get("/{id}")
@limiter.limit("1/second", key_func=get_remote_address)
def get_foreign_user(
        request: Request,
        id: str
) -> s_ForeignUser:
    try:
        return s_ForeignUser.from_user(get_account(m_User.get(MeowID.from_str(id))))
    except IDNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="such user was not found"
        )


@router.patch("/me")
@limiter.limit("20/minute")
def update_account(
        request: Request,
        user: Annotated[m_User, Depends(authorize_user)],
        patch: s_UpdateUser
) -> None:
    if int(user.id) == 0:
        raise HTTPException(
            status_code=403,
            detail="cannot patch guest user"
        )

    if patch.name is not _Nothing:
        user.name = patch.name

    if patch.email is not _Nothing:
        user.email = patch.email

    if patch.password is not _Nothing:
        user.password_hash = hash_password(patch.password)


@router.delete("/me")
@limiter.limit("5/hour", key_func=get_remote_address)
def delete_account(
        request: Request,
        user: Annotated[m_User, Depends(authorize_user)]
) -> None:
    if int(user.id) == 0:
        raise HTTPException(
            status_code=403,
            detail="cannot delete guest user"
        )

    user.delete()
