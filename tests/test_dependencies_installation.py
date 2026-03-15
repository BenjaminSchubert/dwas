# pylint: disable=redefined-outer-name

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from tests._utils import cli, using_project

if TYPE_CHECKING:
    from pathlib import Path


class GreaterThan:
    def __init__(self, version: str) -> None:
        self._expected_version = version

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented

        expected_parts = self._expected_version.split(".")
        other_parts = other.split(".")

        len_diff = len(expected_parts) - len(other_parts)
        if len_diff < 0:
            expected_parts += ["0"] * -len_diff
        elif len_diff > 0:
            other_parts += ["0"] * len_diff

        for e, o in zip(expected_parts, other_parts):
            ei = int(e)
            oi = int(o)

            if ei > oi:
                return False
            if ei < oi:
                return True

        return False

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self._expected_version))

    def __repr__(self) -> str:
        return f"GreaterThan<{self._expected_version}>"


@pytest.fixture(scope="module")
def cache_path(tmp_path_factory):
    return tmp_path_factory.mktemp("cache")


@pytest.mark.parametrize(
    ("dependencies_name", "expected_packages"),
    (
        ("pyproject", {"colorama": "0.4.0"}),
        ("dev-group", {"pip": "25.0"}),
        ("other-group", {"setuptools": "70.0.0"}),
        ("all", {"colorama": "0.4.0", "pip": "25.0", "setuptools": "70.0.0"}),
    ),
    ids=["pyproject", "dev-group", "other-group", "all"],
)
@pytest.mark.parametrize(
    "package", (True, False), ids=["package", "no-package"]
)
@using_project("examples/dependencies")
def test_only_selected_dependencies_are_installed(
    cache_path: Path,
    tmp_path: Path,
    dependencies_name: str,
    package: bool,  # noqa: FBT001
    expected_packages: dict[str, str],
) -> None:
    step_name = f"dependencies[{'no-' if not package else ''}package,{dependencies_name}]"
    original_lock = tmp_path.joinpath("uv.lock").read_text()

    result = cli(cache_path=cache_path, steps=[step_name])
    dependencies = json.loads(result.stdout.strip().splitlines()[-1])
    final_lock = tmp_path.joinpath("uv.lock").read_text()

    expected_installs = [
        {"name": pkg, "version": GreaterThan(version)}
        for pkg, version in expected_packages.items()
    ]
    if package:
        if expected_installs[0]["name"] != "colorama":
            expected_installs = [
                {"name": "colorama", "version": GreaterThan("0.4.0")},
                *expected_installs,
            ]
        expected_installs.append(
            {"name": "test-dependencies", "version": "0.0.1"}
        )

    assert dependencies == expected_installs
    assert final_lock == original_lock
