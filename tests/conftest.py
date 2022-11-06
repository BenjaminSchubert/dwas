# pylint and pytest fixtures dependency injection are not friends
# pylint: disable=redefined-outer-name
import logging
import sys
from dataclasses import dataclass
from typing import List, Optional

import pytest
from _pytest.capture import FDCapture, MultiCapture

from dwas import Config
from dwas.__main__ import main
from dwas._pipeline import Pipeline

from ._utils import isolated_context, isolated_logging


@dataclass(frozen=True)
class Result:
    exit_code: int
    exc: Optional[SystemExit]
    stdout: str
    stderr: str


@pytest.fixture
def cli():
    root_logger = logging.getLogger()
    handlers = root_logger.handlers
    root_logger.handlers = []

    @isolated_context
    @isolated_logging
    def _cli(args: List[str], raise_on_error: bool = True) -> Result:
        capture = MultiCapture(out=FDCapture(1), err=FDCapture(2), in_=None)
        capture.start_capturing()

        exception = None
        exit_code = 0

        try:
            main(args + ["--verbose", "--color"])
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

    yield _cli

    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    root_logger.handlers = handlers


@pytest.fixture
def tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def sample_config(tmp_path):
    return Config(
        cache_path=tmp_path / "cache",
        verbosity=2,
        colors=False,
        n_jobs=1,
        skip_missing_interpreters=False,
        skip_setup=False,
        skip_run=False,
        fail_fast=False,
    )


@pytest.fixture
def pipeline(sample_config):
    return Pipeline(sample_config)
