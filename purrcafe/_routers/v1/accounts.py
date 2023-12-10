from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ._common import authorize_user
from ._schemas import CreateUser as s_CreateUser, User as s_User, ForeignUser as s_ForeignUser, UpdateUser as s_UpdateUser
from ..._database import User as m_User
from ..._database.exceptions import WrongHashLengthError, IDNotFoundError
from ...meowid import MeowID

router = APIRouter()


@router.post("/")
def create_account(user_info: s_CreateUser) -> str:
    try:
        return str(m_User.create(
            name=user_info.name,
            email=user_info.email,
            password_hash=user_info.password_hash
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


@router.get("/{id}")
def get_foreign_user(id: str) -> s_ForeignUser:
    try:
        return s_ForeignUser.from_user(get_account(m_User.get(MeowID.from_str(id))))
    except IDNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="such user was not found"
        )


@router.patch("/me")
def update_account(user: Annotated[m_User, Depends(authorize_user)], patch: s_UpdateUser) -> None:
    if patch.name is not None:
        user.name = patch.name

    if patch.email is not None:
        user.email = patch.email

    if patch.password_hash is not None:
        user.password_hash = patch.password_hash


@router.delete("/me")
def delete_account(user: Annotated[m_User, Depends(authorize_user)]) -> None:
    user.delete()
