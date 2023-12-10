# XXX the reason this is moved into a separate module is the (beloved) circular import issue

import os
import sqlite3

from .._utils import RWLock

database = sqlite3.connect(os.environ.get('PURRCAFE_DB_PATH', "purrcafe.sqlite3"), check_same_thread=False)
database_lock = RWLock()


class _Nothing:
    pass
