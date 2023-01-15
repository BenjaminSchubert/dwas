# pylint and pytest fixtures dependency injection are not friends
# pylint: disable=redefined-outer-name
import copy
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Union

import pytest
from _pytest.capture import FDCapture, MultiCapture

from dwas import Config, predefined
from dwas.__main__ import main
from dwas._pipeline import Pipeline, set_pipeline
from dwas._subproc import set_subprocess_default_pipes

from ._utils import isolated_context, isolated_logging

pytest.register_assert_rewrite("tests.predefined.mixins")


@dataclass(frozen=True)
class Result:
    exc: Optional[SystemExit]
    stdout: str
    stderr: str


@pytest.fixture
def cli(tmp_path_factory):
    cache_path = tmp_path_factory.mktemp("cache")

    @isolated_context
    @isolated_logging
    def _cli(args: List[str], expected_status: int = 0) -> Result:
        capture = MultiCapture(out=FDCapture(1), err=FDCapture(2), in_=None)
        capture.start_capturing()
        set_subprocess_default_pipes(sys.stdout, sys.stderr)

        exception = None
        # See https://github.com/python/typeshed/issues/8513#issue-1333671093
        exit_code: Union[str, int, None] = 0

        args.extend(["--verbose", f"--cache-path={cache_path}"])
        if "--no-colors" not in args and "--colors" not in args:
            args.append("--color")

        try:
            main(args)
        except SystemExit as exc:
            if exc.code != 0:
                exit_code = exc.code
                exception = exc
        finally:
            out, err = capture.readouterr()
            capture.stop_capturing()
            set_subprocess_default_pipes(sys.stdout, sys.stderr)
            print(out)
            print(err, file=sys.stderr)

        assert exit_code == expected_status

        return Result(exc=exception, stdout=out, stderr=err)

    return _cli


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


@pytest.fixture(autouse=True, scope="session")
def ensure_defaults_are_untouched(tmp_path_factory):
    """
    Ensure that the defaults values for predefined steps are not mutated.

    The predefined steps set some defaults that might be mutable, e.g. lists.
    We need to take special care to ensure we do not modify them at runtime so
    that the steps are reusable.

    This loads all the steps before anything runs, and deep copies the defaults.
    It then validates that they did not change at the end of the run.
    """
    steps = {}

    @isolated_context
    def load_steps():
        # Load all the steps programatically, and get their defaults.
        # We could probably do it a bit simpler, without a pipeline, but this
        # works without us having to do more special magic.
        pipeline = Pipeline(
            Config(
                cache_path=tmp_path_factory.mktemp("defaults-validation"),
                verbosity=2,
                colors=False,
                n_jobs=1,
                skip_missing_interpreters=False,
                skip_setup=False,
                skip_run=False,
                fail_fast=False,
            )
        )
        set_pipeline(pipeline)

        for step_factory_name in predefined.__all__:
            steps[step_factory_name] = getattr(predefined, step_factory_name)()

    def extract_defaults():
        return {name: step.__dwas_defaults__ for name, step in steps.items()}

    load_steps()
    # Deep copy the defaults
    original_values = copy.deepcopy(extract_defaults())
    yield

    # And validate
    assert (
        extract_defaults() == original_values
    ), "BUG: Defaults arguments were mutated during the tests."


@pytest.fixture
def project(request, tmp_path, monkeypatch):
    markers = list(request.node.iter_markers("project"))
    assert (
        len(markers) == 1
    ), f"Didn't get the expected number of markers for 'project': {markers}"

    project = markers[0].args[0]

    for path in project.iterdir():
        if path.is_dir():
            copy_func: Callable[[Path, Path], None] = shutil.copytree
        else:
            copy_func = shutil.copy

        copy_func(path, tmp_path / path.name)

    monkeypatch.chdir(tmp_path)
