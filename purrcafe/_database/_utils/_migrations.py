from os import PathLike
from pathlib import Path
import sqlite3

from ..._logging import logger


def complete_migrations(database: sqlite3.Connection, migrations_path: PathLike | str | bytes, last_migration: int) -> int:
    migrations_path = Path(migrations_path)

    logger.debug(f"applying migrations from {migrations_path}")

    current_migration = last_migration
    for name, script in map(lambda path: (path.name, path.read_text()), sorted(filter(lambda path: path.is_file() and path.suffix in ('.sql', '.py') and path.name[3:5] == '__', migrations_path.iterdir()), key=lambda path: int(path.name[0:3]))):
        if (current_migration := int(name.split('__', 1)[0])) <= last_migration:
            logger.debug(f"skipping '{name}' migration...")

            continue

        logger.info(f"applying '{name}' migration...")

        if name.endswith('.py'):
            exec(script)
        else:
            if (pre_migration_script_path := migrations_path.joinpath(f"{current_migration}_pre.py")).exists():
                logger.debug(f"running pre migration script")
                exec(pre_migration_script_path.read_text())

            database.executescript(script)
            database.commit()

            if (post_migration_script_path := migrations_path.joinpath(f"{current_migration}_post.py")).exists():
                logger.debug(f"running post migration script")
                exec(post_migration_script_path.read_text())

    logger.info("finished migrations")

    return current_migration
