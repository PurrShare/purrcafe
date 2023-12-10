from pathlib import Path

from ._database import database, database_lock
from ._utils import complete_migrations
from ._users import User
from ._sessions import Session
from ._files import File


with database_lock.writer:
    complete_migrations(database, Path(__file__).parent.joinpath("migrations"))
