from __future__ import annotations

from typing import Any

from meowid import MeowID


class DatabaseInternalError(RuntimeError):
    pass


class ObjectIDUnknownError(DatabaseInternalError):
    def __str__(self):
        return "object does not know its own ID"


class DatabaseValueError(ValueError):
    pass


class OperationPermissionError(DatabaseValueError):
    operation: str
    violation: str | None

    def __init__(self, operation: str, violation: str | None = None) -> None:
        super().__init__()

        self.operation = operation
        self.violation = violation

    def __str__(self) -> str:
        return f"{self.operation} is not allowed {f"due to {self.violation}" if self.violation is not None else ''}"


class ObjectNotFound(DatabaseValueError):
    name: str
    identifier: str
    identifier_type: type
    given_identifier: Any

    def __init__(self, name: str, identifier: str, identifier_type: type, given_identifier: Any) -> None:
        super().__init__()

        self.name = name
        self.identifier = identifier
        self.identifier_type = identifier_type
        self.given_identifier = given_identifier

    def __str__(self) -> str:
        return f"{self.name} was not found by {self.identifier} ({self.identifier_type.__name__}) of {self.given_identifier} ({type(self.given_identifier).__name__})"


class IDNotFoundError(ObjectNotFound):
    def __init__(self, name: str, given_id: MeowID) -> None:
        super().__init__(name, "id", MeowID, given_id)

    def __str__(self) -> str:
        return f"{self.name} with ID {self.given_identifier} ({int(self.given_identifier)}) was not found"


class DatabaseInvalidValue(DatabaseValueError):
    pass


class ValueAlreadyTakenError(DatabaseValueError):
    name: str
    value: Any | None

    def __init__(self, name: str, value: Any | None) -> None:
        super().__init__()

        self.name = name
        self.value = value

    def __str__(self) -> str:
        return f"{self.name} with value {self.value} is already taken"


class WrongValueLengthError(DatabaseInvalidValue):
    name: str
    units_name: str | None
    max_length: int | None
    min_length: int | None
    given_length: int

    def __init__(self, name: str, units_name: str | None, max_length: int | None, min_length: int | None, given_length: int) -> None:
        super().__init__()

        self.name = name
        self.units_name = units_name
        self.max_length = max_length
        self.min_length = min_length
        self.given_length = given_length

    @property
    def _units_name(self) -> str:
        return f" {self.units_name}" if self.units_name is not None else ''

    def __str__(self) -> str:
        return f"{self.name} has invalid length of {self.given_length}{self._units_name} (expected {f"at least {self.min_length}{self._units_name}" if self.min_length is not None else ''}{' and ' if self.max_length is not None and self.min_length is not None else ''}{f"at most {self.max_length}{self._units_name}" if self.max_length is not None else ''})"


class WrongHashLengthError(WrongValueLengthError):
    name: str
    expected: int
    given: int

    def __init__(self, name: str, expected: int, given: int) -> None:
        super().__init__(name, "characters", expected, expected, given)

        self.name = name
        self.expected = expected
        self.given = given

    def __str__(self) -> str:
        return f"hash of {self.name} must be {self.expected} (not {self.given}) characters long"


class ValueMismatchError[T](DatabaseInvalidValue):
    name: str
    expected: T | None
    given: T | None

    def __init__(self, name: str, expected: T | None, given: T | None) -> None:
        super().__init__()

        self.name = name
        self.expected = expected
        self.given = given

    def __str__(self) -> str:
        return f"{self.name} was expected to be {self.expected if self.expected is not None else "a different value"}{f", but is {self.given}" if self.given is not None else ''}"
