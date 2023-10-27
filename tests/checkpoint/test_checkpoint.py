import tempfile
from pathlib import Path
from itertools import cycle
from unittest.mock import Mock, call

import ulm.checkpoint as checkpoint


def test_singular():
    codeblock = Mock(side_effect=cycle(["VALUE1", "VALUE2"]))
    # make clean dir
    with tempfile.TemporaryDirectory() as tempdir:
        filename = Path(tempdir).joinpath("singular.cp")

        # first run executes code
        with checkpoint.singular(filename) as cp:
            if not (first := cp.saved()):
                first = cp.save(codeblock())

        codeblock.assert_called_once()

        # second run passes without executing
        with checkpoint.singular(filename) as cp:
            if not (second := cp.saved()):
                second = cp.save(codeblock())

        codeblock.assert_called_once()

        # assert blocks have the same values
        assert first == second


def test_indexed():
    items = range(5)
    codeblock = Mock(wraps=lambda value: value)
    with tempfile.TemporaryDirectory() as tempdir:
        filename = Path(tempdir).joinpath("indexed.cp")

        # clean run
        cp = checkpoint.indexed(filename, iterable=items, once_in=3, initializer=[])
        for index, item, context in cp:
            context.append(codeblock(item))
            cp.save(index, context)
        else:
            first = cp.saved()

        codeblock.assert_has_calls([call(i) for i in range(5)])
        assert first == list(range(5))

        codeblock.reset_mock()
        # run from finished
        cp = checkpoint.indexed(filename, iterable=items, once_in=3, initializer=[])
        for index, item, context in cp:
            context.append(codeblock(item))
            cp.save(index, context)
        else:
            second = cp.saved()

        codeblock.assert_not_called()
        assert first == second


def test_indexed_restores_from_the_middle():
    items = list(range(5))
    codeblock = Mock(wraps=lambda value: value)
    with tempfile.TemporaryDirectory() as tempdir:
        filename = Path(tempdir).joinpath("indexed.cp")

        # clean run
        cp = checkpoint.indexed(filename, iterable=items, once_in=3, initializer=[])
        for index, item, context in cp:
            context.append(codeblock(item))
            cp.save(index, context)
            assert items[index] == item

            if index == 3:
                break

        first = context

        codeblock.assert_has_calls([call(i) for i in range(4)])
        assert first == list(range(4))

        codeblock.reset_mock()
        # run from finished
        cp = checkpoint.indexed(filename, iterable=items, once_in=3, initializer=[])
        for index, item, context in cp:
            context.append(codeblock(item))
            cp.save(index, context)
            assert items[index] == item
        else:
            second = cp.saved()

        codeblock.assert_has_calls([call(i) for i in range(3, 5)])
        assert set(first) < set(second)  # is subset
        assert set(second) - set(first) == {4}
