from collections import deque
from typing import Callable
import threading


class _LockContextManager:
    _acquire_callback: Callable[[Callable[[], None]], None]
    _decquire_callback: Callable[[], None]

    def __init__(
            self,
            acquire_callback: Callable[[Callable[[], None]], None],
            decquire_callback: Callable[[], None]
    ) -> None:
        self._acquire_callback = acquire_callback
        self._decquire_callback = decquire_callback

    def __enter__(self) -> None:
        is_acquired = threading.Event()

        self._acquire_callback(is_acquired.set)

        is_acquired.wait()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._decquire_callback()


class RWLock:
    _writer_present: bool
    _readers_count: int

    _writer_queue: deque[Callable[[], None]]
    _reader_queue: deque[Callable[[], None]]

    reader: _LockContextManager
    writer: _LockContextManager

    def __init__(self) -> None:
        self._writer_present = False
        self._readers_count = 0

        self._writer_queue = deque()
        self._reader_queue = deque()

        self.reader = _LockContextManager(self._acquire_reader, self._decquire_reader)
        self.writer = _LockContextManager(self._acquire_writer, self._decquire_writer)

    def _acquire_reader(self, success_callback: Callable[[], None]) -> None:
        if self._writer_present:
            self._reader_queue.append(lambda: self._acquire_reader(success_callback))
        else:
            self._readers_count += 1

            success_callback()

    def _decquire_reader(self) -> None:
        if self._readers_count == 0:
            raise RuntimeError("decquired a non-existant reader (counter is negative)")
        else:
            self._readers_count -= 1

            if self._readers_count == 0 and self._writer_queue:
                self._writer_queue.popleft()()

    def _acquire_writer(self, success_callback: Callable[[], None]) -> None:
        if self._readers_count or self._writer_present:
            self._writer_queue.append(lambda: self._acquire_writer(success_callback))
        else:
            self._writer_present = True

            success_callback()

    def _decquire_writer(self) -> None:
        if not self._writer_present:
            raise RuntimeError("decquiring a non-existant writer (there are no writers present)")
        else:
            self._writer_present = False

            if self._reader_queue:
                self._reader_queue.popleft()()
