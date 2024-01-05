from __future__ import annotations
import math
import random
import datetime
import time
from typing import Final, Any, Generator


class MeowIDError(RuntimeError):
    pass


class MeowIDInvalid(ValueError, MeowIDError):
    pass


class MeowIDExhaustedError(MeowIDError):
    pass


class MeowID:
    TIMESTAMP_OFFSET: Final[int] = 32
    SEQUENCE_COUNT_OFFSET: Final[int] = 20
    SALT_OFFSET: Final[int] = 0

    TIMESTAMP_MASK: Final[int] = 0xFFFFFFFF00000000
    SEQUENCE_COUNT_MASK: Final[int] = 0x00000000FFF00000
    SALT_MASK: Final[int] = 0x00000000000FFFFF

    TIMESTAMP_MAX_VALUE: Final[int] = 2 ** 32 - 1
    SEQUENCE_COUNT_MAX_VALUE: Final[int] = 2 ** 12 - 1
    SALT_MAX_VALUE: Final[int] = 2 ** 20 - 1

    timestamp: datetime.datetime
    sequence_count: int
    salt: int

    @property
    def timestamp_s(self):
        return math.floor(self.timestamp.timestamp())

    _last_timestamp: datetime.datetime | None = None
    _sequence_count: int = 0

    _initialised: bool = False

    def __init__(
            self,
            timestamp: datetime.datetime | None = None,
            sequence_count: int = 0,
            salt: int = 0,
            *,
            _checked: bool = True
    ) -> None:
        if timestamp is None:
            timestamp = datetime.datetime.fromtimestamp(0, datetime.UTC)

        if _checked:
            if (timestamp_t := timestamp.timestamp()) != (timestamp_tn := math.floor(timestamp_t)):
                raise MeowIDInvalid("timestamp's max resolution is seconds, higher is not supported")

            if not 0 <= timestamp_tn <= self.TIMESTAMP_MAX_VALUE:
                raise MeowIDInvalid(f"timestamp is out of range (must be within 0 and {self.TIMESTAMP_MAX_VALUE}")

        self.timestamp = timestamp

        if _checked:
            if not 0 <= sequence_count <= self.SEQUENCE_COUNT_MAX_VALUE:
                raise MeowIDInvalid(f"sequence is out of range (must be within 0 and {self.SEQUENCE_COUNT_MAX_VALUE})")

        self.sequence_count = sequence_count

        if _checked:
            if not 0 <= salt <= self.SALT_MAX_VALUE:
                raise MeowIDInvalid(f"salt is out of range (must be within 0 and {self.SALT_MAX_VALUE}")

        self.salt = salt

        self._initialised = True

    @classmethod
    def from_int(cls, int_: int) -> MeowID:
        return cls(
            datetime.datetime.fromtimestamp((int_ & cls.TIMESTAMP_MASK) >> cls.TIMESTAMP_OFFSET, datetime.UTC),
            (int_ & cls.SEQUENCE_COUNT_MASK) >> cls.SEQUENCE_COUNT_OFFSET,
            (int_ & cls.SALT_MASK) >> cls.SALT_OFFSET
        )

    @classmethod
    def from_str(cls, str_: str) -> MeowID:
        if len(str_) not in (16, 18):
            raise MeowIDInvalid("invalid string meowid format length")

        if len(str_) == 18:
            if str_[8] != '-' or str_[12] != '-':
                raise MeowIDInvalid("invalid long string meowid format")

        try:
            return cls(
                datetime.datetime.fromtimestamp(int((shortened := str_.replace('-', ''))[0:8], 16), datetime.UTC),
                int(shortened[8:11], 16),
                int(shortened[11:16], 16)
            )
        except ValueError as e:
            raise MeowIDInvalid(e) from None

    @classmethod
    def _generate_timestamp(cls) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(math.floor(time.time()), datetime.UTC)

    @classmethod
    def _generate_sequence_count(cls, timestamp: datetime.datetime) -> int:
        if cls._last_timestamp == timestamp:
            cls._sequence_count += 1
        else:
            cls._last_timestamp = timestamp

            cls._sequence_count = 0

        if cls._sequence_count > cls.SEQUENCE_COUNT_MAX_VALUE:
            raise MeowIDExhaustedError("number of possible MeowIDs per second is exhausted")

        return cls._sequence_count

    @classmethod
    def _generate_salt(cls) -> int:
        return random.randint(0, cls.SALT_MAX_VALUE)

    @classmethod
    def generate(cls) -> MeowID:
        return cls(
            (timestamp := cls._generate_timestamp()),
            cls._generate_sequence_count(timestamp),
            cls._generate_salt(),
            _checked=False
        )

    def __setattr__(self, key: str, value: Any) -> None:
        if self._initialised:
            raise TypeError(f"cannot set '{key}' attribute of immutable type '{type(self).__name__}'")
        else:
            super.__setattr__(self, key, value)

    def __hash__(self) -> int:
        return hash(int(self))

    def __int__(self) -> int:
        return (self.timestamp_s << self.TIMESTAMP_OFFSET |
                self.sequence_count << self.SEQUENCE_COUNT_OFFSET |
                self.salt << self.SALT_OFFSET)

    def __repr__(self) -> str:
        return (f"{type(self).__name__}("
                f"timestamp={self.timestamp!r}, "
                f"sequence_count={self.sequence_count!r}, "
                f"salt={self.salt!r}"
                ")")

    def __str__(self) -> str:
        return f"{self.timestamp_s:0>8x}-{self.sequence_count:0>3x}-{self.salt:0>5x}"


def meowid_generator(count: int | None = None) -> Generator[MeowID, None, None]:
    def generate_meowid() -> Generator[MeowID, None, None]:
        yield MeowID.generate()

    if count is None:
        while True:
            yield from generate_meowid()
    else:
        for _ in range(count):
            yield from generate_meowid()
