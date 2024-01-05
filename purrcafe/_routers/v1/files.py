from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Body
from fastapi.responses import Response, PlainTextResponse
from slowapi.util import get_remote_address
from starlette.requests import Request

from ._common import authorize_user, get_file
from ._schemas import FileMetadata as s_FileMetadata
from ... import limiter
from ..._database import File as m_File, User as m_User
from ..._database.exceptions import WrongHashLengthError, WrongValueLengthError

router = APIRouter()


@router.post('/', response_class=PlainTextResponse)
@router.post("/{filename}", response_class=PlainTextResponse)
@limiter.limit("2/minute")
async def upload_file(
        request: Request,
        data: Annotated[bytes, Body(media_type="application/octet-stream")],
        user: Annotated[m_User, Depends(authorize_user)],
        mime_type: Annotated[str, Header(alias="Content-Type")],
        filename: str = None,
        decrypted_data_hash: Annotated[str, Header()] = None,
        anonymous: bool = False
) -> str:
    try:
        return str(m_File.create(
            uploader=user,
            uploader_hidden=anonymous,
            filename=filename,
            data=data,
            decrypted_data_hash=decrypted_data_hash,
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
@limiter.limit("1/second", key_func=get_remote_address)
def get_file_data(
        request: Request,
        file: Annotated[m_File, Depends(get_file)],
        t: bool = False
) -> Response:
    return Response(
        content=file.data,
        headers={'Decrypted-Data-Hash': file.decrypted_data_hash} if file.decrypted_data_hash is not None else {},
        media_type=file.mime_type if not t else 'text/plain'
    )


@router.get("/{id}/n")
def get_filename(file: Annotated[m_File, Depends(get_file)]) -> Response:
    return Response(
        status_code=308,
        headers={'Location': f'n/{file.filename}' if file.filename is not None else '.'}
    )


@router.get("/{id}/n/{name}")
@limiter.limit("1/second", key_func=get_remote_address)
def get_file_data_with_name(
        request: Request,
        file: Annotated[m_File, Depends(get_file)]
) -> Response:
    return Response(
        content=file.data,
        headers={'Decrypted-Data-Hash': file.decrypted_data_hash} if file.decrypted_data_hash is not None else {},
        media_type=file.mime_type
    )


@router.get("/{id}/meta")
@limiter.limit("5/second", key_func=get_remote_address)
def get_file_meta(
        request: Request,
        file: Annotated[m_File, Depends(get_file)]
) -> s_FileMetadata:
    return s_FileMetadata(
        uploader_id=str(file.uploader_id) if not file.uploader_hidden else None,
        upload_datetime=file.upload_datetime,
        expiration_datetime=file.expiration_datetime,
        filename=file.filename,
        decrypted_data_hash=file.decrypted_data_hash,
        mime_type=file.mime_type
    )


@router.delete("/{id}")
@limiter.limit("5/minute")
def delete_file(
        request: Request,
        user: Annotated[m_User, Depends(authorize_user)],
        file: Annotated[m_File, Depends(get_file)]
) -> None:
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
