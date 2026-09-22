from typing import Protocol


class UnitOfWork(Protocol):
    """One business transaction: a command handler commits once when its rules hold."""

    def commit(self) -> None: ...

    def flush(self) -> None: ...
