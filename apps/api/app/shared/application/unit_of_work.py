from typing import Protocol


class UnitOfWork(Protocol):
    """One business transaction: a command handler commits once when its rules hold."""

    def commit(self) -> None: ...

    def flush(self) -> None: ...

    def rollback(self) -> None:
        """Drop what the transaction did so far (a long-running command records its failure afterwards)."""
        ...
