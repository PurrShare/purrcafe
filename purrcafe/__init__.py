import os

from fastapi import FastAPI


app = FastAPI(
    openapi_url="/openapi.json" if os.environ.get('PURRCAFE_DOCS') == '1' else None
)
