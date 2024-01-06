import datetime
import email.utils
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
        mime_type: Annotated[str, Header(alias="Content-Type")] = m_File.DEFAULT_CONTENT_TYPE,
        filename: str = None,
        decrypted_data_hash: Annotated[str, Header()] = None,
        max_access_count: Annotated[int, Header()] = None,
        anonymous: bool = False
) -> str:
    try:
        return str(m_File.create(
            uploader=user,
            uploader_hidden=anonymous,
            filename=filename,
            lifetime=m_File.DEFAULT_LIFETIME,
            data=data,
            decrypted_data_hash=decrypted_data_hash,
            mime_type=mime_type,
            max_access_count=max_access_count
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
@router.get("/{id}/n/{name}")
@limiter.limit("1/second", key_func=get_remote_address)
def get_file_data(
        request: Request,
        file: Annotated[m_File, Depends(get_file)],
        if_modified_since: Annotated[str, Header()] = None,
        t: bool = False
) -> Response:
    file.data_access_count += 1

    response = get_file_head(file, if_modified_since, t)

    if response.status_code == 200:
        response.content = file.data

    if file.max_access_count is not None and file.data_access_count + 1 > file.max_access_count:
        file.delete()

    return response


@router.head("/{id}")
@router.head("/{id}/n/{name}")
def get_file_head(
        file: Annotated[m_File, Depends(get_file)],
        if_modified_since: Annotated[str, Header()] = None,
        t: bool = False
) -> Response:
    if if_modified_since is not None and datetime.datetime.fromisoformat(if_modified_since) > file.upload_datetime:
        response = Response(
            status_code=304
        )
    else:
        response = Response(
            media_type=file.mime_type if not t else 'text/plain'
        )

        if file.decrypted_data_hash is not None:
            response.headers['Decrypted-Data-Hash'] = file.decrypted_data_hash

    response.headers.update({
        'Cache-Control': "public, max-age=604800" if file.max_access_count is None else "no-cache",  # TODO take into account file's expiration date for max age
        'Last-Modified': email.utils.format_datetime(file.upload_datetime)
    })

    return response


@router.get("/{id}/n")
def get_filename(file: Annotated[m_File, Depends(get_file)]) -> Response:
    return Response(
        status_code=308,
        headers={'Location': f'n/{file.filename}' if file.filename is not None else '.'}
    )


@router.get("/{id}/meta")
@limiter.limit("5/second", key_func=get_remote_address)
def get_file_meta(
        request: Request,
        file: Annotated[m_File, Depends(get_file)]
) -> s_FileMetadata:
    file.meta_access_count += 1

    return s_FileMetadata(
        uploader_id=str(file.uploader_id) if not file.uploader_hidden else None,
        upload_datetime=file.upload_datetime,
        expiration_datetime=file.expiration_datetime,
        filename=file.filename,
        decrypted_data_hash=file.decrypted_data_hash,
        mime_type=file.mime_type,
        data_access_count=file.data_access_count,
        max_access_count=file.max_access_count,
        file_size=file.file_size,
        meta_access_count=file.meta_access_count
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

    if user.id != m_User.ADMIN_ID and file.uploader_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="only the user who uploaded the file can delete it"
        )

    file.delete()
