from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import Response, PlainTextResponse
from fastapi.requests import Request

from ._common import authorize_user, get_file
from ._schemas import FileMetadata as s_FileMetadata
from ..._database import File as m_File, User as m_User
from ..._database.exceptions import WrongHashLengthError, WrongValueLengthError

router = APIRouter()


@router.post("/{filename}", response_class=PlainTextResponse)
async def upload_file(
        request: Request,
        user: Annotated[m_User, Depends(authorize_user)],
        encrypted_data_hash: Annotated[str, Header(name="Encrypted-Data-Hash")],
        filename: str | None = None,
        anonymous: bool = False
) -> str:
    try:
        return str(m_File.create(
            uploader=user,
            uploader_hidden=anonymous,
            filename=filename,
            encrypted_data=await request.body(),
            encrypted_data_hash=encrypted_data_hash
        ).id)
    except WrongHashLengthError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        ) from None
    except WrongValueLengthError as e:
        raise HTTPException(
            status_code=413,
            detail=str(e)
        ) from None


@router.get("/{id}")
def get_file_data(file: Annotated[m_File, Depends(get_file)]) -> Response:
    return Response(
        content=file.encrypted_data,
        headers={'Encrypted-Data-Hash': file.encrypted_data_hash},
        media_type='application/octet-stream'
    )


@router.get("/{id}/meta")
def get_file_meta(file: Annotated[m_File, Depends(get_file)]) -> s_FileMetadata:
    return s_FileMetadata(
        uploader_id=str(file.uploader_id) if not file.uploader_hidden else None,
        upload_datetime=file.upload_datetime,
        expiration_datetime=file.expiration_datetime,
        filename=file.filename
    )


@router.delete("/{id}")
def delete_file(user: Annotated[m_User, Depends(authorize_user)], file: Annotated[m_File, Depends(get_file)]) -> None:
    if int(file.uploader_id) == 0:
        raise HTTPException(
            status_code=403,
            detail="cannot delete file uploaded by guest user"
        )

    if file.uploader_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="only the user who uploaded the file can delete it"
        )

    file.delete()
