import asyncio

import slowapi
from slowapi.util import get_remote_address
from starlette.requests import Request

from .._database import User
from .._routers.v1._common import authorize_user, authorize_token


def _jesus_christ_pls_somebody_kill_fastapi_devs_putting_async_in_VERY_unnecessary_places_thx(request: Request) -> str | None:
    from fastapi.security.utils import get_authorization_scheme_param

    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)

    if not authorization or scheme.lower() != "bearer":
        return None

    return param


def get_request_identifier(request: Request) -> str:
    user = authorize_user(authorize_token(_jesus_christ_pls_somebody_kill_fastapi_devs_putting_async_in_VERY_unnecessary_places_thx(request)))

    if user.id == User.ADMIN_ID:
        return ''
    elif user.id == User.GUEST_ID:
        return get_remote_address(request)
    else:
        return str(user.id)


limiter = slowapi.Limiter(key_func=get_request_identifier)
