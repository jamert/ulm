import contextlib
import pickle
from pathlib import Path


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
def singular(filename: Path) -> any:
    yield Singular(filename)
