# pylint: disable=redefined-outer-name

import itertools
import os

import pytest

from dwas._config import Config
from dwas._exceptions import BaseDwasException


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    for key in os.environ:
        monkeypatch.delenv(key)


@pytest.fixture
def kwargs(tmp_path):
    return {
        "cache_path": tmp_path,
        "log_path": None,
        "verbosity": 2,
        "n_jobs": 0,
        "skip_missing_interpreters": False,
        "skip_setup": False,
        "skip_run": False,
        "fail_fast": False,
    }


@pytest.mark.parametrize("enable", (True, False))
def test_can_control_colors_explicitly(enable, kwargs):
    conf = Config(**kwargs, colors=enable)
    assert conf.colors == enable

    # And ensure we have environment variables set correctly
    if enable:
        assert (
            conf.environ.items()
            >= {"PY_COLORS": "1", "FORCE_COLOR": "1"}.items()
        )
    else:
        assert (
            conf.environ.items() >= {"PY_COLORS": "0", "NO_COLOR": "0"}.items()
        )


@pytest.mark.parametrize(
    ("stdout_is_tty", "stderr_is_tty"), itertools.permutations([True, False])
)
def test_enables_colors_if_tty(
    monkeypatch, stdout_is_tty, stderr_is_tty, kwargs
):
    monkeypatch.setattr("sys.stdout.isatty", lambda: stdout_is_tty)
    monkeypatch.setattr("sys.stderr.isatty", lambda: stderr_is_tty)

    conf = Config(**kwargs, colors=None)
    assert conf.colors == (stdout_is_tty and stderr_is_tty)


@pytest.mark.parametrize(
    ("value", "result"),
    (("1", True), ("0", False), ("invalid", BaseDwasException)),
)
def test_can_control_colors_via_py_colors(monkeypatch, kwargs, value, result):
    monkeypatch.setenv("PY_COLORS", value)

    if not isinstance(result, type):
        conf = Config(**kwargs, colors=None)
        assert conf.colors == result
    else:
        with pytest.raises(result):
            conf = Config(**kwargs, colors=None)


def test_can_disable_colors_with_no_color(monkeypatch, kwargs):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)  # pragma: nocover

    conf = Config(**kwargs, colors=None)
    assert not conf.colors


def test_can_enable_colors_with_force_color(monkeypatch, kwargs):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)  # pragma: nocover

    conf = Config(**kwargs, colors=None)
    assert conf.colors


@pytest.mark.parametrize("ci_env_var", ("GITHUB_ACTION",))
def test_enables_colors_on_cis_by_default(ci_env_var, kwargs, monkeypatch):
    monkeypatch.setenv(ci_env_var, "1")

    conf = Config(**kwargs, colors=None)
    assert conf.colors
