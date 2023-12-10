from fastapi import APIRouter

from .accounts import router as accounts_api
from .session import router as session_api
from .files import router as files_api

router = APIRouter()


router.include_router(accounts_api, prefix="/accounts")
router.include_router(session_api, prefix="/session")
router.include_router(files_api, prefix="/files")
