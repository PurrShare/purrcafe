from os import PathLike
from pathlib import Path
import sqlite3

from ..._logging import logger


def complete_migrations(database: sqlite3.Connection, migrations_path: PathLike | str | bytes, last_migration: int) -> int:
    migrations_path = Path(migrations_path)

    logger.debug(f"applying migrations from {migrations_path}")

    final_migration = last_migration
    for name, script in map(lambda path: (path.name, path.read_text()), sorted(filter(lambda path: path.is_file() and path.suffix == '.sql', migrations_path.iterdir()), key=lambda path: path.name)):
        if (final_migration := int(name.split('_', 1)[0])) <= last_migration:
            logger.debug(f"skipping '{name}' migration...")

            continue

        logger.info(f"applying '{name}' migration...")
        database.executescript(script)
        database.commit()

    logger.info("finished migrations")

    return final_migration
