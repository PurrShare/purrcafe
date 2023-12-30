import logging
import logging.handlers
import os
import queue


logger = logging.getLogger("purrcafe")
logger.setLevel(os.environ.get('PURRCAFE_LOGLEVEL', 'INFO'))

_logging_queue = queue.Queue()
_queue_handler = logging.handlers.QueueHandler(_logging_queue)
logger.addHandler(_queue_handler)

_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s | %(module)s (%(funcName)s) - %(levelname)s | %(message)s"))

_queue_listener = logging.handlers.QueueListener(_logging_queue, _handler)
_queue_listener.start()
