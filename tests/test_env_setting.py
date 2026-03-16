# pylint: disable=redefined-outer-name

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests._utils import cli, using_project

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def cache_path(tmp_path_factory):
    return tmp_path_factory.mktemp("cache")


@using_project("examples/set_env")
def test_can_inject_environment_in_dependent_steps(cache_path: Path) -> None:
    result = cli(cache_path=cache_path, steps=["step2"])
    assert result.stdout == "foobar\n"
