from pathlib import Path

from ._database import database, database_lock
from ._utils import complete_migrations
from ._users import User
from ._sessions import Session
from ._files import File


def _complete_migrations():
    migrations_path = Path(__file__).parent.joinpath("migrations")

    state_file = migrations_path.joinpath("state")
    last_migration = int(state_file.read_text()) if state_file.exists() else -1

    with database_lock.writer:
        final_migration = complete_migrations(database, migrations_path, last_migration)

    state_file.write_text(str(final_migration))


_complete_migrations()
