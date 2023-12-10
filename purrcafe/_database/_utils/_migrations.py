from os import PathLike
from pathlib import Path
import sqlite3

from ..._logging import logger


def complete_migrations(database: sqlite3.Connection, migrations_path: PathLike | str | bytes) -> None:
    migrations_path = Path(migrations_path)

    logger.debug(f"applying migrations from {migrations_path}")

    for name, script in map(lambda path: (path.name, path.read_text()), filter(lambda path: path.is_file() and path.suffix == '.sql', migrations_path.iterdir())):
        logger.info(f"applying '{name}' migration...")
        database.executescript(script)
        database.commit()

    logger.info("finished migrations")
