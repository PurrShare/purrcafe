import os

import slowapi
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI

from ._middlewares import LoggingMiddleware
from ._routers._limiting import get_request_identifier, limiter
from ._routers.v1 import router as v1_api

app = FastAPI(
    openapi_url="/openapi.json" if os.environ.get('PURRCAFE_DOCS') == '1' else None
)

app.add_middleware(LoggingMiddleware)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, slowapi._rate_limit_exceeded_handler)


app.include_router(v1_api, prefix="/v1")
