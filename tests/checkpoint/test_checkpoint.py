import tempfile
from pathlib import Path
from itertools import cycle
from unittest.mock import Mock

import ulm.checkpoint as checkpoint


def test_singular():
    # make clean dir
    codeblock = Mock(side_effect=cycle(["VALUE1", "VALUE2"]))
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
