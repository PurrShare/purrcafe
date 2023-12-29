import os

import uvicorn

from . import app


uvicorn.run(
    app,
    host="0.0.0.0" if os.environ.get('PURRCAFE_LISTEN') == '1' else "localhost",
    port=int(os.environ.get('PURRCAFE_PORT', 8080)),
    log_level=os.environ.get('PURRCAFE_UVICORN_LOGLEVEL', "error")
)
