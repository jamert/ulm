import contextlib
import pickle
from pathlib import Path
from typing import Iterable, Optional


class Singular:
    def __init__(self, filename: Path) -> None:
        self.filename = filename

    def saved(self) -> any:
        if self.filename.exists():
            with self.filename.open("rb") as fd:
                return pickle.load(fd)

    def save(self, value: any) -> any:  # TODO: generic type
        with self.filename.open("wb") as fd:
            pickle.dump(value, fd)

        return value


@contextlib.contextmanager
def singular(filename: Path):
    yield Singular(filename)


class indexed:
    def __init__(
        self,
        filename: Path,
        iterable: Iterable,
        once_in: Optional[int] = None,
        initializer: Optional[any] = None,
    ) -> None:
        self.filename = filename
        self.iterable = iterable.__iter__()
        self._context = initializer

        self._restore()

    def _restore(self) -> None:
        self._index = 0
        if self.filename.exists():
            with self.filename.open("rb") as fd:
                self._index, self._context = pickle.load(fd)

            for _ in range(self._index + 1):
                next(self.iterable)

    def __iter__(self) -> "indexed":
        return self

    def __next__(self) -> tuple[int, any, any]:
        i = self._index
        self._index += 1
        return i, next(self.iterable), self._context

    def save(self, index: int, context: any) -> any:  # TODO: generic type
        with self.filename.open("wb") as fd:
            pickle.dump((index, context), fd)
        self._context = context

        return context

    def saved(self) -> any:
        return self._context

    def finish(self) -> None:
        """
        Replacement for the `break` statement
        """
        raise NotImplementedError()
