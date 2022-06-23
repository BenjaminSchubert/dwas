import sys
from dataclasses import dataclass
from typing import List, Optional

import pytest
from _pytest.capture import FDCapture, MultiCapture

from dwas.__main__ import main

from ._utils import isolated_context


@dataclass(frozen=True)
class Result:
    exit_code: int
    exc: Optional[SystemExit]
    stdout: str
    stderr: str


@pytest.fixture
def cli():
    @isolated_context
    def _cli(args: List[str], raise_on_error: bool = True) -> Result:
        capture = MultiCapture(out=FDCapture(1), err=FDCapture(2), in_=None)
        capture.start_capturing()

        exception = None
        exit_code = 0

        try:
            main(args)
        except SystemExit as exc:
            if exc.code != 0:
                exit_code = exc.code
                exception = exc

        out, err = capture.readouterr()
        capture.stop_capturing()

        result = Result(
            exit_code=exit_code, exc=exception, stdout=out, stderr=err
        )

        print(out)
        print(err, file=sys.stderr)

        if raise_on_error and exception is not None:
            raise Exception(result)

        return result

    return _cli
