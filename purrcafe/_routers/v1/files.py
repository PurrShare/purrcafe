from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Body
from fastapi.responses import Response, PlainTextResponse

from ._common import authorize_user, get_file
from ._schemas import FileMetadata as s_FileMetadata
from ..._database import File as m_File, User as m_User
from ..._database.exceptions import WrongHashLengthError, WrongValueLengthError

router = APIRouter()


@router.post('/', response_class=PlainTextResponse)
@router.post("/{filename}", response_class=PlainTextResponse)
async def upload_file(
        data: Annotated[bytes, Body(media_type="application/octet-stream")],
        user: Annotated[m_User, Depends(authorize_user)],
        encrypted_data_hash: Annotated[str, Header()],
        mime_type: Annotated[str, Header(alias="Content-Type")],
        filename: str = None,
        anonymous: bool = False
) -> str:
    try:
        return str(m_File.create(
            uploader=user,
            uploader_hidden=anonymous,
            filename=filename,
            encrypted_data=data,
            encrypted_data_hash=encrypted_data_hash,
            mime_type=mime_type
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
def get_file_data(file: Annotated[m_File, Depends(get_file)], t: bool = False) -> Response:
    return Response(
        content=file.encrypted_data,
        headers={'Encrypted-Data-Hash': file.encrypted_data_hash},
        media_type=file.mime_type if not t else 'text/plain'
    )


@router.get("/{id}/n")
def get_filename(file: Annotated[m_File, Depends(get_file)]) -> Response:
    return Response(
        status_code=308,
        headers={'Location': f'n/{file.filename}' if file.filename is not None else '.'}
    )


@router.get("/{id}/n/{name}")
def get_file_data_with_name(file: Annotated[m_File, Depends(get_file)], name: str = None) -> Response:
    return Response(
        content=file.encrypted_data,
        headers={'Encrypted-Data-Hash': file.encrypted_data_hash},
        media_type=file.mime_type
    )


@router.get("/{id}/meta")
def get_file_meta(file: Annotated[m_File, Depends(get_file)]) -> s_FileMetadata:
    return s_FileMetadata(
        uploader_id=str(file.uploader_id) if not file.uploader_hidden else None,
        upload_datetime=file.upload_datetime,
        expiration_datetime=file.expiration_datetime,
        filename=file.filename,
        mime_type=file.mime_type
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
