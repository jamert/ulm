import contextlib
import pickle
from pathlib import Path
from typing import Any, Generator, Iterable, Optional


class Singular:
    def __init__(self, filename: Path) -> None:
        self.filename = filename

    def saved(self) -> Any:
        if self.filename.exists():
            with self.filename.open("rb") as fd:
                return pickle.load(fd)
        else:
            return None

    def save(self, value: Any) -> Any:  # TODO: generic type
        with self.filename.open("wb") as fd:
            pickle.dump(value, fd)

        return value


@contextlib.contextmanager
def singular(filename: Path) -> Generator[Singular, None, None]:
    yield Singular(filename)


class indexed:
    def __init__(
        self,
        filename: Path,
        iterable: Iterable,
        once_in: Optional[int] = None,
        initializer: Optional[Any] = None,
    ) -> None:
        self.filename = filename
        self.iterable = iterable.__iter__()
        self.once_in = once_in
        self._context = initializer

        self._restore()

    def _restore(self) -> None:
        self._index = -1
        if self.filename.exists():
            with self.filename.open("rb") as fd:
                self._index, self._context = pickle.load(fd)

            for _ in range(self._index):
                next(self.iterable)

    def __iter__(self) -> "indexed":
        return self

    def __next__(self) -> tuple[int, Any, Any]:
        self._index += 1
        return self._index, next(self.iterable), self._context

    def save(self, index: int, context: Any) -> Any:  # TODO: generic type
        if self.once_in is None or (index + 1) % self.once_in == 0:
            with self.filename.open("wb") as fd:
                pickle.dump((index, context), fd)

        self._context = context

        return context

    def saved(self) -> Any:
        """
        Marks finish of iteration
        """
        with self.filename.open("wb") as fd:
            pickle.dump((self._index, self._context), fd)
        return self._context

    def finish(self) -> None:
        """
        Replacement for the `break` statement
        """
        raise NotImplementedError()
