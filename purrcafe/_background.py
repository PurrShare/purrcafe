import datetime
import os
import threading
import time

from ._database import File


def _expired_deleter_worker() -> None:
    while True:
        File.delete_all_expired()

        time.sleep(datetime.timedelta(hours=int(os.environ.get('PURRCAFE_EXPIRED_CHECK_DELAY', 1))).total_seconds())


def start_jobs() -> None:
    threading.Thread(daemon=True, target=_expired_deleter_worker).start()
