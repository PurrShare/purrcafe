import os

import slowapi
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from . import _background as background
from ._middlewares import LoggingMiddleware
from ._routers._limiting import get_request_identifier, limiter
from ._routers.v1 import router as v1_api

app = FastAPI(
    openapi_url="/openapi.json" if os.environ.get('PURRCAFE_DOCS') == '1' else None
)

app.add_middleware(LoggingMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.environ.get('PURRCAFE_FUCK_OFF_CORS') == '1' else ["http://localhost:5173", os.environ.get('PURRCAFE_ORIGIN', "https://purrshare.net")],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_credentials=True
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, slowapi._rate_limit_exceeded_handler)


app.include_router(v1_api, prefix="/v1")


background.start_jobs()
